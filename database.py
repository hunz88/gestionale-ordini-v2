from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
import json

db = SQLAlchemy()


class Project(db.Model):
    """Projects table - main projects tracking"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    customer_name = db.Column(db.String(100), nullable=True)
    printer_type = db.Column(db.String(20), nullable=False)  # '3d_bambu', '3d_flashforge', 'laser_xtool'
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='quote')  # 'quote', 'designing', 'printing', 'completed', 'failed'

    # Voice notes
    voice_note_path = db.Column(db.String(500), nullable=True)
    voice_transcription = db.Column(db.Text, nullable=True)
    settings_notes = db.Column(db.Text, nullable=True)

    # Time tracking
    estimated_time_hours = db.Column(db.Float, nullable=True)
    actual_time_hours = db.Column(db.Float, nullable=True)

    # Costs and pricing
    material_cost = db.Column(db.Float, default=0.0)
    labor_cost = db.Column(db.Float, default=0.0)
    final_price = db.Column(db.Float, default=0.0)
    margin_percentage = db.Column(db.Float, default=30.0)

    # Quantity
    quantity = db.Column(db.Integer, default=1)

    # Photos (JSON array of paths)
    photos = db.Column(db.Text, nullable=True)  # JSON string

    # Project files (JSON array of file paths - PDFs, CAD files, etc.)
    project_files = db.Column(db.Text, nullable=True)  # JSON string

    # Result rating
    result_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    material = db.relationship('Material', backref='projects')
    voice_notes = db.relationship('VoiceNote', backref='project', lazy=True, cascade='all, delete-orphan')

    def get_photos(self):
        """Get photos as list"""
        if self.photos:
            try:
                return json.loads(self.photos)
            except:
                return []
        return []

    def set_photos(self, photos_list):
        """Set photos from list"""
        self.photos = json.dumps(photos_list)

    def get_files(self):
        """Get project files as list"""
        if self.project_files:
            try:
                return json.loads(self.project_files)
            except:
                return []
        return []

    def set_files(self, files_list):
        """Set project files from list"""
        self.project_files = json.dumps(files_list)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'customer_name': self.customer_name,
            'printer_type': self.printer_type,
            'material_id': self.material_id,
            'status': self.status,
            'estimated_time_hours': self.estimated_time_hours,
            'actual_time_hours': self.actual_time_hours,
            'material_cost': self.material_cost,
            'labor_cost': self.labor_cost,
            'final_price': self.final_price,
            'margin_percentage': self.margin_percentage,
            'quantity': self.quantity,
            'photos': self.get_photos(),
            'result_rating': self.result_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'material_name': self.material.name if self.material else None
        }


class Material(db.Model):
    """Materials table - filaments, sheets for laser"""
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # 'pla', 'petg', 'abs', 'tpu', 'resin', 'wood_laser', 'acrylic_laser', 'metal_laser'
    printer_compatible = db.Column(db.String(100), nullable=True)  # comma-separated: "3d_bambu,3d_flashforge"
    color = db.Column(db.String(50), nullable=True)

    # Costs
    cost_per_kg = db.Column(db.Float, nullable=True)  # for 3D printing
    cost_per_sheet = db.Column(db.Float, nullable=True)  # for laser

    # Stock management
    current_stock_kg = db.Column(db.Float, default=0.0)
    initial_stock_kg = db.Column(db.Float, default=1.0)  # for percentage calculation

    # QR Code
    qr_code = db.Column(db.String(100), nullable=True, unique=True)

    # Optimal settings
    optimal_temp = db.Column(db.Integer, nullable=True)
    optimal_speed = db.Column(db.Integer, nullable=True)

    # Voice notes
    voice_notes = db.Column(db.Text, nullable=True)

    # Last used
    last_used = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def stock_percentage(self):
        """Calculate stock percentage"""
        if self.initial_stock_kg <= 0:
            return 0
        return (self.current_stock_kg / self.initial_stock_kg) * 100

    def stock_status(self):
        """Get stock status color"""
        pct = self.stock_percentage()
        if pct > 30:
            return 'success'  # Green
        elif pct > 10:
            return 'warning'  # Yellow
        else:
            return 'danger'  # Red

    def is_compatible_with(self, printer_type):
        """Check if material is compatible with printer"""
        if not self.printer_compatible:
            return True
        return printer_type in self.printer_compatible.split(',')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'printer_compatible': self.printer_compatible,
            'color': self.color,
            'cost_per_kg': self.cost_per_kg,
            'cost_per_sheet': self.cost_per_sheet,
            'current_stock_kg': self.current_stock_kg,
            'stock_percentage': self.stock_percentage(),
            'stock_status': self.stock_status(),
            'qr_code': self.qr_code,
            'optimal_temp': self.optimal_temp,
            'optimal_speed': self.optimal_speed,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }


class PrintProfile(db.Model):
    """Print profiles - saved optimal settings"""
    __tablename__ = 'print_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    printer_type = db.Column(db.String(20), nullable=False)
    material_type = db.Column(db.String(30), nullable=False)

    # Settings
    layer_height = db.Column(db.Float, nullable=True)
    speed_mm_s = db.Column(db.Integer, nullable=True)
    infill_percent = db.Column(db.Integer, nullable=True)
    supports = db.Column(db.Boolean, default=False)

    # Notes
    voice_notes = db.Column(db.Text, nullable=True)

    # Success tracking
    success_rate = db.Column(db.Float, default=100.0)  # percentage
    times_used = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'printer_type': self.printer_type,
            'material_type': self.material_type,
            'layer_height': self.layer_height,
            'speed_mm_s': self.speed_mm_s,
            'infill_percent': self.infill_percent,
            'supports': self.supports,
            'success_rate': self.success_rate,
            'times_used': self.times_used
        }


class Quote(db.Model):
    """Quotes table - quick quotes and estimates"""
    __tablename__ = 'quotes'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Voice request
    voice_request = db.Column(db.Text, nullable=True)  # transcription

    # Pricing
    estimated_price = db.Column(db.Float, nullable=False)

    # Status
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'

    # PDF
    pdf_path = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    project = db.relationship('Project', backref='quotes')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'customer_name': self.customer_name,
            'description': self.description,
            'voice_request': self.voice_request,
            'estimated_price': self.estimated_price,
            'status': self.status,
            'pdf_path': self.pdf_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VoiceNote(db.Model):
    """Voice notes - additional notes for projects"""
    __tablename__ = 'voice_notes'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    audio_path = db.Column(db.String(500), nullable=False)
    transcription = db.Column(db.Text, nullable=True)
    note_type = db.Column(db.String(50), default='general')  # 'general', 'problem', 'modification', 'result'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'audio_path': self.audio_path,
            'transcription': self.transcription,
            'note_type': self.note_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Settings(db.Model):
    """Application settings"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key, default=None):
        """Get setting value"""
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        """Set setting value"""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()
        return setting
