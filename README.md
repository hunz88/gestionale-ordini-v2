# 🖨️ Alkemy Print Hub

**Sistema di Gestione Completo per Stampanti 3D e Laser**

Alkemy Print Hub è un'applicazione web Flask per gestire progetti di stampa 3D (Bambu Lab P1S, Flashforge M5) e laser cutting (xTool M1 Ultra), con supporto per note vocali tramite Whisper AI, generazione preventivi PDF, e tracking completo dei materiali.

---

## ✨ Caratteristiche Principali

### 🎙️ Note Vocali con AI
- Registrazione voice notes per progetti e preventivi
- Trascrizione automatica tramite OpenAI Whisper API
- Parsing intelligente di cliente, materiale, quantità e tempo
- Supporto note vocali su materiali e impostazioni

### 📊 Dashboard Completa
- Statistiche real-time: progetti attivi, guadagni mensili
- Alert materiali in esaurimento
- Grafici progetti per stato e materiali più usati
- Quick actions per velocizzare il workflow

### 🔧 Gestione Progetti
- Creazione progetti con voice note o form manuale
- Upload foto progresso (prima/durante/dopo)
- Calcolo automatico costi: materiale + lavoro + margine
- Timeline stati: quote → designing → printing → completed
- Rating risultati (1-5 stelle) per ottimizzare profili stampa

### 📦 Gestione Materiali
- Tracking stock con alert automatici (🟢 >30%, 🟡 10-30%, 🔴 <10%)
- Costi per kg (3D) o per foglio (laser)
- QR code univoci per ogni materiale
- Impostazioni ottimali (temperatura, velocità)
- Auto-decremento stock al completamento progetti

### ⚡ Preventivi Rapidi
- Quick quote con voice note cliente
- Generazione PDF professionale con QR code
- Conversione preventivo → progetto con un click
- Storico preventivi con stati (pending/accepted/rejected)

### 📈 Storico & Analytics
- Filtri avanzati: cliente, stato, stampante, date
- Export CSV progetti
- Statistiche guadagni totali per periodo
- Materiali più utilizzati

### ⚙️ Impostazioni Business
- Tariffa oraria lavoro (€/h)
- Margine default (%)
- Gestione API keys
- Enable/disable stampanti attive
- Backup database

---

## 🚀 Installazione

### Prerequisiti
- Python 3.9+
- pip
- Virtualenv (consigliato)

### Setup Rapido

1. **Clona o scarica il progetto**
```bash
cd /home/pi/alkemy-print-hub
```

2. **Crea ambiente virtuale**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows
```

3. **Installa dipendenze**
```bash
pip install -r requirements.txt
```

4. **Configura variabili d'ambiente**
```bash
cp .env.example .env
nano .env  # Modifica con i tuoi valori
```

**Variabili importanti:**
```env
OPENAI_API_KEY=sk-your-api-key-here  # Richiesto per trascrizioni
FLASK_ENV=development  # production per deploy
SECRET_KEY=your-secret-key-here
FLASK_PORT=5321
```

5. **Inizializza database con dati esempio**
```bash
python app.py
```
Questo creerà automaticamente:
- Database SQLite in `data/printshub.db`
- 4 materiali di esempio (PLA, PETG, Acrilico, Compensato)
- 2 progetti di esempio
- Impostazioni default

6. **Avvia il server**
```bash
python app.py
```

7. **Accedi all'applicazione**
Apri il browser su: **http://localhost:5321**

---

## 📁 Struttura Progetto

```
alkemy-print-hub/
├── app.py                  # Applicazione Flask principale
├── config.py               # Configurazioni
├── database.py             # Modelli SQLAlchemy
├── whisper_service.py      # Servizio trascrizioni Whisper
├── pdf_generator.py        # Generazione PDF preventivi
├── requirements.txt        # Dipendenze Python
├── .env                    # Variabili d'ambiente (NON committare!)
├── .env.example            # Template variabili
├── README.md               # Questa documentazione
│
├── templates/              # Template HTML Jinja2
│   ├── base.html          # Template base con navbar
│   ├── dashboard.html
│   ├── new_project.html
│   ├── project_detail.html
│   ├── materials.html
│   ├── quick_quote.html
│   ├── history.html
│   └── settings.html
│
├── static/                 # File statici
│   ├── css/
│   │   └── style.css      # Stili custom (brand colors)
│   ├── js/
│   │   └── app.js         # JavaScript utilities
│   └── uploads/           # Upload files
│       ├── audio/         # Voice notes audio
│       ├── photos/        # Foto progetti
│       └── quotes/        # PDF preventivi
│
└── data/
    └── printshub.db       # Database SQLite
```

---

## 🎨 Brand & Design

**Colori Alkemy:**
- **Arancione**: `#FF6B35` (pulsanti primari, accenti)
- **Blu Scuro**: `#004E89` (header, elementi secondari)

**UI/UX:**
- Mobile-first responsive (ottimizzato per tablet in laboratorio)
- Dark mode default
- Bootstrap 5.3 + custom CSS
- Font: Inter / System UI

---

## 🗄️ Database Schema

### Projects
```sql
id, title, customer_name, printer_type, material_id, status,
voice_note_path, voice_transcription, estimated_time_hours,
actual_time_hours, material_cost, labor_cost, final_price,
margin_percentage, quantity, photos (JSON), settings_notes,
result_rating, created_at, completed_at
```

### Materials
```sql
id, name, type, printer_compatible, color, cost_per_kg,
cost_per_sheet, current_stock_kg, initial_stock_kg, qr_code,
optimal_temp, optimal_speed, voice_notes, last_used
```

### VoiceNotes
```sql
id, project_id, audio_path, transcription, note_type, created_at
```

