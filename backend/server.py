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
BASE_DIR = "/home/sunsetbar/gestionale-ordini-v2"
DB_FILE = os.path.join(BASE_DIR, "ordini_v2.db")
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
# MODELLI FATTURAZIONE ELETTRONICA
# ══════════════════════════════════════════════════════════════════════════════
class Cliente(db.Model):
    __tablename__ = 'clienti'
    id = db.Column(db.Integer, primary_key=True)
    tipo_soggetto = db.Column(db.String(20), default='azienda')  # azienda, privato
    partita_iva = db.Column(db.String(11))  # Solo per aziende
    codice_fiscale = db.Column(db.String(16), nullable=False)
    ragione_sociale = db.Column(db.String(200))  # Per aziende
    nome = db.Column(db.String(100))  # Per privati
    cognome = db.Column(db.String(100))  # Per privati
    indirizzo = db.Column(db.String(200), nullable=False)
    cap = db.Column(db.String(5), nullable=False)
    citta = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(2), nullable=False)
    nazione = db.Column(db.String(2), default='IT')
    codice_destinatario = db.Column(db.String(7), default='0000000')  # SDI 7 caratteri
    pec = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(200))
    note = db.Column(db.Text)
    attivo = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Fattura(db.Model):
    __tablename__ = 'fatture'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False)  # Progressivo annuale
    anno = db.Column(db.Integer, nullable=False)
    data_emissione = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'))  # Link all'ordine
    imponibile = db.Column(db.Float, nullable=False, default=0)
    iva = db.Column(db.Float, nullable=False, default=0)
    totale = db.Column(db.Float, nullable=False, default=0)
    percorso_xml = db.Column(db.String(500))
    stato = db.Column(db.String(20), default='bozza')  # bozza, emessa, inviata, errore
    tipo_documento = db.Column(db.String(10), default='TD01')  # TD01=Fattura, TD04=Nota Credito
    fattura_riferimento_id = db.Column(db.Integer, db.ForeignKey('fatture.id'))  # Per note di credito
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazioni
    cliente = db.relationship('Cliente', backref='fatture')
    fattura_riferimento = db.relationship('Fattura', remote_side=[id], backref='note_credito')

class RigaFattura(db.Model):
    __tablename__ = 'righe_fattura'
    id = db.Column(db.Integer, primary_key=True)
    fattura_id = db.Column(db.Integer, db.ForeignKey('fatture.id'), nullable=False)
    numero_riga = db.Column(db.Integer, nullable=False)
    descrizione = db.Column(db.String(500), nullable=False)
    quantita = db.Column(db.Float, nullable=False, default=1)
    prezzo_unitario = db.Column(db.Float, nullable=False)
    aliquota_iva = db.Column(db.Float, nullable=False, default=10)  # BAR/SOMMINISTRAZIONE = 10%, Altri: 4, 22
    totale_riga = db.Column(db.Float, nullable=False)

    # Relazione
    fattura = db.relationship('Fattura', backref='righe')

class Cedente(db.Model):
    """Dati del cedente/prestatore (la tua azienda) - Modificabili da interfaccia"""
    __tablename__ = 'cedente'
    id = db.Column(db.Integer, primary_key=True)

    # Dati fiscali
    partita_iva = db.Column(db.String(13), nullable=False)  # ITxxxxxxxxxxx
    codice_fiscale = db.Column(db.String(16), nullable=False)
    denominazione = db.Column(db.String(200), nullable=False)
    regime_fiscale = db.Column(db.String(10), default='RF01')  # RF01=ordinario, RF19=forfettario

    # Indirizzo
    indirizzo = db.Column(db.String(200), nullable=False)
    cap = db.Column(db.String(5), nullable=False)
    citta = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(2), nullable=False)
    nazione = db.Column(db.String(2), default='IT')

    # Contatti
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(200))

    # Timestamp
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
            # Migrazione tabella voce
            result = conn.execute(db.text("PRAGMA table_info(voce)"))
            columns = [row[1] for row in result]

            if 'destinazione_stampa' not in columns:
                logging.info("Aggiunta colonna destinazione_stampa")
                conn.execute(db.text("ALTER TABLE voce ADD COLUMN destinazione_stampa VARCHAR(20) DEFAULT 'cucina'"))
                for gruppo in CUCINA_GROUPS:
                    conn.execute(db.text("UPDATE voce SET destinazione_stampa = 'cucina' WHERE gruppo = :gruppo"), {"gruppo": gruppo})
                conn.commit()
                logging.info("✓ Migrazione voce completata")

            # Migrazione tabella fatture
            result = conn.execute(db.text("PRAGMA table_info(fatture)"))
            fatture_columns = [row[1] for row in result]

            if 'tipo_documento' not in fatture_columns:
                logging.info("Aggiunta colonna tipo_documento")
                conn.execute(db.text("ALTER TABLE fatture ADD COLUMN tipo_documento VARCHAR(10) DEFAULT 'TD01'"))
                conn.commit()
                logging.info("✓ Colonna tipo_documento aggiunta")

            if 'fattura_riferimento_id' not in fatture_columns:
                logging.info("Aggiunta colonna fattura_riferimento_id")
                conn.execute(db.text("ALTER TABLE fatture ADD COLUMN fattura_riferimento_id INTEGER"))
                conn.commit()
                logging.info("✓ Colonna fattura_riferimento_id aggiunta")

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
        
        try:
            env = os.environ.copy()
            env['PRINTER_NAME'] = printer_name
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

