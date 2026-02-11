#!/usr/bin/env python3
import sys
import os
import io
import textwrap
import logging
import traceback
from datetime import datetime
from escpos.printer import Network
from PIL import Image, ImageDraw, ImageFont

# ─────────── CONFIGURAZIONE ───────────
# Percorso base
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Crea directory logs se non esiste
os.makedirs(LOG_DIR, exist_ok=True)

# Leggi da environment o usa default
PRINTER_NAME = os.environ.get('PRINTER_NAME', 'bancone')

# Configurazione stampanti - IP CORRETTI PER RETE 0.x
if PRINTER_NAME == 'cucina':
    PRINTER_IP = "192.168.0.10"
else:  # bancone
    PRINTER_IP = "192.168.0.11"

PRINTER_PORT = 9100
MAX_WIDTH = 512
TITLE_PTS = 90
BODY_PTS = 48

# Font piccoli per fatture
FATTURA_TITLE_PTS = 32
FATTURA_BODY_PTS = 20

# Lista font possibili
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/arial.ttf"
]

# Setup logging
LOG_FILE = os.path.join(LOG_DIR, 'print_job.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

def find_font(pts):
    """Trova il primo font disponibile"""
    for font_path in FONT_PATHS:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, pts)
                logging.info(f"Font trovato: {font_path}")
                return font
        except Exception as e:
            logging.debug(f"Font {font_path} non funziona: {e}")
            continue
    
    # Fallback al font di default
    logging.warning("Nessun font trovato, uso default")
    return ImageFont.load_default()

def _make_img(text: str, pts: int) -> Image.Image:
    """Crea immagine del testo"""
    try:
        font = find_font(pts)
        
        # METODO MIGLIORATO - calcola dimensioni
        # Crea immagine temporanea per misurare
        temp_img = Image.new("L", (1, 1), 255)
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        # Aggiungi padding
        padding = 20
        img_width = w + padding
        img_height = h + padding
        
        # Crea immagine finale
        img = Image.new("L", (img_width, img_height), 255)  # Bianco
        draw = ImageDraw.Draw(img)
        
        # Centra il testo
        x = padding // 2
        y = padding // 2
        draw.text((x, y), text, font=font, fill=0)  # Nero
        
        # Ridimensiona se troppo larga
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
        
        logging.info(f"Immagine creata: {img.width}x{img.height} per '{text}'")
        return img
        
    except Exception as e:
        logging.error(f"Errore creazione immagine per '{text}': {e}")
        # Fallback: crea immagine con testo semplice
        img = Image.new("L", (300, 100), 255)
        draw = ImageDraw.Draw(img)
        draw.text((10, 30), text, fill=0)
        return img

