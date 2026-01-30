#!/usr/bin/env python3
# backend/server.py - SUNSET BAR - TUTTO IN ordini_v2.db

import os
import sys
import time
import queue
import threading
import subprocess
import logging
import traceback
import json
import re
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func, desc

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
# Base directory - directory padre del progetto (gestionale-ordini-v2)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Database in backend/ordini.db
DB_FILE = os.path.join(BASE_DIR, "backend", "ordini.db")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__, static_folder="frontend", static_url_path="")
app.config.update(
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_FILE}",
    SQLALCHEMY_TRACK_MODIFICATIONS = False
)
CORS(app)
db = SQLAlchemy(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "gestionale.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info("="*60)
logging.info("🌅 SUNSET BAR - Gestionale Ordini")
logging.info(f"📁 BASE_DIR: {BASE_DIR}")
logging.info(f"💾 Database: {DB_FILE}")
logging.info("="*60)

# ══════════════════════════════════════════════════════════════════════════════
# GRUPPI STAMPANTI
# ══════════════════════════════════════════════════════════════════════════════
CUCINA_GROUPS = [
    'TOAST', 'BRUSCHETTE', 'PANINI A PANE MORBIDO',
    'BURGER & SPECIALITA CALDE', 'PIADINE ARTIGIANALI'
]

# ══════════════════════════════════════════════════════════════════════════════
# MODELLI DATABASE
# ══════════════════════════════════════════════════════════════════════════════
class Voce(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gruppo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    prezzo = db.Column(db.Float, nullable=False)
    destinazione_stampa = db.Column(db.String(20), default='cucina', nullable=False)
    ordinamento = db.Column(db.Integer, default=0)

class Comanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tavolo = db.Column(db.String(20), nullable=False)
    testo = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StoricoOrdini(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tavolo = db.Column(db.String(20), nullable=False)
    testo = db.Column(db.Text, nullable=False)
    totale = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

class StatisticheArticoli(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    articolo_id = db.Column(db.Integer, nullable=False)
    articolo_nome = db.Column(db.String(100), nullable=False)
    articolo_gruppo = db.Column(db.String(50), nullable=False)
    quantita = db.Column(db.Integer, default=1)
    prezzo_unitario = db.Column(db.Float, nullable=False)
    data_ordine = db.Column(db.DateTime, default=datetime.utcnow)
    tavolo = db.Column(db.String(20))

class PagamentiParziali(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'), nullable=False)
    articoli_pagati = db.Column(db.Text, nullable=False)
    importo_pagato = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(200), default="")

# NUOVI MODELLI - AGGIUNTE/RIMOZIONI
class Aggiunta(db.Model):
    __tablename__ = 'aggiunte'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    prezzo = db.Column(db.Float, nullable=False)
    attivo = db.Column(db.Integer, default=1)
    ordinamento = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Rimozione(db.Model):
    __tablename__ = 'rimozioni'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    attivo = db.Column(db.Integer, default=1)
    ordinamento = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ══════════════════════════════════════════════════════════════════════════════
# MODELLO SALE/TAVOLI
# ══════════════════════════════════════════════════════════════════════════════
class ConfigurazioneSala(db.Model):
    __tablename__ = 'configurazione_sale'
    id = db.Column(db.Integer, primary_key=True)
    codice_sala = db.Column(db.String(20), unique=True, nullable=False)
    nome_sala = db.Column(db.String(50), nullable=False)
    icona = db.Column(db.String(10), default='🏠')
    colore = db.Column(db.String(20), default='#007bff')
    numero_inizio = db.Column(db.Integer, nullable=False)
    numero_tavoli = db.Column(db.Integer, nullable=False)
    attivo = db.Column(db.Integer, default=1)
    ordinamento = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ══════════════════════════════════════════════════════════════════════════════
# MODELLO TASTI RAPIDI
# ══════════════════════════════════════════════════════════════════════════════
class TastoRapido(db.Model):
    __tablename__ = 'tasti_rapidi'
    id = db.Column(db.Integer, primary_key=True)
    articolo_id = db.Column(db.Integer, db.ForeignKey('voce.id'), nullable=False)
    ordinamento = db.Column(db.Integer, default=0)
    attivo = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_USER = "admin"
ADMIN_PW = "Peugeot2590"

def _auth(user: str, pw: str) -> bool:
    return user == ADMIN_USER and pw == ADMIN_PW

def _deny():
    return Response("Accesso negato", 401,
                   {'WWW-Authenticate': 'Basic realm="Sunset Bar Admin"'})

def requires_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        au = request.authorization
        if not au or not _auth(au.username, au.password):
            return _deny()
        return f(*args, **kwargs)
    return wrapper

# ══════════════════════════════════════════════════════════════════════════════
# MIGRATION DATABASE
# ══════════════════════════════════════════════════════════════════════════════
def migrate_database():
    """Aggiunge colonne mancanti"""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(db.text("PRAGMA table_info(voce)"))
            columns = [row[1] for row in result]

            if 'destinazione_stampa' not in columns:
                logging.info("Aggiunta colonna destinazione_stampa")
                conn.execute(db.text("ALTER TABLE voce ADD COLUMN destinazione_stampa VARCHAR(20) DEFAULT 'cucina'"))
                for gruppo in CUCINA_GROUPS:
                    conn.execute(db.text("UPDATE voce SET destinazione_stampa = 'cucina' WHERE gruppo = :gruppo"), {"gruppo": gruppo})
                conn.commit()
                logging.info("✓ Migrazione destinazione_stampa completata")

            if 'ordinamento' not in columns:
                logging.info("Aggiunta colonna ordinamento")
                conn.execute(db.text("ALTER TABLE voce ADD COLUMN ordinamento INTEGER DEFAULT 0"))
                conn.commit()
                logging.info("✓ Migrazione ordinamento completata")
    except Exception as e:
        logging.error(f"Errore migrazione: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS ORDINI
# ══════════════════════════════════════════════════════════════════════════════
def calculate_total_from_text(order_text):
    total = 0.0
    for line in order_text.split('\n'):
        line = line.strip()
        if not line or '€' not in line:
            continue
        try:
            matches = re.findall(r'€(\d+[.,]\d{2})', line)
            if matches:
                total += float(matches[-1].replace(',', '.'))
        except:
            continue
    return total

def add_total_to_order(order_text, total):
    lines = order_text.strip().split('\n')
    lines.append('-' * 32)
    lines.append(f'TOTALE: €{total:.2f}')
    return '\n'.join(lines)

def save_to_history(comanda_obj):
    totale = calculate_total_from_text(comanda_obj.testo)
    storico = StoricoOrdini(
        tavolo=comanda_obj.tavolo,
        testo=comanda_obj.testo,
        totale=totale,
        created_at=comanda_obj.created_at,
        completed_at=datetime.utcnow()
    )
    db.session.add(storico)
    db.session.commit()
    logging.info(f"✓ Ordine tavolo {comanda_obj.tavolo} archiviato")

def save_statistics(items, tavolo):
    for item in items:
        stat = StatisticheArticoli(
            articolo_id=item.get('id', 0),
            articolo_nome=item.get('nome', 'Sconosciuto'),
            articolo_gruppo=item.get('gruppo', 'Altro'),
            quantita=item.get('qty', 1),
            prezzo_unitario=item.get('prezzo', 0),
            tavolo=tavolo
        )
        db.session.add(stat)
    db.session.commit()

def cleanup_old_history():
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    old_orders = StoricoOrdini.query.filter(StoricoOrdini.completed_at < cutoff_date).all()
    if old_orders:
        for order in old_orders:
            db.session.delete(order)
        db.session.commit()
        logging.info(f"🧹 Rimossi {len(old_orders)} ordini vecchi")

def parse_order_text(order_text):
    items = []
    for line in order_text.strip().split('\n'):
        line = line.strip()
        if not line or 'TOTALE:' in line or line.startswith('-'):
            continue
        pattern = r'(\d+)×\s*([^–]+?)\s*–\s*€(\d+[.,]\d{2})'
        match = re.match(pattern, line)
        if match:
            qty = int(match.group(1))
            name_with_notes = match.group(2).strip()
            total_price = float(match.group(3).replace(',', '.'))
            unit_price = total_price / qty
            note = ""
            name = name_with_notes
            if '(' in name_with_notes and ')' in name_with_notes:
                parts = name_with_notes.split('(', 1)
                name = parts[0].strip()
                note = parts[1].replace(')', '').strip()
            items.append({
                'name': name,
                'quantity': qty,
                'unit_price': unit_price,
                'total_price': total_price,
                'note': note,
                'original_line': line
            })
    return items

def rebuild_order_text(items):
    lines = []
    total = 0
    for item in items:
        line = f"{item['quantity']}× {item['name']}"
        if item['note']:
            line += f" ({item['note']})"
        line += f" – €{item['total_price']:.2f}"
        lines.append(line)
        total += item['total_price']
    if lines:
        lines.append('-' * 32)
        lines.append(f'TOTALE: €{total:.2f}')
    return '\n'.join(lines)

def create_partial_bill_text(paid_items, table_number, is_partial=True):
    lines = []
    total = 0
    if is_partial:
        lines.extend([
            f"TAVOLO {table_number}",
            "*** CONTO PARZIALE ***",
            "",
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            ""
        ])
    for item in paid_items:
        line = f"{item['quantity']}× {item['name']}"
        if item['note']:
            line += f" ({item['note']})"
        line += f" – €{item['total_price']:.2f}"
        lines.append(line)
        total += item['total_price']
    lines.extend([
        '-' * 32,
        f'TOTALE PARZIALE: €{total:.2f}'
    ])
    if is_partial:
        lines.extend([
            "",
            "scontrino non fiscale",
            "ritiro scontrino fiscale in cassa"
        ])
    return '\n'.join(lines)

# ══════════════════════════════════════════════════════════════════════════════
# WORKER STAMPA
# ══════════════════════════════════════════════════════════════════════════════
PRINT_QUEUE = queue.Queue()

def _printer_worker():
    script = os.path.join(BASE_DIR, "print_job.py")
    python_path = sys.executable
    
    if not os.path.exists(script):
        logging.error(f"❌ print_job.py non trovato: {script}")
        return
    
    logging.info(f"🖨️  Printer worker avviato: {script}")
    
    while True:
        job = PRINT_QUEUE.get()
        tavolo = job['tavolo']
        testo = job['testo']
        printer_name = job['printer']
        job_type = job.get('job_type', 'new_order')  # Default: ordine nuovo

        try:
            env = os.environ.copy()
            env['PRINTER_NAME'] = printer_name
            env['JOB_TYPE'] = job_type  # Passa il tipo di job
            env['PYTHONPATH'] = BASE_DIR
            
            result = subprocess.run(
                [python_path, script, str(tavolo)],
                input=testo,
                text=True,
                capture_output=True,
                env=env,
                cwd=BASE_DIR
            )
            
            if result.returncode != 0:
                logging.error(f"❌ Stampa {printer_name}: {result.stderr}")
            else:
                logging.info(f"✓ Stampato su {printer_name} - Tavolo {tavolo}")
            
        except Exception as e:
            logging.error(f"❌ Errore stampa: {e}")
        finally:
            PRINT_QUEUE.task_done()

threading.Thread(target=_printer_worker, daemon=True).start()

def enqueue_print(tavolo: str, testo: str, printer: str = 'bar', job_type: str = 'new_order'):
    """
    Accoda una stampa

    job_type può essere:
    - 'new_order': nuovo ordine completo (stampa completa)
    - 'add_items': aggiunta articoli (stampa semplificata)
    """
    logging.info(f"📝 In coda stampa {printer} - Tavolo {tavolo} - Tipo: {job_type}")
    PRINT_QUEUE.put({'tavolo': tavolo, 'testo': testo, 'printer': printer, 'job_type': job_type})

def schedule_cleanup():
    while True:
        time.sleep(86400)
        cleanup_old_history()

threading.Thread(target=schedule_cleanup, daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT MENU
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/menu", methods=["GET"])
def menu_get():
    rows = Voce.query.order_by(Voce.gruppo, Voce.ordinamento, Voce.nome).all()
    return jsonify([{
        "id": x.id,
        "gruppo": x.gruppo,
        "nome": x.nome,
        "prezzo": x.prezzo,
        "destinazione_stampa": x.destinazione_stampa,
        "ordinamento": x.ordinamento
    } for x in rows])

@app.route("/menu", methods=["POST"])
@requires_auth
def menu_add():
    d = request.get_json(force=True)
    v = Voce(
        gruppo=d["gruppo"].strip(),
        nome=d["nome"].strip(),
        prezzo=float(d["prezzo"]),
        destinazione_stampa=d.get("destinazione_stampa", "cucina")
    )
    db.session.add(v)
    db.session.commit()
    return jsonify(ok=True, id=v.id)

@app.route("/menu/<int:vid>", methods=["PUT"])
@requires_auth
def menu_upd(vid):
    d = request.get_json(force=True)
    voce = Voce.query.get_or_404(vid)
    if "gruppo" in d: voce.gruppo = d["gruppo"].strip()
    if "nome" in d: voce.nome = d["nome"].strip()
    if "prezzo" in d: voce.prezzo = float(d["prezzo"])
    if "destinazione_stampa" in d: voce.destinazione_stampa = d["destinazione_stampa"]
    db.session.commit()
    return jsonify(ok=True)

@app.route("/menu/<int:vid>", methods=["DELETE"])
@requires_auth
def menu_del(vid):
    voce = Voce.query.get_or_404(vid)
    db.session.delete(voce)
    db.session.commit()
    return jsonify(ok=True)

@app.route("/menu/riordina", methods=["POST"])
@requires_auth
def menu_riordina():
    """Aggiorna l'ordinamento degli articoli"""
    try:
        d = request.get_json(force=True)
        ordini = d.get('ordini', [])  # Array di {id, ordinamento}

        for item in ordini:
            voce = Voce.query.get(item['id'])
            if voce:
                voce.ordinamento = item['ordinamento']

        db.session.commit()
        return jsonify(ok=True)
    except Exception as e:
        logging.error(f"Errore riordina menu: {e}")
        return jsonify(error=str(e)), 500

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT AGGIUNTE (DA ordini_v2.db)
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/aggiunte", methods=["GET"])
def get_aggiunte():
    """Lista aggiunte ATTIVE raggruppate per categoria"""
    try:
        aggiunte = Aggiunta.query.filter_by(attivo=1).order_by(
            Aggiunta.categoria, Aggiunta.ordinamento, Aggiunta.nome
        ).all()
        
        result = {}
        for agg in aggiunte:
            if agg.categoria not in result:
                result[agg.categoria] = []
            result[agg.categoria].append({
                'id': agg.id,
                'nome': agg.nome,
                'prezzo': agg.prezzo
            })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore /api/aggiunte: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/aggiunte/all", methods=["GET"])
@requires_auth
def get_aggiunte_all():
    """Lista TUTTE le aggiunte (anche disattivate) - per admin"""
    try:
        aggiunte = Aggiunta.query.order_by(
            Aggiunta.categoria, Aggiunta.ordinamento, Aggiunta.nome
        ).all()
        
        return jsonify([{
            'id': a.id,
            'nome': a.nome,
            'categoria': a.categoria,
            'prezzo': a.prezzo,
            'attivo': bool(a.attivo),
            'ordinamento': a.ordinamento
        } for a in aggiunte])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/aggiunte", methods=["POST"])
@requires_auth
def add_aggiunta():
    """Aggiungi nuova aggiunta"""
    try:
        d = request.get_json(force=True)
        agg = Aggiunta(
            nome=d['nome'].strip(),
            categoria=d['categoria'].strip(),
            prezzo=float(d['prezzo']),
            attivo=1,
            ordinamento=d.get('ordinamento', 0)
        )
        db.session.add(agg)
        db.session.commit()
        return jsonify({'ok': True, 'id': agg.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/aggiunte/<int:aid>", methods=["PUT"])
@requires_auth
def update_aggiunta(aid):
    """Modifica aggiunta"""
    try:
        d = request.get_json(force=True)
        agg = Aggiunta.query.get_or_404(aid)
        
        if 'nome' in d: agg.nome = d['nome'].strip()
        if 'categoria' in d: agg.categoria = d['categoria'].strip()
        if 'prezzo' in d: agg.prezzo = float(d['prezzo'])
        if 'attivo' in d: agg.attivo = 1 if d['attivo'] else 0
        if 'ordinamento' in d: agg.ordinamento = int(d['ordinamento'])
        
        agg.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/aggiunte/<int:aid>", methods=["DELETE"])
@requires_auth
def delete_aggiunta(aid):
    """Elimina aggiunta"""
    try:
        agg = Aggiunta.query.get_or_404(aid)
        db.session.delete(agg)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT RIMOZIONI (DA ordini_v2.db)
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/rimozioni", methods=["GET"])
def get_rimozioni():
    """Lista rimozioni ATTIVE raggruppate per categoria"""
    try:
        rimozioni = Rimozione.query.filter_by(attivo=1).order_by(
            Rimozione.categoria, Rimozione.ordinamento, Rimozione.nome
        ).all()
        
        result = {}
        for rim in rimozioni:
            if rim.categoria not in result:
                result[rim.categoria] = []
            result[rim.categoria].append({
                'id': rim.id,
                'nome': rim.nome
            })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore /api/rimozioni: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/rimozioni/all", methods=["GET"])
@requires_auth
def get_rimozioni_all():
    """Lista TUTTE le rimozioni - per admin"""
    try:
        rimozioni = Rimozione.query.order_by(
            Rimozione.categoria, Rimozione.ordinamento, Rimozione.nome
        ).all()
        
        return jsonify([{
            'id': r.id,
            'nome': r.nome,
            'categoria': r.categoria,
            'attivo': bool(r.attivo),
            'ordinamento': r.ordinamento
        } for r in rimozioni])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/rimozioni", methods=["POST"])
@requires_auth
def add_rimozione():
    """Aggiungi nuova rimozione"""
    try:
        d = request.get_json(force=True)
        rim = Rimozione(
            nome=d['nome'].strip(),
            categoria=d['categoria'].strip(),
            attivo=1,
            ordinamento=d.get('ordinamento', 0)
        )
        db.session.add(rim)
        db.session.commit()
        return jsonify({'ok': True, 'id': rim.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/rimozioni/<int:rid>", methods=["PUT"])
@requires_auth
def update_rimozione(rid):
    """Modifica rimozione"""
    try:
        d = request.get_json(force=True)
        rim = Rimozione.query.get_or_404(rid)
        
        if 'nome' in d: rim.nome = d['nome'].strip()
        if 'categoria' in d: rim.categoria = d['categoria'].strip()
        if 'attivo' in d: rim.attivo = 1 if d['attivo'] else 0
        if 'ordinamento' in d: rim.ordinamento = int(d['ordinamento'])
        
        rim.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/rimozioni/<int:rid>", methods=["DELETE"])
@requires_auth
def delete_rimozione(rid):
    """Elimina rimozione"""
    try:
        rim = Rimozione.query.get_or_404(rid)
        db.session.delete(rim)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT ORDINI
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/orders", methods=["GET"])
def orders_get():
    ordini = Comanda.query.order_by(Comanda.created_at.desc()).all()
    result = []
    for o in ordini:
        has_payments = PagamentiParziali.query.filter_by(comanda_id=o.id).count() > 0
        result.append({
            "id": o.id,
            "tavolo": o.tavolo,
            "testo": o.testo,
            "created_at": o.created_at.isoformat(),
            "has_partial_payments": has_payments
        })
    return jsonify(result)

@app.route("/orders", methods=["POST"])
def orders_new():
    d = request.get_json(force=True)
    tavolo = d.get("tavolo","").strip()
    comanda = d.get("comanda","").strip()
    items = d.get("items", [])
    
    if not tavolo or not comanda:
        return jsonify(error="dati mancanti"), 400

    rec = Comanda(tavolo=tavolo, testo=comanda)
    db.session.add(rec)
    db.session.commit()
    
    if items:
        save_statistics(items, tavolo)

    # Stampa cucina E bancone - dividi in base a destinazione_stampa
    cucina_items = []
    bancone_items = []

    if items:
        for item in items:
            voce = Voce.query.filter_by(id=item.get('id')).first()
            destinazione = 'cucina'

            if voce and voce.destinazione_stampa:
                destinazione = voce.destinazione_stampa
            elif item.get('gruppo', '') in CUCINA_GROUPS:
                destinazione = 'cucina'
            else:
                destinazione = 'bancone'

            line = f"{item['qty']}× {item['nome']}"
            if item.get('note'):
                line += f" ({item['note']})"

            # Aggiungi a cucina se destinazione = 'cucina' o 'entrambi'
            if destinazione in ['cucina', 'entrambi']:
                cucina_items.append(line)

            # Aggiungi a bancone se destinazione = 'bancone' o 'entrambi'
            if destinazione in ['bancone', 'entrambi']:
                bancone_items.append(line)

    # Stampa in cucina solo gli articoli destinati alla cucina
    if cucina_items:
        enqueue_print(tavolo, '\n'.join(cucina_items), 'cucina')

    # Stampa al bancone solo gli articoli destinati al bancone
    if bancone_items:
        total = calculate_total_from_text(comanda)
        bancone_text = '\n'.join(bancone_items)
        bancone_con_totale = add_total_to_order(bancone_text, total)
        enqueue_print(tavolo, bancone_con_totale, 'bar')

    return jsonify(ok=True, id=rec.id)

@app.route("/orders/<int:oid>/reprint", methods=["POST"])
def orders_reprint(oid):
    o = Comanda.query.get_or_404(oid)
    total = calculate_total_from_text(o.testo)
    testo_con_totale = add_total_to_order(o.testo, total)
    enqueue_print(o.tavolo, testo_con_totale, 'bar')
    return jsonify(ok=True)

@app.route("/orders/<int:oid>", methods=["PUT"])
def orders_update(oid):
    d = request.get_json(force=True) or {}
    o = Comanda.query.get_or_404(oid)
    if "tavolo" in d: o.tavolo = d["tavolo"].strip()
    if "testo" in d: o.testo = d["testo"]
    db.session.commit()
    return jsonify(ok=True)

@app.route("/orders/<int:oid>", methods=["DELETE"])
def orders_del(oid):
    o = Comanda.query.get_or_404(oid)
    save_to_history(o)
    db.session.delete(o)
    db.session.commit()
    return jsonify(ok=True)

@app.route("/orders/<int:oid>/complete", methods=["POST"])
def complete_order(oid):
    """Completa ordine e archivia"""
    try:
        o = Comanda.query.get_or_404(oid)
        save_to_history(o)
        db.session.delete(o)
        db.session.commit()
        return jsonify(ok=True)
    except Exception as e:
        logging.error(f"Errore complete: {e}")
        return jsonify(error=str(e)), 500

@app.route("/orders/<int:oid>/add-items", methods=["POST"])
def add_items_to_order(oid):
    """Aggiunge articoli a un ordine esistente"""
    try:
        o = Comanda.query.get_or_404(oid)
        data = request.get_json(force=True)
        new_items = data.get('items', [])

        if not new_items:
            return jsonify(error="Nessun articolo da aggiungere"), 400

        # Costruisci testo nuovi articoli
        new_text = ''
        for item in new_items:
            prezzo_base = item['prezzo'] * item['qty']
            costo_aggiunte = sum(a.get('prezzo', 0) * item['qty'] for a in item.get('aggiunte', []))
            totale_item = prezzo_base + costo_aggiunte

            riga = f"{item['qty']}× {item['nome']}"

            if item.get('aggiunte') or item.get('rimozioni') or item.get('note'):
                details = []
                if item.get('aggiunte'):
                    details.append(f"+ {', '.join(a['nome'] for a in item['aggiunte'])}")
                if item.get('rimozioni'):
                    details.append(f"− {', '.join(r['nome'] for r in item['rimozioni'])}")
                if item.get('note'):
                    details.append(item['note'])
                riga += f" ({' | '.join(details)})"

            riga += f" – €{totale_item:.2f}"
            new_text += riga + '\n'

        # Rimuovi TOTALE dall'ordine esistente se presente
        current_lines = o.testo.split('\n')
        filtered_lines = [line for line in current_lines if 'TOTALE:' not in line and line.strip() != '-' * 32]

        # Combina ordine esistente + nuovi articoli
        o.testo = '\n'.join(filtered_lines).strip() + '\n' + new_text.strip()
        db.session.commit()

        # Salva statistiche per i nuovi articoli
        if new_items:
            save_statistics(new_items, o.tavolo)

        # Stampa cucina E bancone (solo nuovi articoli)
        cucina_items = []
        bancone_items = []

        for item in new_items:
            voce = Voce.query.filter_by(id=item.get('id')).first()
            destinazione = 'cucina'

            if voce and voce.destinazione_stampa:
                destinazione = voce.destinazione_stampa
            elif item.get('gruppo', '') in CUCINA_GROUPS:
                destinazione = 'cucina'
            else:
                destinazione = 'bancone'

            # Costruisci riga con personalizzazioni
            line = f"{item['qty']}× {item['nome']}"
            if item.get('aggiunte'):
                line += f" (+ {', '.join(a['nome'] for a in item['aggiunte'])})"
            if item.get('rimozioni'):
                line += f" (− {', '.join(r['nome'] for r in item['rimozioni'])})"
            if item.get('note'):
                line += f" ({item['note']})"

            # Aggiungi alle liste appropriate
            if destinazione in ['cucina', 'entrambi']:
                cucina_items.append(line)
            if destinazione in ['bancone', 'entrambi']:
                bancone_items.append(line)

        # Stampa SOLO nuovi articoli in cucina (con flag "aggiunta")
        if cucina_items:
            enqueue_print(o.tavolo, '\n'.join(cucina_items), 'cucina', job_type='add_items')

        # Stampa SOLO nuovi articoli al bancone (con flag "aggiunta")
        if bancone_items:
            enqueue_print(o.tavolo, '\n'.join(bancone_items), 'bar', job_type='add_items')

        logging.info(f"✓ Aggiunti {len(new_items)} articoli all'ordine {oid} - Tavolo {o.tavolo} (Cucina: {len(cucina_items)}, Bancone: {len(bancone_items)})")

        total = calculate_total_from_text(o.testo)
        return jsonify(ok=True, new_total=total, updated_text=o.testo)
    except Exception as e:
        logging.error(f"Errore add_items: {e}")
        return jsonify(error=str(e)), 500

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT DIVIDI CONTO
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/orders/<int:oid>/split", methods=["POST"])
def split_order(oid):
    try:
        comanda = Comanda.query.get_or_404(oid)
        data = request.get_json(force=True)
        paid_items = data.get('paid_items', [])
        print_receipt = data.get('print_receipt', True)
        
        if not paid_items:
            return jsonify(error="Nessun articolo selezionato"), 400
        
        importo_pagato = sum(item['total_price'] for item in paid_items)
        
        pagamento = PagamentiParziali(
            comanda_id=oid,
            articoli_pagati=json.dumps(paid_items),
            importo_pagato=importo_pagato,
            note=f"Pagamento parziale di {len(paid_items)} articoli"
        )
        db.session.add(pagamento)
        
        all_items = parse_order_text(comanda.testo)
        remaining_items = []

        # Crea una copia di paid_items per tracciare quanto è stato pagato
        paid_items_tracking = []
        for paid_item in paid_items:
            paid_items_tracking.append({
                'name': paid_item['name'],
                'note': paid_item.get('note', ''),
                'unit_price': paid_item['unit_price'],
                'quantity_left': paid_item['quantity']
            })

        for item in all_items:
            remaining_qty = item['quantity']

            # Cerca match e sottrai le quantità pagate
            for paid_track in paid_items_tracking:
                if (item['name'] == paid_track['name'] and
                    item['note'] == paid_track['note'] and
                    abs(item['unit_price'] - paid_track['unit_price']) < 0.01 and
                    paid_track['quantity_left'] > 0):

                    # Calcola quanto sottrarre
                    qty_to_subtract = min(remaining_qty, paid_track['quantity_left'])
                    remaining_qty -= qty_to_subtract
                    paid_track['quantity_left'] -= qty_to_subtract

                    if remaining_qty <= 0:
                        break

            # Se rimane qualcosa, aggiungilo agli articoli rimanenti
            if remaining_qty > 0:
                remaining_items.append({
                    **item,
                    'quantity': remaining_qty,
                    'total_price': remaining_qty * item['unit_price']
                })
        
        if remaining_items:
            comanda.testo = rebuild_order_text(remaining_items)
        else:
            comanda.testo = "Ordine completato - tutti gli articoli pagati"
        
        db.session.commit()
        
        if print_receipt:
            partial_bill_text = create_partial_bill_text(paid_items, comanda.tavolo)
            enqueue_print(comanda.tavolo, partial_bill_text, 'bar')

        # Calcola totale rimanente per verifica
        remaining_total = sum(item['total_price'] for item in remaining_items)

        logging.info(f"💳 Conto diviso ordine {oid} Tavolo {comanda.tavolo}: Pagato €{importo_pagato:.2f}, Rimanente €{remaining_total:.2f} ({len(remaining_items)} articoli)")

        return jsonify({
            'ok': True,
            'importo_pagato': importo_pagato,
            'totale_rimanente': remaining_total,
            'articoli_rimanenti': len(remaining_items),
            'ordine_completato': len(remaining_items) == 0
        })
    except Exception as e:
        logging.error(f"Errore split: {e}")
        return jsonify(error=str(e)), 500

@app.route("/orders/<int:oid>/payments", methods=["GET"])
def get_order_payments(oid):
    try:
        pagamenti = PagamentiParziali.query.filter_by(comanda_id=oid).order_by(
            PagamentiParziali.created_at.desc()
        ).all()
        result = []
        for p in pagamenti:
            result.append({
                'id': p.id,
                'importo': p.importo_pagato,
                'articoli': json.loads(p.articoli_pagati),
                'created_at': p.created_at.isoformat(),
                'note': p.note
            })
        return jsonify(result)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/orders/<int:oid>/details", methods=["GET"])
def get_order_details(oid):
    """Restituisce dettagli ordine con articoli NON ancora pagati

    IMPORTANTE: comanda.testo è già aggiornato da split_order() per contenere
    solo gli articoli rimanenti. NON dobbiamo sottrarre nulla qui!
    """
    try:
        comanda = Comanda.query.get_or_404(oid)

        # comanda.testo contiene GIÀ solo gli articoli rimanenti da pagare
        # perché split_order() lo aggiorna ogni volta che si fa un pagamento parziale
        current_items = parse_order_text(comanda.testo)

        # Carica tutti i pagamenti parziali (solo per storico)
        pagamenti = PagamentiParziali.query.filter_by(comanda_id=oid).order_by(
            PagamentiParziali.created_at.desc()
        ).all()

        payments_history = []
        total_paid = 0

        for p in pagamenti:
            paid_items = json.loads(p.articoli_pagati)
            payments_history.append({
                'id': p.id,
                'importo': p.importo_pagato,
                'articoli': paid_items,
                'created_at': p.created_at.isoformat(),
                'note': p.note
            })
            total_paid += p.importo_pagato

        # Calcola totale rimanente DIRETTAMENTE da current_items
        # (che sono GIÀ solo gli articoli non pagati)
        current_total = sum(item['total_price'] for item in current_items)

        logging.info(f"📋 Dettagli ordine {oid} Tavolo {comanda.tavolo}: Rimanente da pagare €{current_total:.2f}, Già pagato €{total_paid:.2f}, Articoli rimasti: {len(current_items)}")

        return jsonify({
            'id': comanda.id,
            'tavolo': comanda.tavolo,
            'testo': comanda.testo,
            'created_at': comanda.created_at.isoformat(),
            'current_items': current_items,      # Articoli da comanda.testo (già solo i rimanenti)
            'current_total': current_total,      # Totale da pagare
            'payments_history': payments_history, # Storico pagamenti
            'total_paid': total_paid,            # Totale già pagato
            'has_payments': len(payments_history) > 0
        })
    except Exception as e:
        logging.error(f"Errore get_order_details: {e}")
        return jsonify(error=str(e)), 500

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT STORICO E STATISTICHE
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/storico", methods=["GET"])
@requires_auth
def get_storico():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    
    query = StoricoOrdini.query
    if date_from:
        query = query.filter(StoricoOrdini.completed_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(StoricoOrdini.completed_at <= datetime.fromisoformat(date_to))
    
    ordini = query.order_by(StoricoOrdini.completed_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'ordini': [{
            'id': o.id,
            'tavolo': o.tavolo,
            'testo': o.testo,
            'totale': o.totale,
            'created_at': o.created_at.isoformat(),
            'completed_at': o.completed_at.isoformat()
        } for o in ordini.items],
        'total': ordini.total,
        'pages': ordini.pages,
        'current_page': page
    })

@app.route("/api/statistiche/articoli", methods=["GET"])
@requires_auth
def get_statistiche_articoli():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=7)).isoformat()
    if not date_to:
        date_to = datetime.utcnow().isoformat()
    
    stats = db.session.query(
        StatisticheArticoli.articolo_nome,
        StatisticheArticoli.articolo_gruppo,
        func.sum(StatisticheArticoli.quantita).label('quantita_totale'),
        func.sum(StatisticheArticoli.quantita * StatisticheArticoli.prezzo_unitario).label('ricavo_totale'),
        func.count(StatisticheArticoli.id).label('ordini_totali')
    ).filter(
        StatisticheArticoli.data_ordine >= datetime.fromisoformat(date_from),
        StatisticheArticoli.data_ordine <= datetime.fromisoformat(date_to)
    ).group_by(
        StatisticheArticoli.articolo_nome,
        StatisticheArticoli.articolo_gruppo
    ).order_by(desc('quantita_totale')).all()
    
    return jsonify({
        'periodo': {'from': date_from, 'to': date_to},
        'articoli': [{
            'nome': s.articolo_nome,
            'gruppo': s.articolo_gruppo,
            'quantita_totale': s.quantita_totale,
            'ricavo_totale': round(s.ricavo_totale, 2),
            'ordini_totali': s.ordini_totali
        } for s in stats]
    })

@app.route("/api/statistiche/gruppi", methods=["GET"])
@requires_auth
def get_statistiche_gruppi():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=7)).isoformat()
    if not date_to:
        date_to = datetime.utcnow().isoformat()
    
    stats = db.session.query(
        StatisticheArticoli.articolo_gruppo,
        func.sum(StatisticheArticoli.quantita).label('quantita_totale'),
        func.sum(StatisticheArticoli.quantita * StatisticheArticoli.prezzo_unitario).label('ricavo_totale')
    ).filter(
        StatisticheArticoli.data_ordine >= datetime.fromisoformat(date_from),
        StatisticheArticoli.data_ordine <= datetime.fromisoformat(date_to)
    ).group_by(
        StatisticheArticoli.articolo_gruppo
    ).order_by(desc('ricavo_totale')).all()
    
    return jsonify({
        'periodo': {'from': date_from, 'to': date_to},
        'gruppi': [{
            'gruppo': s.articolo_gruppo,
            'quantita_totale': s.quantita_totale,
            'ricavo_totale': round(s.ricavo_totale, 2)
        } for s in stats]
    })

# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT CONFIGURAZIONE SALE
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/configurazione-sale", methods=["GET"])
def get_configurazione_sale():
    """Lista sale con configurazione tavoli"""
    try:
        sale = ConfigurazioneSala.query.filter_by(attivo=1).order_by(
            ConfigurazioneSala.ordinamento, ConfigurazioneSala.codice_sala
        ).all()
        
        result = []
        for sala in sale:
            tavoli = []
            for i in range(sala.numero_tavoli):
                numero_tavolo = sala.numero_inizio + i
                tavoli.append({
                    'numero': numero_tavolo,
                    'label': f"{sala.nome_sala} {numero_tavolo}"
                })
            
            result.append({
                'codice_sala': sala.codice_sala,
                'nome_sala': sala.nome_sala,
                'icona': sala.icona,
                'colore': sala.colore,
                'numero_inizio': sala.numero_inizio,
                'numero_tavoli': sala.numero_tavoli,
                'tavoli': tavoli
            })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore /api/configurazione-sale: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/configurazione-sale", methods=["POST"])
@requires_auth
def update_configurazione_sala():
    """Aggiorna configurazione sala"""
    try:
        d = request.get_json(force=True)
        codice = d.get('codice_sala')
        
        sala = ConfigurazioneSala.query.filter_by(codice_sala=codice).first()
        if not sala:
            return jsonify({'error': 'Sala non trovata'}), 404
        
        if 'nome_sala' in d:
            sala.nome_sala = d['nome_sala'].strip()
        if 'numero_tavoli' in d:
            sala.numero_tavoli = int(d['numero_tavoli'])
        if 'icona' in d:
            sala.icona = d['icona']
        if 'colore' in d:
            sala.colore = d['colore']
        
        sala.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'ok': True})
    except Exception as e:
        logging.error(f"Errore update sala: {e}")
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT TASTI RAPIDI
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/tasti-rapidi", methods=["GET"])
def get_tasti_rapidi():
    """Restituisce gli articoli configurati come tasti rapidi"""
    try:
        tasti = TastoRapido.query.filter_by(attivo=1).order_by(TastoRapido.ordinamento).all()
        
        result = []
        for tasto in tasti:
            articolo = Voce.query.get(tasto.articolo_id)
            if articolo:
                result.append({
                    'id': tasto.id,
                    'articolo_id': articolo.id,
                    'nome': articolo.nome,
                    'gruppo': articolo.gruppo,
                    'prezzo': articolo.prezzo,
                    'ordinamento': tasto.ordinamento
                })
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore /api/tasti-rapidi: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/tasti-rapidi", methods=["POST"])
@requires_auth
def add_tasto_rapido():
    """Aggiunge un articolo ai tasti rapidi"""
    try:
        d = request.get_json(force=True)
        articolo_id = d.get('articolo_id')
        
        if not articolo_id:
            return jsonify({'error': 'articolo_id mancante'}), 400
        
        # Verifica che l'articolo esista
        articolo = Voce.query.get(articolo_id)
        if not articolo:
            return jsonify({'error': 'Articolo non trovato'}), 404
        
        # Verifica che non sia già presente
        existing = TastoRapido.query.filter_by(articolo_id=articolo_id, attivo=1).first()
        if existing:
            return jsonify({'error': 'Articolo già presente nei tasti rapidi'}), 400
        
        # Calcola ordinamento (ultimo + 1)
        max_ord = db.session.query(func.max(TastoRapido.ordinamento)).scalar() or 0
        
        tasto = TastoRapido(
            articolo_id=articolo_id,
            ordinamento=max_ord + 1,
            attivo=1
        )
        db.session.add(tasto)
        db.session.commit()
        
        return jsonify({'ok': True, 'id': tasto.id})
    except Exception as e:
        logging.error(f"Errore add tasto rapido: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/tasti-rapidi/<int:id>", methods=["DELETE"])
@requires_auth
def delete_tasto_rapido(id):
    """Rimuove un tasto rapido"""
    try:
        tasto = TastoRapido.query.get(id)
        if not tasto:
            return jsonify({'error': 'Tasto rapido non trovato'}), 404
        
        tasto.attivo = 0
        db.session.commit()
        
        return jsonify({'ok': True})
    except Exception as e:
        logging.error(f"Errore delete tasto rapido: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/tasti-rapidi/ordina", methods=["POST"])
@requires_auth
def ordina_tasti_rapidi():
    """Aggiorna l'ordine dei tasti rapidi"""
    try:
        d = request.get_json(force=True)
        ordini = d.get('ordini', [])  # Array di {id, ordinamento}
        
        for item in ordini:
            tasto = TastoRapido.query.get(item['id'])
            if tasto:
                tasto.ordinamento = item['ordinamento']
        
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        logging.error(f"Errore ordina tasti rapidi: {e}")
        return jsonify({'error': str(e)}), 500

# FILE STATICI
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/admin.html")
@requires_auth
def admin_html():
    return send_from_directory(app.static_folder, "admin.html")

@app.route("/storico.html")
@requires_auth
def storico_html():
    return send_from_directory(app.static_folder, "storico.html")

@app.route("/statistiche.html")
@requires_auth
def statistiche_html():
    return send_from_directory(app.static_folder, "statistiche.html")

@app.route("/", defaults={"path":"index.html"})
@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.info("🔧 Inizializzazione database...")
    with app.app_context():
        db.create_all()
        migrate_database()
        cleanup_old_history()
        
        # Check tabelle aggiunte/rimozioni
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Inizializza sale se non esistono
        if 'configurazione_sale' in tables:
            sale_count = ConfigurazioneSala.query.count()
            if sale_count == 0:
                logging.info("Inizializzazione configurazione sale...")
                sale_default = [
                    ConfigurazioneSala(
                        codice_sala='interno1', nome_sala='Interno 1', icona='🏠',
                        colore='#007bff', numero_inizio=1, numero_tavoli=15, ordinamento=1
                    ),
                    ConfigurazioneSala(
                        codice_sala='interno2', nome_sala='Interno 2', icona='🏠',
                        colore='#6f42c1', numero_inizio=16, numero_tavoli=15, ordinamento=2
                    ),
                    ConfigurazioneSala(
                        codice_sala='esterno', nome_sala='Esterno', icona='☀️',
                        colore='#fd7e14', numero_inizio=31, numero_tavoli=15, ordinamento=3
                    ),
                    ConfigurazioneSala(
                        codice_sala='asporto', nome_sala='Asporto', icona='📦',
                        colore='#28a745', numero_inizio=50, numero_tavoli=1, ordinamento=4
                    )
                ]
                for sala in sale_default:
                    db.session.add(sala)
                db.session.commit()
                logging.info("✓ 4 sale configurate")
            else:
                logging.info(f"✓ Sale configurate: {sale_count}")
        
        if 'aggiunte' not in tables or 'rimozioni' not in tables:
            logging.warning("="*60)
            logging.warning("⚠️  TABELLE AGGIUNTE/RIMOZIONI NON TROVATE!")
            logging.warning("="*60)
            logging.warning("Esegui: python3 aggiungi_tabelle_aggiunte.py")
            logging.warning("="*60)
        else:
            agg_count = Aggiunta.query.filter_by(attivo=1).count()
            rim_count = Rimozione.query.filter_by(attivo=1).count()
            logging.info(f"✓ Aggiunte attive: {agg_count}")
            logging.info(f"✓ Rimozioni attive: {rim_count}")
    
    logging.info("="*60)
    # Porta configurabile da variabile d'ambiente (default: 5000)
    port = int(os.environ.get('FLASK_PORT', 5000))

    logging.info("🌅 SUNSET BAR - Server in ascolto")
    logging.info(f"🌐 URL: http://0.0.0.0:{port}")
    logging.info(f"💾 Database: {DB_FILE}")
    logging.info(f"🔧 Modalità: {'TEST (porta 44321)' if port == 44321 else 'PRODUZIONE (porta 5000)'}")
    logging.info("="*60)

    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