def enqueue_print(tavolo: str, testo: str, printer: str = 'bar'):
    logging.info(f"📝 In coda stampa {printer} - Tavolo {tavolo}")
    PRINT_QUEUE.put({'tavolo': tavolo, 'testo': testo, 'printer': printer})

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
    rows = Voce.query.order_by(Voce.gruppo, Voce.nome).all()
    return jsonify([{
        "id": x.id,
        "gruppo": x.gruppo,
        "nome": x.nome,
        "prezzo": x.prezzo,
        "destinazione_stampa": x.destinazione_stampa
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

    # Stampa cucina
    cucina_items = []
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
            
            if destinazione in ['cucina', 'entrambi']:
                cucina_items.append(line)
    
    if cucina_items:
        enqueue_print(tavolo, '\n'.join(cucina_items), 'cucina')
    
    # Stampa bar
    total = calculate_total_from_text(comanda)
    comanda_con_totale = add_total_to_order(comanda, total)
    enqueue_print(tavolo, comanda_con_totale, 'bar')

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
        
        for item in all_items:
            found_match = False
            for paid_item in paid_items:
                if (item['name'] == paid_item['name'] and 
                    item['note'] == paid_item.get('note', '') and
                    abs(item['unit_price'] - paid_item['unit_price']) < 0.01):
                    if item['quantity'] > paid_item['quantity']:
                        remaining_qty = item['quantity'] - paid_item['quantity']
                        remaining_items.append({
                            **item,
                            'quantity': remaining_qty,
                            'total_price': remaining_qty * item['unit_price']
                        })
                    found_match = True
                    break
            if not found_match:
                remaining_items.append(item)
        
        if remaining_items:
            comanda.testo = rebuild_order_text(remaining_items)
        else:
            comanda.testo = "Ordine completato - tutti gli articoli pagati"
        
        db.session.commit()
        
        if print_receipt:
            partial_bill_text = create_partial_bill_text(paid_items, comanda.tavolo)
            enqueue_print(comanda.tavolo, partial_bill_text, 'bar')
        
        logging.info(f"💳 Conto diviso ordine {oid}: €{importo_pagato:.2f}")
        
        return jsonify({
            'ok': True,
            'importo_pagato': importo_pagato,
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
    try:
        comanda = Comanda.query.get_or_404(oid)
        current_items = parse_order_text(comanda.testo)
        pagamenti = PagamentiParziali.query.filter_by(comanda_id=oid).order_by(
            PagamentiParziali.created_at.desc()
        ).all()
        payments_history = []
        total_paid = 0
        for p in pagamenti:
            payments_history.append({
                'id': p.id,
                'importo': p.importo_pagato,
                'articoli': json.loads(p.articoli_pagati),
                'created_at': p.created_at.isoformat(),
                'note': p.note
            })
            total_paid += p.importo_pagato
        current_total = sum(item['total_price'] for item in current_items)
        return jsonify({
            'id': comanda.id,
            'tavolo': comanda.tavolo,
            'testo': comanda.testo,
            'created_at': comanda.created_at.isoformat(),
            'current_items': current_items,
            'current_total': current_total,
            'payments_history': payments_history,
            'total_paid': total_paid,
            'has_payments': len(payments_history) > 0
        })
    except Exception as e:
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

# ══════════════════════════════════════════════════════════════════════════════
# API FATTURAZIONE ELETTRONICA
# ══════════════════════════════════════════════════════════════════════════════

# ────────────────────────────── CLIENTI ──────────────────────────────

@app.route("/api/clienti", methods=["GET"])
def get_clienti():
    """Ritorna lista clienti attivi con ricerca opzionale"""
    try:
        search = request.args.get('search', '').strip()

        query = Cliente.query.filter_by(attivo=1)

        if search:
            # Ricerca in ragione sociale, nome, cognome, P.IVA, CF
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Cliente.ragione_sociale.ilike(search_pattern),
                    Cliente.nome.ilike(search_pattern),
                    Cliente.cognome.ilike(search_pattern),
                    Cliente.partita_iva.ilike(search_pattern),
                    Cliente.codice_fiscale.ilike(search_pattern)
                )
            )

        clienti = query.order_by(Cliente.ragione_sociale, Cliente.cognome).all()

        result = []
        for c in clienti:
            result.append({
                'id': c.id,
                'tipo_soggetto': c.tipo_soggetto,
                'partita_iva': c.partita_iva,
                'codice_fiscale': c.codice_fiscale,
                'ragione_sociale': c.ragione_sociale,
                'nome': c.nome,
                'cognome': c.cognome,
                'indirizzo': c.indirizzo,
                'cap': c.cap,
                'citta': c.citta,
                'provincia': c.provincia,
                'nazione': c.nazione,
                'codice_destinatario': c.codice_destinatario,
                'pec': c.pec,
                'telefono': c.telefono,
                'email': c.email,
                'note': c.note,
                'display_name': c.ragione_sociale if c.ragione_sociale else f"{c.nome} {c.cognome}"
            })

        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore get_clienti: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/clienti/<int:id>", methods=["GET"])
def get_cliente(id):
    """Ritorna dettagli cliente"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({'error': 'Cliente non trovato'}), 404

        return jsonify({
            'id': cliente.id,
            'tipo_soggetto': cliente.tipo_soggetto,
            'partita_iva': cliente.partita_iva,
            'codice_fiscale': cliente.codice_fiscale,
            'ragione_sociale': cliente.ragione_sociale,
            'nome': cliente.nome,
            'cognome': cliente.cognome,
            'indirizzo': cliente.indirizzo,
            'cap': cliente.cap,
            'citta': cliente.citta,
            'provincia': cliente.provincia,
            'nazione': cliente.nazione,
            'codice_destinatario': cliente.codice_destinatario,
            'pec': cliente.pec,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'note': cliente.note
        })
    except Exception as e:
        logging.error(f"Errore get_cliente: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/clienti", methods=["POST"])
def create_cliente():
    """Crea nuovo cliente"""
    try:
        from backend.fatture.fattura_elettronica import valida_codice_fiscale, valida_codice_sdi

        d = request.get_json(force=True)

        # Validazioni
        if not d.get('codice_fiscale'):
            return jsonify({'error': 'Codice fiscale obbligatorio'}), 400

        if not valida_codice_fiscale(d['codice_fiscale']):
            return jsonify({'error': 'Codice fiscale non valido'}), 400

        if d.get('codice_destinatario') and not valida_codice_sdi(d['codice_destinatario']):
            return jsonify({'error': 'Codice SDI deve essere 7 caratteri'}), 400

        # Crea cliente
        cliente = Cliente(
            tipo_soggetto=d.get('tipo_soggetto', 'azienda'),
            partita_iva=d.get('partita_iva', '').strip(),
            codice_fiscale=d['codice_fiscale'].strip().upper(),
            ragione_sociale=d.get('ragione_sociale', '').strip(),
            nome=d.get('nome', '').strip(),
            cognome=d.get('cognome', '').strip(),
            indirizzo=d.get('indirizzo', '').strip(),
            cap=d.get('cap', '').strip(),
            citta=d.get('citta', '').strip(),
            provincia=d.get('provincia', '').strip().upper(),
            nazione=d.get('nazione', 'IT').upper(),
            codice_destinatario=d.get('codice_destinatario', '0000000').strip(),
            pec=d.get('pec', '').strip(),
            telefono=d.get('telefono', '').strip(),
            email=d.get('email', '').strip(),
            note=d.get('note', '').strip(),
            attivo=1
        )

        db.session.add(cliente)
        db.session.commit()

        return jsonify({'ok': True, 'id': cliente.id})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore create_cliente: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/clienti/<int:id>", methods=["PUT"])
def update_cliente(id):
    """Aggiorna cliente esistente"""
    try:
        from backend.fatture.fattura_elettronica import valida_codice_fiscale, valida_codice_sdi

        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({'error': 'Cliente non trovato'}), 404

        d = request.get_json(force=True)

        # Validazioni
        if d.get('codice_fiscale') and not valida_codice_fiscale(d['codice_fiscale']):
            return jsonify({'error': 'Codice fiscale non valido'}), 400

        if d.get('codice_destinatario') and not valida_codice_sdi(d['codice_destinatario']):
            return jsonify({'error': 'Codice SDI deve essere 7 caratteri'}), 400

        # Aggiorna campi
        if 'tipo_soggetto' in d:
            cliente.tipo_soggetto = d['tipo_soggetto']
        if 'partita_iva' in d:
            cliente.partita_iva = d['partita_iva'].strip()
        if 'codice_fiscale' in d:
            cliente.codice_fiscale = d['codice_fiscale'].strip().upper()
        if 'ragione_sociale' in d:
            cliente.ragione_sociale = d['ragione_sociale'].strip()
        if 'nome' in d:
            cliente.nome = d['nome'].strip()
        if 'cognome' in d:
            cliente.cognome = d['cognome'].strip()
        if 'indirizzo' in d:
            cliente.indirizzo = d['indirizzo'].strip()
        if 'cap' in d:
            cliente.cap = d['cap'].strip()
        if 'citta' in d:
            cliente.citta = d['citta'].strip()
        if 'provincia' in d:
            cliente.provincia = d['provincia'].strip().upper()
        if 'nazione' in d:
            cliente.nazione = d['nazione'].upper()
        if 'codice_destinatario' in d:
            cliente.codice_destinatario = d['codice_destinatario'].strip()
        if 'pec' in d:
            cliente.pec = d['pec'].strip()
        if 'telefono' in d:
            cliente.telefono = d['telefono'].strip()
        if 'email' in d:
            cliente.email = d['email'].strip()
        if 'note' in d:
            cliente.note = d['note'].strip()

        cliente.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore update_cliente: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/clienti/<int:id>", methods=["DELETE"])
def delete_cliente(id):
    """Disattiva cliente (soft delete)"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({'error': 'Cliente non trovato'}), 404

        cliente.attivo = 0
        cliente.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore delete_cliente: {e}")
        return jsonify({'error': str(e)}), 500

# ────────────────────────────── FATTURE ──────────────────────────────

@app.route("/api/fatture", methods=["GET"])
def get_fatture():
    """Ritorna lista fatture con filtri opzionali"""
    try:
        anno = request.args.get('anno', datetime.now().year, type=int)
        stato = request.args.get('stato', '')

        query = Fattura.query.filter_by(anno=anno)

        if stato:
            query = query.filter_by(stato=stato)

        fatture = query.order_by(Fattura.numero.desc()).all()

        result = []
        for f in fatture:
            result.append({
                'id': f.id,
                'numero': f.numero,
                'anno': f.anno,
                'numero_completo': f"{f.anno}/{f.numero}",
                'data_emissione': f.data_emissione.strftime('%Y-%m-%d'),
                'cliente_id': f.cliente_id,
                'cliente_nome': f.cliente.ragione_sociale if f.cliente.ragione_sociale else f"{f.cliente.nome} {f.cliente.cognome}",
                'imponibile': f.imponibile,
                'iva': f.iva,
                'totale': f.totale,
                'stato': f.stato,
                'percorso_xml': f.percorso_xml,
                'created_at': f.created_at.strftime('%Y-%m-%d %H:%M')
            })

        return jsonify(result)
    except Exception as e:
        logging.error(f"Errore get_fatture: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/<int:id>", methods=["GET"])
def get_fattura(id):
    """Ritorna dettagli fattura con righe"""
    try:
        fattura = Fattura.query.get(id)
        if not fattura:
            return jsonify({'error': 'Fattura non trovata'}), 404

        righe = []
        for r in fattura.righe:
            righe.append({
                'id': r.id,
                'numero_riga': r.numero_riga,
                'descrizione': r.descrizione,
                'quantita': r.quantita,
                'prezzo_unitario': r.prezzo_unitario,
                'aliquota_iva': r.aliquota_iva,
                'totale_riga': r.totale_riga
            })

        return jsonify({
            'id': fattura.id,
            'numero': fattura.numero,
            'anno': fattura.anno,
            'numero_completo': f"{fattura.anno}/{fattura.numero}",
            'data_emissione': fattura.data_emissione.strftime('%Y-%m-%d'),
            'cliente_id': fattura.cliente_id,
            'cliente': {
                'id': fattura.cliente.id,
                'ragione_sociale': fattura.cliente.ragione_sociale,
                'nome': fattura.cliente.nome,
                'cognome': fattura.cliente.cognome,
                'partita_iva': fattura.cliente.partita_iva,
                'codice_fiscale': fattura.cliente.codice_fiscale,
                'indirizzo': fattura.cliente.indirizzo,
                'cap': fattura.cliente.cap,
                'citta': fattura.cliente.citta,
                'provincia': fattura.cliente.provincia
            },
            'imponibile': fattura.imponibile,
            'iva': fattura.iva,
            'totale': fattura.totale,
            'stato': fattura.stato,
            'righe': righe,
            'note': fattura.note
        })
    except Exception as e:
        logging.error(f"Errore get_fattura: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/da-ordine", methods=["POST"])
def create_fattura_da_ordine():
    """Crea fattura da ordine/comanda esistente"""
    try:
        from backend.fatture.fattura_elettronica import FatturaElettronicaXML

        d = request.get_json(force=True)

        comanda_id = d.get('comanda_id')
        cliente_id = d.get('cliente_id')
        items = d.get('items', [])  # Lista articoli dall'ordine

        if not cliente_id:
            return jsonify({'error': 'Cliente obbligatorio'}), 400

        # Verifica cliente esista
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({'error': 'Cliente non trovato'}), 404

        # Calcola prossimo numero fattura per l'anno corrente
        anno_corrente = datetime.now().year
        ultima_fattura = Fattura.query.filter_by(anno=anno_corrente).order_by(Fattura.numero.desc()).first()
        prossimo_numero = (ultima_fattura.numero + 1) if ultima_fattura else 1

        # Calcola totali
        imponibile = 0
        iva_totale = 0
        totale = 0

        righe_fattura = []
        for idx, item in enumerate(items, start=1):
            qty = item.get('qty', 1)
            prezzo_unit = item.get('prezzo', 0)  # PREZZO IVA INCLUSA
            aliquota = item.get('aliquota_iva', 10)  # BAR/SOMMINISTRAZIONE = 10%

            # SCORPORO IVA (prezzi sono già IVA inclusa)
            totale_riga_lordo = qty * prezzo_unit
            imponibile_riga = totale_riga_lordo / (1 + aliquota / 100)
            iva_riga = totale_riga_lordo - imponibile_riga

            imponibile += imponibile_riga
            iva_totale += iva_riga

            righe_fattura.append({
                'numero_riga': idx,
                'descrizione': item.get('nome', ''),
                'quantita': qty,
                'prezzo_unitario': imponibile_riga / qty,  # Prezzo SCORPORATO IVA (per coerenza con PUT)
                'aliquota_iva': aliquota,
                'totale_riga': totale_riga_lordo  # Totale IVA inclusa
            })

        totale = imponibile + iva_totale

        # Crea fattura
        fattura = Fattura(
            numero=prossimo_numero,
            anno=anno_corrente,
            data_emissione=datetime.now().date(),
            cliente_id=cliente_id,
            comanda_id=comanda_id,
            imponibile=round(imponibile, 2),
            iva=round(iva_totale, 2),
            totale=round(totale, 2),
            stato='bozza'
        )

        db.session.add(fattura)
        db.session.flush()  # Per ottenere l'ID

        # Crea righe fattura
        for riga_data in righe_fattura:
            riga = RigaFattura(
                fattura_id=fattura.id,
                numero_riga=riga_data['numero_riga'],
                descrizione=riga_data['descrizione'],
                quantita=riga_data['quantita'],
                prezzo_unitario=riga_data['prezzo_unitario'],
                aliquota_iva=riga_data['aliquota_iva'],
                totale_riga=riga_data['totale_riga']
            )
            db.session.add(riga)

        db.session.commit()

        return jsonify({
            'ok': True,
            'id': fattura.id,
            'numero_completo': f"{fattura.anno}/{fattura.numero}"
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore create_fattura_da_ordine: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/<int:id>/nota-credito", methods=["POST"])
def create_nota_credito(id):
    """Crea una Nota di Credito per annullare una fattura emessa"""
    try:
        # Recupera fattura originale
        fattura_originale = Fattura.query.get(id)
        if not fattura_originale:
            return jsonify({'error': 'Fattura non trovata'}), 404

        if fattura_originale.stato == 'bozza':
            return jsonify({'error': 'La fattura in bozza può essere modificata direttamente o eliminata'}), 400

        if fattura_originale.tipo_documento == 'TD04':
            return jsonify({'error': 'Non si può creare una nota di credito da un\'altra nota di credito'}), 400

        # Verifica se esiste già una nota di credito per questa fattura
        nota_esistente = Fattura.query.filter_by(
            fattura_riferimento_id=id,
            tipo_documento='TD04'
        ).first()

        if nota_esistente:
            return jsonify({'error': f'Esiste già una Nota di Credito n. {nota_esistente.numero}/{nota_esistente.anno}'}), 400

        # Calcola prossimo numero per l'anno corrente
        anno_corrente = datetime.now().year
        ultima_fattura = Fattura.query.filter_by(anno=anno_corrente).order_by(Fattura.numero.desc()).first()
        prossimo_numero = (ultima_fattura.numero + 1) if ultima_fattura else 1

        # Crea Nota di Credito
        nota_credito = Fattura(
            numero=prossimo_numero,
            anno=anno_corrente,
            data_emissione=datetime.now().date(),
            cliente_id=fattura_originale.cliente_id,
            imponibile=fattura_originale.imponibile,
            iva=fattura_originale.iva,
            totale=fattura_originale.totale,
            stato='bozza',
            tipo_documento='TD04',
            fattura_riferimento_id=fattura_originale.id,
            note=f"Nota di Credito per annullo fattura n. {fattura_originale.numero}/{fattura_originale.anno}"
        )

        db.session.add(nota_credito)
        db.session.flush()

        # Copia righe dalla fattura originale
        righe_originali = RigaFattura.query.filter_by(fattura_id=fattura_originale.id).all()
        for riga_orig in righe_originali:
            riga_nc = RigaFattura(
                fattura_id=nota_credito.id,
                numero_riga=riga_orig.numero_riga,
                descrizione=riga_orig.descrizione,
                quantita=riga_orig.quantita,
                prezzo_unitario=riga_orig.prezzo_unitario,
                aliquota_iva=riga_orig.aliquota_iva,
                totale_riga=riga_orig.totale_riga
            )
            db.session.add(riga_nc)

        db.session.commit()

        return jsonify({
            'ok': True,
            'id': nota_credito.id,
            'numero_completo': f"{nota_credito.numero}/{nota_credito.anno}",
            'tipo': 'TD04'
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore create_nota_credito: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def genera_testo_fattura(fattura):
    """Genera il testo COMPLETO della fattura per la stampa (font piccoli gestiti da print_job.py)"""
    try:
        # Leggi dati cedente dal database (o fallback a config)
        cedente = Cedente.query.first()
        if not cedente:
            # Fallback a config_cedente.py se non ancora migrato
            from backend.fatture.config_cedente import DATI_CEDENTE
            dati_cedente = DATI_CEDENTE
        else:
            dati_cedente = {
                'denominazione': cedente.denominazione,
                'partita_iva': cedente.partita_iva,
                'indirizzo': cedente.indirizzo,
                'cap': cedente.cap,
                'citta': cedente.citta,
                'provincia': cedente.provincia
            }

        # Nome cliente
        if fattura.cliente.ragione_sociale:
            nome_cliente = fattura.cliente.ragione_sociale
        else:
            nome_cliente = f"{fattura.cliente.nome} {fattura.cliente.cognome}"

        # Costruisci testo fattura COMPLETO (font piccoli applicati da stampante)
        testo = []
        testo.append("=" * 32)
        testo.append("FATTURA ELETTRONICA")
        testo.append(f"N. {fattura.anno}/{fattura.numero}")
        testo.append(f"Data: {fattura.data_emissione.strftime('%d/%m/%Y')}")
        testo.append("=" * 32)
        testo.append("")
        testo.append("CEDENTE / PRESTATORE:")
        testo.append(dati_cedente['denominazione'])
        testo.append(f"P.IVA: {dati_cedente['partita_iva']}")
        testo.append(f"{dati_cedente['indirizzo']}")
        testo.append(f"{dati_cedente['cap']} {dati_cedente['citta']} ({dati_cedente['provincia']})")
        testo.append("")
        testo.append("CLIENTE:")
        testo.append(nome_cliente)
        if fattura.cliente.partita_iva:
            testo.append(f"P.IVA: {fattura.cliente.partita_iva}")
        testo.append(f"CF: {fattura.cliente.codice_fiscale}")
        testo.append(f"{fattura.cliente.indirizzo}")
        testo.append(f"{fattura.cliente.cap} {fattura.cliente.citta} ({fattura.cliente.provincia})")
        testo.append("")
        testo.append("=" * 32)
        testo.append("DETTAGLIO ARTICOLI:")
        testo.append("=" * 32)

        # Righe fattura con TUTTI i dettagli
        for riga in fattura.righe:
            testo.append("")
            testo.append(f"{riga.quantita:.0f}x {riga.descrizione}")
            # Mostra prezzo IVA INCLUSA (quello che il cliente conosce)
            prezzo_ivato = riga.totale_riga / riga.quantita
            testo.append(f"  Prezzo unit: €{prezzo_ivato:.2f}")
            testo.append(f"  Totale: €{riga.totale_riga:.2f}")
            testo.append(f"  IVA: {riga.aliquota_iva:.0f}%")

        testo.append("")
        testo.append("=" * 32)
        testo.append("TOTALI:")
        testo.append(f"Imponibile: €{fattura.imponibile:.2f}")
        testo.append(f"IVA:        €{fattura.iva:.2f}")
        testo.append(f"TOTALE:     €{fattura.totale:.2f}")
        testo.append("=" * 32)
        testo.append("")
        testo.append("Documento fiscale valido ai fini IVA")
        testo.append("File XML generato per invio SDI")
        testo.append("")

        return "\n".join(testo)

    except Exception as e:
        logging.error(f"Errore genera_testo_fattura: {e}")
        return f"FATTURA {fattura.anno}/{fattura.numero}\nTOTALE: €{fattura.totale:.2f}\n(Errore generazione dettaglio)"

@app.route("/api/fatture/<int:id>/emetti", methods=["POST"])
def emetti_fattura(id):
    """Emette la fattura generando il file XML"""
    try:
        from backend.fatture.fattura_elettronica import FatturaElettronicaXML

        fattura = Fattura.query.get(id)
        if not fattura:
            return jsonify({'error': 'Fattura non trovata'}), 404

        if fattura.stato not in ['bozza', 'errore']:
            return jsonify({'error': 'Fattura già emessa'}), 400

        # Prepara dati per XML
        dati_fattura = {
            'numero': fattura.numero,
            'anno': fattura.anno,
            'data_emissione': fattura.data_emissione,
            'totale': fattura.totale,
            'tipo_documento': fattura.tipo_documento
        }

        # Se è una Nota di Credito, aggiungi riferimento fattura originale
        if fattura.tipo_documento == 'TD04' and fattura.fattura_riferimento_id:
            fatt_rif = Fattura.query.get(fattura.fattura_riferimento_id)
            if fatt_rif:
                dati_fattura['fattura_riferimento'] = {
                    'numero': fatt_rif.numero,
                    'anno': fatt_rif.anno,
                    'data_emissione': fatt_rif.data_emissione
                }

        dati_cliente = {
            'partita_iva': fattura.cliente.partita_iva,
            'codice_fiscale': fattura.cliente.codice_fiscale,
            'ragione_sociale': fattura.cliente.ragione_sociale,
            'nome': fattura.cliente.nome,
            'cognome': fattura.cliente.cognome,
            'indirizzo': fattura.cliente.indirizzo,
            'cap': fattura.cliente.cap,
            'citta': fattura.cliente.citta,
            'provincia': fattura.cliente.provincia,
            'nazione': fattura.cliente.nazione,
            'codice_destinatario': fattura.cliente.codice_destinatario,
            'pec': fattura.cliente.pec
        }

        righe_xml = []
        for r in fattura.righe:
            righe_xml.append({
                'descrizione': r.descrizione,
                'quantita': r.quantita,
                'prezzo_unitario': r.prezzo_unitario,
                'aliquota_iva': r.aliquota_iva,
                'totale_riga': r.totale_riga
            })

        # Genera XML con dati cedente dal database
        cedente = Cedente.query.first()
        if cedente:
            dati_cedente_dict = {
                'partita_iva': cedente.partita_iva,
                'codice_fiscale': cedente.codice_fiscale,
                'denominazione': cedente.denominazione,
                'regime_fiscale': cedente.regime_fiscale,
                'indirizzo': cedente.indirizzo,
                'cap': cedente.cap,
                'citta': cedente.citta,
                'provincia': cedente.provincia,
                'nazione': cedente.nazione,
                'telefono': cedente.telefono,
                'email': cedente.email
            }
            generatore = FatturaElettronicaXML(dati_cedente=dati_cedente_dict)
        else:
            generatore = FatturaElettronicaXML()  # Usa config_cedente.py come fallback

        percorso_xml = generatore.genera_xml(dati_fattura, dati_cliente, righe_xml)

        # Aggiorna fattura
        fattura.percorso_xml = percorso_xml
        fattura.stato = 'emessa'
        fattura.updated_at = datetime.utcnow()
        db.session.commit()

        # Stampa fattura automaticamente
        try:
            testo_fattura = genera_testo_fattura(fattura)
            enqueue_print(f"FATT-{fattura.numero}", testo_fattura, 'bar')
            logging.info(f"📄 Fattura {fattura.anno}/{fattura.numero} inviata alla stampante")
        except Exception as print_err:
            logging.error(f"⚠️ Errore stampa fattura: {print_err}")

        return jsonify({
            'ok': True,
            'percorso_xml': percorso_xml,
            'numero_completo': f"{fattura.anno}/{fattura.numero}"
        })
    except Exception as e:
        db.session.rollback()
        fattura.stato = 'errore'
        fattura.note = str(e)
        db.session.commit()
        logging.error(f"Errore emetti_fattura: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/<int:id>/xml", methods=["GET"])
def download_xml_fattura(id):
    """Download file XML fattura"""
    try:
        fattura = Fattura.query.get(id)
        if not fattura:
            return jsonify({'error': 'Fattura non trovata'}), 404

        if not fattura.percorso_xml or not os.path.exists(fattura.percorso_xml):
            return jsonify({'error': 'File XML non trovato'}), 404

        directory = os.path.dirname(fattura.percorso_xml)
        filename = os.path.basename(fattura.percorso_xml)

        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Errore download_xml_fattura: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/download-periodo", methods=["POST"])
def download_xml_periodo():
    """Download ZIP con tutti gli XML fatture in un periodo"""
    try:
        import zipfile
        import tempfile

        data = request.json
        data_da_str = data.get('data_da')
        data_a_str = data.get('data_a')

        if not data_da_str or not data_a_str:
            return jsonify({'error': 'Specificare data_da e data_a'}), 400

        # Converti stringhe in date
        data_da = datetime.strptime(data_da_str, '%Y-%m-%d').date()
        data_a = datetime.strptime(data_a_str, '%Y-%m-%d').date()

        # Recupera fatture emesse nel periodo
        fatture = Fattura.query.filter(
            Fattura.stato == 'emessa',
            Fattura.data_emissione >= data_da,
            Fattura.data_emissione <= data_a,
            Fattura.percorso_xml.isnot(None)
        ).all()

        if not fatture:
            return jsonify({'error': 'Nessuna fattura emessa nel periodo specificato'}), 404

        # Crea file ZIP temporaneo
        temp_zip = tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False)
        zip_path = temp_zip.name
        temp_zip.close()

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fattura in fatture:
                if fattura.percorso_xml and os.path.exists(fattura.percorso_xml):
                    # Nome file nel ZIP: IT01234567890_00001.xml
                    filename = os.path.basename(fattura.percorso_xml)
                    zipf.write(fattura.percorso_xml, arcname=filename)

        # Nome del file ZIP da scaricare
        zip_filename = f"fatture_{data_da_str}_{data_a_str}.zip"

        # Invia il file
        return send_from_directory(
            os.path.dirname(zip_path),
            os.path.basename(zip_path),
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        logging.error(f"Errore download_xml_periodo: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/<int:id>", methods=["DELETE"])
def delete_fattura(id):
    """Elimina fattura (solo se in bozza)"""
    try:
        fattura = Fattura.query.get(id)
        if not fattura:
            return jsonify({'error': 'Fattura non trovata'}), 404

        if fattura.stato not in ['bozza', 'errore']:
            return jsonify({'error': 'Impossibile eliminare fattura emessa'}), 400

        # Elimina righe
        RigaFattura.query.filter_by(fattura_id=id).delete()

        # Elimina fattura
        db.session.delete(fattura)
        db.session.commit()

        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore delete_fattura: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/<int:id>", methods=["PUT"])
def update_fattura(id):
    """Modifica fattura (solo se in bozza)"""
    try:
        fattura = Fattura.query.get(id)
        if not fattura:
            return jsonify({'error': 'Fattura non trovata'}), 404

        if fattura.stato not in ['bozza', 'errore']:
            return jsonify({'error': 'Impossibile modificare fattura già emessa. Crea una Nota di Credito.'}), 400

        data = request.json

        # Aggiorna dati fattura
        if 'cliente_id' in data:
            fattura.cliente_id = data['cliente_id']
        if 'data_emissione' in data:
            fattura.data_emissione = datetime.strptime(data['data_emissione'], '%Y-%m-%d').date()
        if 'note' in data:
            fattura.note = data['note']

        # Aggiorna righe se fornite
        if 'items' in data:
            # Elimina vecchie righe
            RigaFattura.query.filter_by(fattura_id=id).delete()

            # Aggiungi nuove righe
            totale_imponibile = 0
            totale_iva = 0

            for idx, item in enumerate(data['items'], 1):
                prezzo_unitario = float(item['prezzo'])
                quantita = float(item.get('qty', 1))
                aliquota_iva = float(item.get('aliquota_iva', 10))  # BAR/SOMMINISTRAZIONE = 10%

                # Calcola imponibile e IVA
                totale_riga_lordo = prezzo_unitario * quantita
                imponibile_riga = totale_riga_lordo / (1 + aliquota_iva / 100)
                iva_riga = totale_riga_lordo - imponibile_riga

                totale_imponibile += imponibile_riga
                totale_iva += iva_riga

                riga = RigaFattura(
                    fattura_id=fattura.id,
                    numero_riga=idx,
                    descrizione=item['nome'],
                    quantita=quantita,
                    prezzo_unitario=imponibile_riga / quantita,
                    aliquota_iva=aliquota_iva,
                    totale_riga=totale_riga_lordo
                )
                db.session.add(riga)

            # Aggiorna totali fattura
            fattura.imponibile = round(totale_imponibile, 2)
            fattura.iva = round(totale_iva, 2)
            fattura.totale = round(totale_imponibile + totale_iva, 2)

        fattura.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'ok': True,
            'id': fattura.id,
            'numero_completo': f"{fattura.numero}/{fattura.anno}"
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore update_fattura: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route("/api/fatture/config", methods=["GET"])
def get_config_fatture():
    """Ritorna configurazione cedente per il frontend (LEGACY - usa /api/cedente)"""
    try:
        # Leggi dal database
        cedente = Cedente.query.first()
        if cedente:
            return jsonify({
                'partita_iva': cedente.partita_iva,
                'codice_fiscale': cedente.codice_fiscale,
                'denominazione': cedente.denominazione,
                'regime_fiscale': cedente.regime_fiscale,
                'indirizzo': cedente.indirizzo,
                'cap': cedente.cap,
                'citta': cedente.citta,
                'provincia': cedente.provincia,
                'nazione': cedente.nazione,
                'telefono': cedente.telefono,
                'email': cedente.email
            })
        else:
            # Fallback a config_cedente.py se non ancora migrato
            from backend.fatture.fattura_elettronica import FatturaElettronicaXML
            gen = FatturaElettronicaXML()
            return jsonify(gen.CEDENTE)
    except Exception as e:
        logging.error(f"Errore get_config_fatture: {e}")
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# API CEDENTE (DATI SOCIETÀ)
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/cedente", methods=["GET"])
def get_cedente():
    """Recupera i dati del cedente (tua società)"""
    try:
        cedente = Cedente.query.first()

        # Se non esiste, inizializza da config_cedente.py
        if not cedente:
            from backend.fatture.config_cedente import DATI_CEDENTE
            cedente = Cedente(
                partita_iva=DATI_CEDENTE['partita_iva'],
                codice_fiscale=DATI_CEDENTE['codice_fiscale'],
                denominazione=DATI_CEDENTE['denominazione'],
                regime_fiscale=DATI_CEDENTE['regime_fiscale'],
                indirizzo=DATI_CEDENTE['indirizzo'],
                cap=DATI_CEDENTE['cap'],
                citta=DATI_CEDENTE['citta'],
                provincia=DATI_CEDENTE['provincia'],
                nazione=DATI_CEDENTE.get('nazione', 'IT'),
                telefono=DATI_CEDENTE.get('telefono'),
                email=DATI_CEDENTE.get('email')
            )
            db.session.add(cedente)
            db.session.commit()

        return jsonify({
            'id': cedente.id,
            'partita_iva': cedente.partita_iva,
            'codice_fiscale': cedente.codice_fiscale,
            'denominazione': cedente.denominazione,
            'regime_fiscale': cedente.regime_fiscale,
            'indirizzo': cedente.indirizzo,
            'cap': cedente.cap,
            'citta': cedente.citta,
            'provincia': cedente.provincia,
            'nazione': cedente.nazione,
            'telefono': cedente.telefono,
            'email': cedente.email
        })
    except Exception as e:
        logging.error(f"Errore get_cedente: {e}")
        return jsonify({'error': str(e)}), 500

@app.route("/api/cedente", methods=["PUT"])
def update_cedente():
    """Aggiorna i dati del cedente (tua società)"""
    try:
        data = request.json
        cedente = Cedente.query.first()

        if not cedente:
            return jsonify({'error': 'Cedente non trovato. Accedi prima alla pagina per inizializzarlo.'}), 404

        # Aggiorna campi
        cedente.partita_iva = data.get('partita_iva', cedente.partita_iva)
        cedente.codice_fiscale = data.get('codice_fiscale', cedente.codice_fiscale)
        cedente.denominazione = data.get('denominazione', cedente.denominazione)
        cedente.regime_fiscale = data.get('regime_fiscale', cedente.regime_fiscale)
        cedente.indirizzo = data.get('indirizzo', cedente.indirizzo)
        cedente.cap = data.get('cap', cedente.cap)
        cedente.citta = data.get('citta', cedente.citta)
        cedente.provincia = data.get('provincia', cedente.provincia)
        cedente.nazione = data.get('nazione', cedente.nazione)
        cedente.telefono = data.get('telefono', cedente.telefono)
        cedente.email = data.get('email', cedente.email)
        cedente.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': 'Dati società aggiornati con successo',
            'cedente': {
                'id': cedente.id,
                'partita_iva': cedente.partita_iva,
                'codice_fiscale': cedente.codice_fiscale,
                'denominazione': cedente.denominazione,
                'regime_fiscale': cedente.regime_fiscale,
                'indirizzo': cedente.indirizzo,
                'cap': cedente.cap,
                'citta': cedente.citta,
                'provincia': cedente.provincia,
                'nazione': cedente.nazione,
                'telefono': cedente.telefono,
                'email': cedente.email
            }
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Errore update_cedente: {e}")
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

@app.route("/gestione_fatture.html")
def fatture_html():
    return send_from_directory(app.static_folder, "gestione_fatture.html")

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
    logging.info("🌅 SUNSET BAR - Server in ascolto")
    logging.info(f"🌐 URL: http://0.0.0.0:5123")
    logging.info(f"💾 Database: {DB_FILE}")
    logging.info("="*60)
    
    app.run(host="0.0.0.0", port=5123, threaded=True, debug=False)