def categorizza_items(testo):
    """Separa bevande da piatti in base al contenuto - VERSIONE CORRETTA"""
    
    # Parole chiave per identificare le bevande
    BEVANDE_KEYWORDS = [
        'caffè', 'caffe', 'espresso', 'cappuccino', 'macchiato', 'latte',
        'tè', 'te', 'tisana', 'cioccolata', 'coca', 'pepsi', 'aranciata',
        'acqua', 'birra', 'vino', 'prosecco', 'aperitivo', 'spritz',
        'negroni', 'mojito', 'cocktail', 'drink', 'succo', 'spremuta',
        'gassosa', 'limonata', 'chinotto', 'bitter', 'amaro', 'grappa',
        'limoncello', 'digestivo', 'cordiale', 'sciroppo', 'frappè',
        'frullato', 'centrifuga', 'smoothie', 'milkshake', 'amari',
        'poli', 'frusta', 'classica', 'pregiata', 'pregiati'
    ]
    
    # ✅ PAROLE CHIAVE CUCINA - VERSIONE COMPLETA E CORRETTA
    CUCINA_KEYWORDS = [
        # Paste e primi
        'pasta', 'risotto', 'pizza', 'lasagne', 'gnocchi', 'ravioli',
        'spaghetti', 'penne', 'fusilli', 'tagliatelle', 'carbonara',
        'amatriciana', 'cacio', 'pepe', 'pomodoro', 'pesto', 'ragù',
        
        # Carni e secondi
        'bistecca', 'scaloppina', 'cotoletta', 'pollo', 'maiale',
        'pesce', 'branzino', 'orata', 'salmone', 'baccalà', 'fritto',
        'grigliata', 'arrosto', 'brasato', 'spezzatino',
        
        # Zuppe e contorni
        'minestra', 'zuppa', 'vellutata', 'contorno', 'verdure', 
        'patate', 'insalata', 'primo', 'secondo', 'antipasto', 'piatto',
        
        # ✅ HAMBURGER E BURGER - ERANO MANCANTI!
        'hamburger', 'burger', 'cheeseburger', 'big', 'boston', 
        'classic', 'pork',
        
        # ✅ TOAST - ERANO MANCANTI!
        'toast', 'classico', 'onto', 'parma', 'trentino',
        
        # ✅ BRUSCHETTE - ERANO MANCANTI!
        'bruschetta', 'bruschette',
        
        # ✅ PANINI - ERANO MANCANTI!
        'panino', 'panini', 'pane morbido', 'morbido',
        
        # ✅ PIADINE - ERANO MANCANTI!
        'piadina', 'piadine', 'artigianali', 'artigianale',
        'mediterraneo', 'romagnola', 'tirolese',
        
        # ✅ BRIOCHES E PRODOTTI DA FORNO - ERANO MANCANTI!
        'brioche', 'croissant', 'cornetto', 'vuota', 'nutella',
        'marmellata', 'crema', 'cioccolato', 'integrale',
        
        # Altri prodotti caldi
        'hot dog', 'club sandwich', 'sandwich', 'wrap',
        'focaccia', 'calzone', 'supplì'
    ]
    
    linee = testo.strip().split('\n')
    bevande = []
    cucina = []
    altro = []
    
    for linea in linee:
        if not linea.strip():
            continue
            
        linea_lower = linea.lower()
        
        # Controlla se è una bevanda
        is_bevanda = any(keyword in linea_lower for keyword in BEVANDE_KEYWORDS)
        # Controlla se è un piatto da cucina
        is_cucina = any(keyword in linea_lower for keyword in CUCINA_KEYWORDS)
        
        if is_bevanda and not is_cucina:
            bevande.append(linea)
        elif is_cucina and not is_bevanda:
            cucina.append(linea)
        else:
            # Se non è chiaro o contiene entrambi, metti in "altro"
            altro.append(linea)
    
    return bevande, cucina, altro