### Quotes
```sql
id, project_id, customer_name, description, voice_request,
estimated_price, status, pdf_path, created_at
```

### Settings
```sql
id, key, value, updated_at
```

---

## 🔧 Configurazione Avanzata

### OpenAI Whisper API

1. Ottieni API key da: https://platform.openai.com/api-keys
2. Aggiungi in `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
```

**Nota:** Senza API key, il sistema usa trascrizioni mock per testing.

### Deploy su Raspberry Pi 5

#### Metodo 1: Systemd Service (Consigliato)

1. Crea file service:
```bash
sudo nano /etc/systemd/system/alkemy-print-hub.service
```

```ini
[Unit]
Description=Alkemy Print Hub
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/alkemy-print-hub
ExecStart=/home/pi/alkemy-print-hub/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Abilita e avvia:
```bash
sudo systemctl daemon-reload
sudo systemctl enable alkemy-print-hub
sudo systemctl start alkemy-print-hub
sudo systemctl status alkemy-print-hub
```

#### Metodo 2: Gunicorn + Nginx (Produzione)

1. Installa Gunicorn:
```bash
pip install gunicorn
```

2. Avvia con Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5321 app:app
```

3. Configura Nginx reverse proxy:
```nginx
server {
    listen 80;
    server_name your-raspberry-pi-ip;

    location / {
        proxy_pass http://127.0.0.1:5321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📱 Utilizzo

### 1. Creare un Nuovo Progetto

1. Dashboard → **Nuovo Progetto**
2. **🎤 Registra Idea**: "Devo fare 10 portachiavi in PLA rosso per Marco"
3. Sistema auto-compila: cliente, materiale, quantità
4. Upload foto (opzionale)
5. Verifica calcolo costi automatico
6. **Crea Progetto**

### 2. Gestire Materiali

1. Navbar → **Materiali**
2. **Nuovo Materiale**: aggiungi PLA, PETG, acrilico, etc.
3. Imposta stock iniziale e costi
4. Sistema genera QR code automatico
5. Alert automatici quando stock < 30%

### 3. Preventivo Rapido

1. Navbar → **Quick Quote**
2. **🎤 Registra Richiesta Cliente**
3. Sistema auto-genera preventivo
4. **Genera PDF** → scarica o invia
5. Opzione: **Converti in Progetto**

### 4. Tracking Progetto

1. Dashboard → click su progetto
2. Aggiorna stato: quote → designing → printing → completed
3. **Aggiungi Nota Vocale**: problemi, modifiche, risultato
4. Imposta tempo effettivo
5. Rating finale (1-5 stelle)

---

## 🔍 API Endpoints

### Trascrizione Audio
```http
POST /api/transcribe
Content-Type: multipart/form-data

Form Data:
- audio: file (webm, mp3, wav)
- context: "project" | "material" | "quote"

Response:
{
  "success": true,
  "transcription": "...",
  "parsed_info": {
    "customer_name": "Mario Rossi",
    "quantity": 10,
    "material": "pla",
    "estimated_hours": 3.0
  }
}
```

### Materiali Compatibili
```http
GET /api/materials/compatible/:printer_type

Response:
[
  {
    "id": 1,
    "name": "PLA Bianco",
    "cost_per_kg": 18.50,
    "stock_percentage": 75.0
  }
]
```

### Statistiche Mensili
```http
GET /api/stats/monthly

Response:
[
  {
    "month": "January 2026",
    "earnings": 450.00,
    "projects": 12
  }
]
```

---

## 🛠️ Troubleshooting

### Problema: "No module named 'openai'"
**Soluzione:**
```bash
pip install openai==1.12.0
```

### Problema: Permessi microfono negati
**Soluzione:**
- Browser: Impostazioni → Privacy → Microfono → Consenti per localhost
- HTTPS richiesto in produzione per getUserMedia API

### Problema: Database locked
**Soluzione:**
```bash
# Chiudi tutte le connessioni e riavvia
sudo systemctl restart alkemy-print-hub
```

### Problema: File upload troppo grande
**Soluzione:**
Aumenta `MAX_CONTENT_LENGTH` in `config.py`:
```python
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
```

---

## 🔒 Sicurezza

- **NON committare** il file `.env` con API keys
- Cambia `SECRET_KEY` in produzione
- Usa HTTPS per deployment pubblico
- Implementa autenticazione utente per multi-user
- Backup regolari del database:
  ```bash
  cp data/printshub.db data/printshub_backup_$(date +%Y%m%d).db
  ```

---

## 🚀 Roadmap Futuri Sviluppi

- [ ] Autenticazione multi-utente
- [ ] Integrazione diretta stampanti (API Bambu/Flashforge)
- [ ] Thermal printer per etichette QR materiali
- [ ] Print profiles library condivisa
- [ ] Export reports Excel/PDF
- [ ] Notifiche email/Telegram completamento stampe
- [ ] Mobile app companion (React Native)
- [ ] Integrazione calendario per scheduling stampe

---

## 📞 Supporto

**Sviluppato per:** Alkemy Company - Sunset Bar

**Contatti:**
- Email: support@alkemy.example.com
- Repository: [Link GitHub]

---

## 📄 Licenza

Proprietario - Alkemy Company © 2026

---

## 🙏 Credits

- **Flask** - Web framework
- **Bootstrap 5** - UI framework
- **RecordRTC** - Voice recording
- **OpenAI Whisper** - Speech-to-text
- **ReportLab** - PDF generation
- **Chart.js** - Grafici

---

**Versione:** 1.0.0
**Ultima Modifica:** 30 Gennaio 2026

---

## 🎯 Quick Start Command

```bash
# Setup completo in un comando
git clone [repo] && cd alkemy-print-hub && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python app.py
```

**Buona stampa! 🖨️✨**
