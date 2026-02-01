import os
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc, extract

from config import Config
from database import db, Project, Material, PrintProfile, Quote, VoiceNote, Settings
from whisper_service import get_whisper_service
from pdf_generator import generate_quote_pdf

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize database
db.init_app(app)

# Initialize Whisper service
whisper = get_whisper_service()


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, folder, allowed_extensions):
    """Save uploaded file with unique filename"""
    if file and allowed_file(file.filename, allowed_extensions):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = folder / filename
        file.save(str(filepath))
        return filename
    return None


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    # Get active projects
    active_projects = Project.query.filter(
        Project.status.in_(['quote', 'designing', 'printing'])
    ).order_by(desc(Project.created_at)).limit(10).all()

    # Get low stock materials
    all_materials = Material.query.all()
    low_stock_materials = [m for m in all_materials if m.stock_percentage() < 30]

    # Get current month earnings
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_earnings = db.session.query(func.sum(Project.final_price)).filter(
        Project.status == 'completed',
        Project.completed_at >= month_start
    ).scalar() or 0

    # Projects this month
    projects_this_month = Project.query.filter(
        Project.created_at >= month_start
    ).count()

    # Statistics for charts
    # Projects by status
    status_counts = db.session.query(
        Project.status,
        func.count(Project.id)
    ).group_by(Project.status).all()

    # Most used materials
    material_usage = db.session.query(
        Material.name,
        func.count(Project.id)
    ).join(Project, Project.material_id == Material.id).group_by(Material.name).limit(5).all()

    return render_template('dashboard.html',
                         active_projects=active_projects,
                         low_stock_materials=low_stock_materials,
                         monthly_earnings=monthly_earnings,
                         projects_this_month=projects_this_month,
                         status_counts=dict(status_counts),
                         material_usage=dict(material_usage))


@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    """Create new project"""
    if request.method == 'GET':
        materials = Material.query.order_by(Material.name).all()
        return render_template('new_project.html', materials=materials)

    # POST - Create project
    try:
        # Get form data
        title = request.form.get('title')
        customer_name = request.form.get('customer_name')
        printer_type = request.form.get('printer_type')
        material_id = request.form.get('material_id')
        quantity = int(request.form.get('quantity', 1))
        estimated_time_hours = float(request.form.get('estimated_time_hours', 0))
        transcription = request.form.get('transcription', '')

        # Calculate costs
        hourly_rate = float(Settings.get('hourly_labor_rate', Config.HOURLY_LABOR_RATE))
        margin_pct = float(Settings.get('default_margin_percentage', Config.DEFAULT_MARGIN_PERCENTAGE))

        labor_cost = estimated_time_hours * hourly_rate
        material_cost = 0.0

        if material_id:
            material = Material.query.get(int(material_id))
            if material:
                if material.cost_per_kg:
                    # Estimate material cost (simplified)
                    material_cost = material.cost_per_kg * 0.05 * quantity  # ~50g per piece
                elif material.cost_per_sheet:
                    material_cost = material.cost_per_sheet * quantity

        subtotal = labor_cost + material_cost
        final_price = subtotal * (1 + margin_pct / 100)

        # Create project
        project = Project(
            title=title,
            customer_name=customer_name,
            printer_type=printer_type,
            material_id=int(material_id) if material_id else None,
            quantity=quantity,
            estimated_time_hours=estimated_time_hours,
            voice_transcription=transcription,
            material_cost=material_cost,
            labor_cost=labor_cost,
            final_price=final_price,
            margin_percentage=margin_pct,
            status='quote'
        )

        # Handle photos
        photos = []
        for i in range(5):  # Support up to 5 photos
            key = f'photo_{i}'
            if key in request.files:
                photo_file = request.files[key]
                filename = save_uploaded_file(photo_file, Config.PHOTOS_FOLDER, Config.ALLOWED_IMAGE_EXTENSIONS)
                if filename:
                    photos.append(f"/static/uploads/photos/{filename}")

        if photos:
            project.set_photos(photos)

        # Handle ALL project files (PDFs, CAD, documents, etc.)
        project_files_list = []
        if 'project_files' in request.files:
            files = request.files.getlist('project_files')
            for file in files:
                if file and file.filename:
                    filename = save_uploaded_file(file, Config.FILES_FOLDER, Config.ALL_ALLOWED_EXTENSIONS)
                    if filename:
                        # Get file size from saved file
                        file_path = Config.FILES_FOLDER / filename
                        file_size = file_path.stat().st_size if file_path.exists() else 0
                        project_files_list.append({
                            'path': f"/static/uploads/files/{filename}",
                            'filename': file.filename,
                            'size': file_size
                        })

        if project_files_list:
            project.set_files(project_files_list)

        db.session.add(project)
        db.session.commit()

        flash('Progetto creato con successo!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Errore nella creazione del progetto: {str(e)}', 'danger')
        return redirect(url_for('new_project'))