def stampa_sezione(p, titolo, items, tavolo, show_footer=True):
    """Stampa una sezione specifica (bevande o cucina)"""
    if not items:
        return
    
    logging.info(f"Stampo sezione: {titolo}")
    
    # Titolo sezione
    title_text = f"TAVOLO {tavolo}\n{titolo}"
    img = _make_img(title_text, TITLE_PTS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    p.image(buf)
    p.text("\n")
    
    # Data e ora
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    img = _make_img(timestamp, BODY_PTS // 2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    p.image(buf)
    p.text("\n\n")
    
    # Items
    for item in items:
        for part in textwrap.wrap(item, 32) or [""]:
            img = _make_img(part, BODY_PTS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            p.image(buf)
        p.text("\n")
    
    # Footer solo se richiesto (per bancone)
    if show_footer:
        p.text("\n" + "-" * 48 + "\n")
        img = _make_img("scontrino non fiscale", 24)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        p.image(buf)
        p.text("\n")
        
        img = _make_img("ritiro scontrino fiscale in cassa", 24)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        p.image(buf)
        p.text("\n")

def raw_print(tavolo: str, testo: str) -> bool:
    try:
        logging.info(f"=== INIZIO STAMPA ===")
        logging.info(f"Stampante: {PRINTER_NAME}")
        logging.info(f"Connessione: {PRINTER_IP}:{PRINTER_PORT}")
        logging.info(f"Tavolo: {tavolo}")

        # Rileva se è una fattura
        is_fattura = "FATT" in testo[:50] or "FATTURA" in testo[:50]

        if is_fattura:
            # STAMPA FATTURA CON FONT PICCOLI
            logging.info("🧾 Rilevata FATTURA - uso font piccoli")
            p = Network(PRINTER_IP, PRINTER_PORT, timeout=10)
            p.hw('init')

            for line in testo.splitlines():
                if line.strip():
                    # Usa font piccoli per fatture
                    if "FATT" in line or "===" in line:
                        img = _make_img(line, FATTURA_TITLE_PTS)
                    else:
                        img = _make_img(line, FATTURA_BODY_PTS)

                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    p.image(buf)
                else:
                    p.text("\n")

            p.text("\n\n\n")
            p.cut(feed=True)
            p.close()
            logging.info("✓ Fattura stampata con font piccoli")
            return True

        # Categorizza gli items (solo per comande normali)
        bevande, cucina, altro = categorizza_items(testo)
        
        logging.info(f"Bevande trovate: {len(bevande)}")
        logging.info(f"Piatti cucina trovati: {len(cucina)}")
        logging.info(f"Altri items: {len(altro)}")
        
        # Log dettagliato per debug
        if bevande:
            logging.info(f"Bevande: {', '.join(bevande[:3])}...")
        if cucina:
            logging.info(f"Cucina: {', '.join(cucina[:3])}...")
        if altro:
            logging.info(f"Altro: {', '.join(altro[:3])}...")
        
        # Connessione
        p = Network(PRINTER_IP, PRINTER_PORT, timeout=10)
        p.hw('init')  # reset
        logging.info("Connessione stabilita")
        
        if PRINTER_NAME == 'cucina':
            # ====== CUCINA: SOLO PIATTI CALDI ======
            tutti_piatti = cucina + altro  # Altro va in cucina per sicurezza
            
            if tutti_piatti:
                stampa_sezione(p, "*** CUCINA ***", tutti_piatti, tavolo, show_footer=False)
                p.text("\n\n\n")
                p.cut(feed=True)
                logging.info(f"✓ Stampa cucina completata: {len(tutti_piatti)} articoli")
            else:
                logging.info("Nessun piatto per la cucina")
                # Stampa comunque un avviso
                img = _make_img(f"TAVOLO {tavolo}\nNESSUN PIATTO DA CUCINARE", BODY_PTS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                p.image(buf)
                p.text("\n\n\n")
                p.cut(feed=True)
        
        else:
            # ====== BANCONE: TRE STAMPE ======
            
            # 1. STAMPA COMPLETA PER IL CONTO
            logging.info("=== PRIMA STAMPA BANCONE: ORDINE COMPLETO ===")
            
            title_text = f"TAVOLO {tavolo}\n*** ORDINE COMPLETO ***"
            img = _make_img(title_text, TITLE_PTS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            p.image(buf)
            p.text("\n")
            
            # Data e ora
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            img = _make_img(timestamp, BODY_PTS // 2)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            p.image(buf)
            p.text("\n\n")
            
            # Tutto l'ordine
            for line in testo.splitlines():
                if line.strip():
                    for part in textwrap.wrap(line, 32) or [""]:
                        img = _make_img(part, BODY_PTS)
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        p.image(buf)
                    p.text("\n")
            
            # Footer prima stampa
            p.text("\n" + "-" * 48 + "\n")
            img = _make_img("PER CONTO E VERIFICA", 32)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            p.image(buf)
            p.text("\n")
            
            img = _make_img("scontrino non fiscale", 24)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            p.image(buf)
            p.text("\n")
            
            img = _make_img("ritiro scontrino fiscale in cassa", 24)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            p.image(buf)
            p.text("\n\n\n")
            
            # TAGLIO PRIMA STAMPA
            p.cut(feed=True)
            logging.info("✓ Prima stampa bancone completata")
            
            # 2. SECONDA STAMPA: SOLO BEVANDE
            if bevande:
                logging.info(f"=== SECONDA STAMPA BANCONE: {len(bevande)} BEVANDE ===")
                p.text("\n\n")  # Spazio
                stampa_sezione(p, "*** SOLO BEVANDE ***", bevande, tavolo, show_footer=False)
                
                # Footer bevande
                p.text("\n" + "-" * 48 + "\n")
                img = _make_img("DA PREPARARE AL BANCO", 32)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                p.image(buf)
                p.text("\n\n\n")
                
                # TAGLIO SECONDA STAMPA
                p.cut(feed=True)
                logging.info("✓ Seconda stampa bancone completata")
            else:
                logging.info("Nessuna bevanda da stampare separatamente")
        
        p.close()
        
        logging.info(f"=== STAMPA COMPLETATA CON SUCCESSO ===")
        return True
        
    except Exception as e:
        logging.error(f"=== ERRORE STAMPA ===")
        logging.error(f"Errore: {e}")
        logging.error(f"Tipo: {type(e).__name__}")
        logging.error(f"Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: print_job.py <tavolo>", file=sys.stderr)
        sys.exit(1)
    
    tavolo = sys.argv[1]
    comanda = sys.stdin.read()
    
    if not comanda.strip():
        logging.warning("Ricevuta comanda vuota")
        sys.exit(1)
    
    logging.info(f"=== AVVIO PRINT JOB ===")
    logging.info(f"Tavolo richiesto: '{tavolo}'")
    logging.info(f"Stampante: {PRINTER_NAME}")
    
    success = raw_print(tavolo, comanda)
    
    if success:
        logging.info("=== PRINT JOB COMPLETATO ===")
        sys.exit(0)
    else:
        logging.error("=== PRINT JOB FALLITO ===")
        sys.exit(2)