@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    """Project detail page"""
    project = Project.query.get_or_404(project_id)
    voice_notes = VoiceNote.query.filter_by(project_id=project_id).order_by(desc(VoiceNote.created_at)).all()
    return render_template('project_detail.html', project=project, voice_notes=voice_notes)


@app.route('/projects/<int:project_id>/update', methods=['POST'])
def update_project(project_id):
    """Update project"""
    project = Project.query.get_or_404(project_id)

    try:
        # Update fields
        if 'status' in request.form:
            project.status = request.form['status']
            if project.status == 'completed' and not project.completed_at:
                project.completed_at = datetime.utcnow()

                # Update material stock
                if project.material_id:
                    material = Material.query.get(project.material_id)
                    if material and material.cost_per_kg:
                        # Deduct material (estimate 50g per piece)
                        used_kg = 0.05 * project.quantity
                        material.current_stock_kg = max(0, material.current_stock_kg - used_kg)
                        material.last_used = datetime.utcnow()

        if 'actual_time_hours' in request.form and request.form['actual_time_hours']:
            project.actual_time_hours = float(request.form['actual_time_hours'])

        if 'result_rating' in request.form and request.form['result_rating']:
            project.result_rating = int(request.form['result_rating'])

        if 'settings_notes' in request.form:
            project.settings_notes = request.form['settings_notes']

        db.session.commit()
        flash('Progetto aggiornato con successo!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Errore nell\'aggiornamento: {str(e)}', 'danger')

    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """Delete project"""
    project = Project.query.get_or_404(project_id)

    try:
        # Delete associated voice notes (will cascade automatically due to relationship)
        db.session.delete(project)
        db.session.commit()
        flash('Progetto eliminato con successo!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Errore nell\'eliminazione: {str(e)}', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/voice-note', methods=['POST'])
def add_voice_note(project_id):
    """Add voice note to project"""
    project = Project.query.get_or_404(project_id)

    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400

        audio_file = request.files['audio']
        filename = save_uploaded_file(audio_file, Config.AUDIO_FOLDER, Config.ALLOWED_AUDIO_EXTENSIONS)

        if not filename:
            return jsonify({'error': 'Invalid file format'}), 400

        audio_path = f"/static/uploads/audio/{filename}"
        full_path = Config.AUDIO_FOLDER / filename

        # Transcribe
        transcription = whisper.transcribe_audio(str(full_path))

        # Create voice note
        voice_note = VoiceNote(
            project_id=project_id,
            audio_path=audio_path,
            transcription=transcription,
            note_type=request.form.get('note_type', 'general')
        )

        db.session.add(voice_note)
        db.session.commit()

        return jsonify({
            'success': True,
            'voice_note': voice_note.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/materials')
def materials():
    """Materials management page"""
    materials_list = Material.query.order_by(Material.name).all()
    return render_template('materials.html', materials=materials_list)


@app.route('/materials/new', methods=['POST'])
def new_material():
    """Create new material"""
    try:
        material = Material(
            name=request.form['name'],
            type=request.form['type'],
            printer_compatible=request.form.get('printer_compatible', ''),
            color=request.form.get('color', ''),
            cost_per_kg=float(request.form['cost_per_kg']) if request.form.get('cost_per_kg') else None,
            cost_per_sheet=float(request.form['cost_per_sheet']) if request.form.get('cost_per_sheet') else None,
            current_stock_kg=float(request.form.get('current_stock_kg', 1.0)),
            initial_stock_kg=float(request.form.get('current_stock_kg', 1.0)),
            optimal_temp=int(request.form['optimal_temp']) if request.form.get('optimal_temp') else None,
            optimal_speed=int(request.form['optimal_speed']) if request.form.get('optimal_speed') else None,
            qr_code=f"MAT-{uuid.uuid4().hex[:8].upper()}"
        )

        db.session.add(material)
        db.session.commit()

        flash('Materiale aggiunto con successo!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Errore nell\'aggiunta del materiale: {str(e)}', 'danger')

    return redirect(url_for('materials'))


@app.route('/materials/<int:material_id>/update', methods=['POST'])
def update_material(material_id):
    """Update material stock"""
    material = Material.query.get_or_404(material_id)

    try:
        if 'current_stock_kg' in request.form:
            material.current_stock_kg = float(request.form['current_stock_kg'])

        if 'voice_notes' in request.form:
            material.voice_notes = request.form['voice_notes']

        db.session.commit()
        flash('Materiale aggiornato!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Errore: {str(e)}', 'danger')

    return redirect(url_for('materials'))


@app.route('/materials/<int:material_id>/delete', methods=['POST'])
def delete_material(material_id):
    """Delete material"""
    material = Material.query.get_or_404(material_id)

    try:
        # Check if material is used in any projects
        projects_using = Project.query.filter_by(material_id=material_id).count()
        if projects_using > 0:
            flash(f'Impossibile eliminare: {projects_using} progetti usano questo materiale!', 'danger')
            return redirect(url_for('materials'))

        db.session.delete(material)
        db.session.commit()
        flash('Materiale eliminato con successo!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Errore nell\'eliminazione: {str(e)}', 'danger')

    return redirect(url_for('materials'))


@app.route('/quick-quote', methods=['GET', 'POST'])
def quick_quote():
    """Quick quote generator"""
    if request.method == 'GET':
        # Get recent quotes
        recent_quotes = Quote.query.order_by(desc(Quote.created_at)).limit(10).all()
        return render_template('quick_quote.html', recent_quotes=recent_quotes)

    # POST - Generate quote
    try:
        customer_name = request.form['customer_name']
        description = request.form['description']
        estimated_price = float(request.form['estimated_price'])
        voice_request = request.form.get('voice_request', '')

        quote = Quote(
            customer_name=customer_name,
            description=description,
            estimated_price=estimated_price,
            voice_request=voice_request,
            status='pending'
        )

        db.session.add(quote)
        db.session.commit()

        # Generate PDF
        pdf_filename = f"quote_{quote.id}_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = Config.UPLOAD_FOLDER / 'quotes' / pdf_filename
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        generate_quote_pdf(quote, str(pdf_path))
        quote.pdf_path = f"/static/uploads/quotes/{pdf_filename}"
        db.session.commit()

        flash('Preventivo creato con successo!', 'success')
        return redirect(url_for('quick_quote'))

    except Exception as e:
        db.session.rollback()
        flash(f'Errore: {str(e)}', 'danger')
        return redirect(url_for('quick_quote'))


@app.route('/history')
def history():
    """Project history and search"""
    # Get filters
    status_filter = request.args.get('status')
    customer_filter = request.args.get('customer')
    printer_filter = request.args.get('printer_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Build query
    query = Project.query

    if status_filter:
        query = query.filter(Project.status == status_filter)

    if customer_filter:
        query = query.filter(Project.customer_name.ilike(f'%{customer_filter}%'))

    if printer_filter:
        query = query.filter(Project.printer_type == printer_filter)

    if date_from:
        query = query.filter(Project.created_at >= datetime.fromisoformat(date_from))

    if date_to:
        query = query.filter(Project.created_at <= datetime.fromisoformat(date_to))

    projects = query.order_by(desc(Project.created_at)).all()

    # Calculate statistics
    total_earnings = sum(p.final_price for p in projects if p.status == 'completed')
    total_projects = len(projects)

    return render_template('history.html',
                         projects=projects,
                         total_earnings=total_earnings,
                         total_projects=total_projects)


@app.route('/search')
def search():
    """Global search"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    printer_filter = request.args.get('printer', '')

    results = []

    if query:
        # Search projects
        if not search_type or search_type == 'projects':
            projects = Project.query.filter(
                db.or_(
                    Project.title.ilike(f'%{query}%'),
                    Project.customer_name.ilike(f'%{query}%'),
                    Project.voice_transcription.ilike(f'%{query}%')
                )
            )

            if status_filter:
                projects = projects.filter(Project.status == status_filter)
            if printer_filter:
                projects = projects.filter(Project.printer_type == printer_filter)

            for project in projects.all():
                results.append({
                    'type': 'project',
                    'id': project.id,
                    'title': project.title,
                    'customer_name': project.customer_name,
                    'printer_type': project.printer_type,
                    'status': project.status,
                    'final_price': project.final_price,
                    'voice_transcription': project.voice_transcription,
                    'created_at': project.created_at
                })

        # Search materials
        if not search_type or search_type == 'materials':
            materials = Material.query.filter(
                db.or_(
                    Material.name.ilike(f'%{query}%'),
                    Material.color.ilike(f'%{query}%'),
                    Material.voice_notes.ilike(f'%{query}%')
                )
            ).all()

            for material in materials:
                results.append({
                    'type': 'material',
                    'name': material.name,
                    'type': material.type,
                    'color': material.color,
                    'current_stock_kg': material.current_stock_kg,
                    'stock_percentage': material.stock_percentage
                })

        # Search quotes
        if not search_type or search_type == 'quotes':
            quotes = Quote.query.filter(
                db.or_(
                    Quote.customer_name.ilike(f'%{query}%'),
                    Quote.description.ilike(f'%{query}%'),
                    Quote.voice_request.ilike(f'%{query}%')
                )
            ).all()

            for quote in quotes:
                results.append({
                    'type': 'quote',
                    'id': quote.id,
                    'customer_name': quote.customer_name,
                    'description': quote.description,
                    'estimated_price': quote.estimated_price,
                    'status': quote.status,
                    'created_at': quote.created_at
                })

    return render_template('search.html', query=query, results=results)


@app.route('/quote/<int:quote_id>')
def quote_detail(quote_id):
    """View quote details and download PDF"""
    quote = Quote.query.get_or_404(quote_id)

    # If PDF doesn't exist, generate it now
    if not quote.pdf_path or not os.path.exists(quote.pdf_path.replace('/static/uploads/', str(Config.UPLOAD_FOLDER) + '/')):
        pdf_filename = f"quote_{quote.id}_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = Config.UPLOAD_FOLDER / 'quotes' / pdf_filename
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        generate_quote_pdf(quote, str(pdf_path))
        quote.pdf_path = f"/static/uploads/quotes/{pdf_filename}"
        db.session.commit()

    return send_file(
        quote.pdf_path.replace('/static/uploads/', str(Config.UPLOAD_FOLDER) + '/'),
        as_attachment=True,
        download_name=f"Preventivo_{quote.customer_name.replace(' ', '_')}_{quote.id}.pdf"
    )


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Application settings"""
    if request.method == 'GET':
        # Get current settings
        hourly_rate = Settings.get('hourly_labor_rate', Config.HOURLY_LABOR_RATE)
        margin = Settings.get('default_margin_percentage', Config.DEFAULT_MARGIN_PERCENTAGE)
        dark_mode = Settings.get('dark_mode', 'true')

        return render_template('settings.html',
                             hourly_rate=hourly_rate,
                             margin=margin,
                             dark_mode=dark_mode)

    # POST - Update settings
    try:
        Settings.set('hourly_labor_rate', request.form['hourly_labor_rate'])
        Settings.set('default_margin_percentage', request.form['default_margin_percentage'])
        Settings.set('dark_mode', request.form.get('dark_mode', 'false'))

        flash('Impostazioni salvate!', 'success')

    except Exception as e:
        flash(f'Errore: {str(e)}', 'danger')

    return redirect(url_for('settings'))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    """API endpoint for transcribing audio"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400

        audio_file = request.files['audio']
        filename = save_uploaded_file(audio_file, Config.AUDIO_FOLDER, Config.ALLOWED_AUDIO_EXTENSIONS)

        if not filename:
            return jsonify({'error': 'Invalid file format'}), 400

        audio_path = Config.AUDIO_FOLDER / filename
        transcription = whisper.transcribe_audio(str(audio_path))

        # Parse information based on context
        context = request.form.get('context', 'project')

        if context == 'project':
            info = whisper.parse_project_info(transcription)
        elif context == 'material':
            info = whisper.parse_material_info(transcription)
        elif context == 'quote':
            info = whisper.parse_quote_info(transcription)
        else:
            info = {}

        return jsonify({
            'success': True,
            'transcription': transcription,
            'parsed_info': info,
            'audio_path': f"/static/uploads/audio/{filename}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/materials/compatible/<printer_type>')
def api_compatible_materials(printer_type):
    """Get materials compatible with printer type"""
    materials = Material.query.all()
    compatible = [m.to_dict() for m in materials if m.is_compatible_with(printer_type)]
    return jsonify(compatible)


@app.route('/api/stats/monthly')
def api_monthly_stats():
    """Get monthly statistics for charts"""
    # Last 6 months
    stats = []
    for i in range(6):
        month_date = datetime.utcnow() - timedelta(days=30 * i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if i > 0:
            month_end = (datetime.utcnow() - timedelta(days=30 * (i - 1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month_end = datetime.utcnow()

        earnings = db.session.query(func.sum(Project.final_price)).filter(
            Project.status == 'completed',
            Project.completed_at >= month_start,
            Project.completed_at < month_end
        ).scalar() or 0

        projects_count = Project.query.filter(
            Project.created_at >= month_start,
            Project.created_at < month_end
        ).count()

        stats.append({
            'month': month_start.strftime('%B %Y'),
            'earnings': float(earnings),
            'projects': projects_count
        })

    return jsonify(stats[::-1])  # Reverse to show oldest first


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """Initialize database with sample data"""
    with app.app_context():
        # Create tables
        db.create_all()

        # Check if already initialized
        if Material.query.first():
            return

        print("Initializing database with sample data...")

        # Add default settings
        Settings.set('hourly_labor_rate', '15.0')
        Settings.set('default_margin_percentage', '30.0')
        Settings.set('dark_mode', 'true')

        # Add sample materials
        materials = [
            Material(
                name="PLA Bianco Sunlu",
                type="pla",
                printer_compatible="3d_bambu,3d_flashforge",
                color="Bianco",
                cost_per_kg=18.50,
                current_stock_kg=0.75,
                initial_stock_kg=1.0,
                optimal_temp=210,
                optimal_speed=60,
                qr_code="MAT-PLA001",
                voice_notes="Ottima adesione, finitura liscia. Perfetto per prototipi."
            ),
            Material(
                name="PETG Trasparente",
                type="petg",
                printer_compatible="3d_bambu,3d_flashforge",
                color="Trasparente",
                cost_per_kg=22.00,
                current_stock_kg=0.45,
                initial_stock_kg=1.0,
                optimal_temp=235,
                optimal_speed=50,
                qr_code="MAT-PETG001",
                voice_notes="Richiede bed a 80 gradi. Ottima resistenza."
            ),
            Material(
                name="Acrilico Trasparente 3mm",
                type="acrylic_laser",
                printer_compatible="laser_xtool",
                color="Trasparente",
                cost_per_sheet=8.50,
                current_stock_kg=5.0,
                initial_stock_kg=10.0,
                qr_code="MAT-ACR001",
                voice_notes="Taglia bene a 80% potenza, 15mm/s. Ottima incisione."
            ),
            Material(
                name="Compensato 5mm",
                type="wood_laser",
                printer_compatible="laser_xtool",
                color="Naturale",
                cost_per_sheet=4.00,
                current_stock_kg=3.0,
                initial_stock_kg=15.0,
                qr_code="MAT-WOOD001",
                voice_notes="Perfetto per incisioni profonde. Attenzione alla resina."
            )
        ]

        for material in materials:
            db.session.add(material)

        db.session.commit()

        # Add sample projects
        projects = [
            Project(
                title="Portachiavi personalizzati Sunset Bar",
                customer_name="Marco Rossi",
                printer_type="3d_bambu",
                material_id=1,
                status="completed",
                quantity=10,
                estimated_time_hours=3.0,
                actual_time_hours=2.8,
                material_cost=9.25,
                labor_cost=45.00,
                final_price=70.53,
                margin_percentage=30.0,
                result_rating=5,
                voice_transcription="Devo fare 10 portachiavi per il cliente Marco del Sunset Bar",
                created_at=datetime.utcnow() - timedelta(days=15),
                completed_at=datetime.utcnow() - timedelta(days=13)
            ),
            Project(
                title="Targhe acriliche personalizzate",
                customer_name="Laura Bianchi",
                printer_type="laser_xtool",
                material_id=3,
                status="printing",
                quantity=5,
                estimated_time_hours=2.0,
                material_cost=42.50,
                labor_cost=30.00,
                final_price=94.25,
                margin_percentage=30.0,
                voice_transcription="5 targhe personalizzate in acrilico trasparente per Laura",
                created_at=datetime.utcnow() - timedelta(days=2)
            )
        ]

        for project in projects:
            db.session.add(project)

        db.session.commit()

        print("Database initialized successfully!")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    init_database()
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=(Config.FLASK_ENV == 'development')
    )
