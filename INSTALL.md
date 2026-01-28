# 📦 GUIDA INSTALLAZIONE - Sunset Bar Gestionale Ordini v2

Guida completa per installare il gestionale sulla porta **44321** del Raspberry Pi per test parallelo senza interferire con l'installazione esistente.

---

## 📋 INDICE

1. [Requisiti di Sistema](#requisiti-di-sistema)
2. [Preparazione](#preparazione)
3. [Installazione](#installazione)
4. [Configurazione](#configurazione)
5. [Avvio Test](#avvio-test)
6. [Installazione Permanente (Opzionale)](#installazione-permanente)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 📌 REQUISITI DI SISTEMA

### Hardware
- **Raspberry Pi** (modello 3B+ o superiore raccomandato)
- **Minimo 1GB RAM** (2GB raccomandato)
- **Minimo 4GB spazio libero** su SD card
- **Rete WiFi/Ethernet** attiva

### Software
- **Raspberry Pi OS** (Raspbian Buster o successivo)
- **Python 3.7+** (di solito già installato)
- **pip** (package manager Python)
- **Git** (per clonare il repository)

### Porte
- **44321** per il server test (LIBERA)
- **5000** per il server produzione (già occupata dall'installazione esistente)

---

## 🔧 PREPARAZIONE

### 1. Verifica Requisiti

```bash
# Verifica Python
python3 --version
# Output atteso: Python 3.7.x o superiore

# Verifica pip
pip3 --version

# Verifica Git
git --version

# Verifica porta 44321 libera
sudo netstat -tulpn | grep :44321
# Output atteso: nessun output (porta libera)
```

### 2. Crea Directory di Test

```bash
# Directory dedicata per i test
mkdir -p ~/gestionale-test
cd ~/gestionale-test
```

---

## 📥 INSTALLAZIONE

### 1. Clona Repository

```bash
# Clona dalla branch con le ultime modifiche
git clone -b claude/review-code-quality-rdIyv https://github.com/hunz88/gestionale-ordini-v2.git

# Entra nella directory
cd gestionale-ordini-v2
```

### 2. Installa Dipendenze Python

```bash
# Installa tutte le dipendenze
pip3 install -r requirements.txt --break-system-packages

# Se hai problemi con --break-system-packages, usa venv:
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

**Dipendenze principali installate:**
- Flask (web framework)
- Flask-SQLAlchemy (database ORM)
- Flask-CORS (gestione CORS)
- python-escpos (stampa termica)
- Pillow (gestione immagini per stampa)

### 3. Verifica Installazione

```bash
# Test import Python
python3 -c "import flask, sqlalchemy; print('✅ Dipendenze OK')"
```

---

## ⚙️ CONFIGURAZIONE

### 1. Configura Porta 44321

Modifica il file `backend/server.py` per usare la porta 44321:

```bash
# Apri con nano (o vim)
nano backend/server.py
```

**Cerca questa riga (circa riga 25):**
```python
BASE_DIR = "/home/sunsetbar/gestionale-ordini-v2"
```

**Modificala con il tuo path:**
```python
BASE_DIR = "/home/<TUO_UTENTE>/gestionale-test/gestionale-ordini-v2"
```

**Cerca questa riga finale (circa riga 1203):**
```python
app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
```

**Modificala così:**
```python
app.run(host="0.0.0.0", port=44321, threaded=True, debug=False)
```

**Salva e esci:**
- `Ctrl + O` (salva)
- `Invio` (conferma)
- `Ctrl + X` (esci)

### 2. Configura Database

Il database SQLite verrà creato automaticamente al primo avvio. Il file sarà:
```
~/gestionale-test/gestionale-ordini-v2/ordini_v2.db
```

**IMPORTANTE:** Questo database è separato da quello di produzione!

### 3. Crea Directory Logs

```bash
# Crea directory per i log
mkdir -p logs

# Verifica permessi
ls -la
```

---

## 🚀 AVVIO TEST

### Metodo 1: Avvio Manuale (Consigliato per Test)

```bash
# Dalla directory gestionale-ordini-v2
cd ~/gestionale-test/gestionale-ordini-v2/backend

# Avvia server sulla porta 44321
python3 server.py
```

**Output atteso:**
```
============================================================
🌅 SUNSET BAR - Gestionale Ordini
📁 BASE_DIR: /home/<user>/gestionale-test/gestionale-ordini-v2
💾 Database: /home/<user>/gestionale-test/gestionale-ordini-v2/ordini_v2.db
============================================================
✓ Migrazione destinazione_stampa completata
✓ Migrazione ordinamento completata
✓ Sale configurate: 4
✓ Aggiunte attive: 26
✓ Rimozioni attive: 18
============================================================
🌅 SUNSET BAR - Server in ascolto
🌐 URL: http://0.0.0.0:44321
💾 Database: /home/<user>/gestionale-test/gestionale-ordini-v2/ordini_v2.db
============================================================
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:44321
 * Running on http://192.168.x.x:44321
```

**Il server ora è in ascolto sulla porta 44321!**

### Metodo 2: Avvio in Background

```bash
# Avvia in background
cd ~/gestionale-test/gestionale-ordini-v2/backend
nohup python3 server.py > ../logs/server.log 2>&1 &

# Salva il PID per stopparlo dopo
echo $! > /tmp/gestionale-test.pid

# Verifica che sia in esecuzione
ps aux | grep server.py
```

**Per fermare:**
```bash
kill $(cat /tmp/gestionale-test.pid)
```

---

## 🔧 INSTALLAZIONE PERMANENTE (Opzionale)

Se vuoi che il server test parta automaticamente al boot del Raspberry, crea un servizio systemd.

### 1. Crea File Service

```bash
sudo nano /etc/systemd/system/gestionale-test.service
```

**Contenuto:**
```ini
[Unit]
Description=Sunset Bar Gestionale Test (Port 44321)
After=network.target

[Service]
Type=simple
User=<TUO_UTENTE>
WorkingDirectory=/home/<TUO_UTENTE>/gestionale-test/gestionale-ordini-v2/backend
ExecStart=/usr/bin/python3 /home/<TUO_UTENTE>/gestionale-test/gestionale-ordini-v2/backend/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Sostituisci `<TUO_UTENTE>` con il tuo username!**

### 2. Attiva Servizio

```bash
# Ricarica daemon
sudo systemctl daemon-reload

# Abilita avvio automatico
sudo systemctl enable gestionale-test.service

# Avvia ora
sudo systemctl start gestionale-test.service

# Verifica stato
sudo systemctl status gestionale-test.service
```

### 3. Comandi Utili

```bash
# Ferma servizio
sudo systemctl stop gestionale-test.service

# Riavvia servizio
sudo systemctl restart gestionale-test.service

# Vedi log
sudo journalctl -u gestionale-test.service -f
```

---

## ✅ TESTING

### 1. Verifica Server Attivo

```bash
# Ping locale
curl http://localhost:44321/

# Ping da rete locale
curl http://192.168.x.x:44321/
```

### 2. Accesso da Browser

**Da qualsiasi dispositivo sulla rete:**

1. **Interfaccia Mobile Nuova:**
   ```
   http://192.168.x.x:44321/index-new.html
   ```

2. **Interfaccia Mobile Classica:**
   ```
   http://192.168.x.x:44321/
   ```

3. **Interfaccia Tablet:**
   ```
   http://192.168.x.x:44321/tablet.html
   ```

4. **Ordini Attivi (con funzione AGGIUNGI ARTICOLI):**
   ```
   http://192.168.x.x:44321/history.html
   ```

5. **Pannello Admin:**
   ```
   http://192.168.x.x:44321/admin.html
   ```
   - User: `admin`
   - Password: `Peugeot2590`

6. **Riordina Menu:**
   ```
   http://192.168.x.x:44321/ordina-menu.html
   ```

### 3. Test Funzionalità

#### Test 1: Creazione Ordine
1. Vai su `http://IP:44321/index-new.html`
2. Seleziona tavolo (es: 5)
3. Seleziona categoria (es: CAFFETTERIA)
4. Aggiungi articoli (es: 2x Caffè)
5. Invia ordine
6. ✅ Verifica che appaia in `/history.html`

#### Test 2: Aggiungi Articoli a Ordine Esistente
1. Vai su `/history.html`
2. Trova l'ordine del tavolo 5
3. Clicca **"➕ Aggiungi"**
4. Seleziona categoria
5. Aggiungi articoli
6. Conferma
7. ✅ Verifica che l'ordine sia aggiornato

#### Test 3: Riordina Menu
1. Vai su `/ordina-menu.html` (serve login)
2. Seleziona categoria (es: CAFFETTERIA)
3. Trascina articoli per riordinarli
4. Clicca "💾 Salva Ordine"
5. Vai su `/index-new.html`
6. ✅ Verifica che gli articoli siano nell'ordine nuovo

---

## 🐛 TROUBLESHOOTING

### Problema: Porta già in uso

**Errore:**
```
OSError: [Errno 98] Address already in use
```

**Soluzione:**
```bash
# Trova processo sulla porta 44321
sudo lsof -i :44321

# Uccidi processo
sudo kill -9 <PID>

# Oppure usa altra porta (es: 44322)
# Modifica server.py
```

### Problema: Database locked

**Errore:**
```
sqlite3.OperationalError: database is locked
```

**Soluzione:**
```bash
# Ferma tutti i processi
killall python3

# Rimuovi lock se presente
rm -f ordini_v2.db-journal

# Riavvia server
```

### Problema: Modulo non trovato

**Errore:**
```
ModuleNotFoundError: No module named 'flask'
```

**Soluzione:**
```bash
# Reinstalla dipendenze
pip3 install -r requirements.txt --break-system-packages

# Oppure usa venv
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Problema: Permessi

**Errore:**
```
Permission denied
```

**Soluzione:**
```bash
# Dai permessi alla directory
chmod -R 755 ~/gestionale-test/gestionale-ordini-v2

# Assicurati di essere il proprietario
chown -R $USER:$USER ~/gestionale-test/gestionale-ordini-v2
```

### Problema: Stampanti non funzionano

Se le stampanti di rete non rispondono in ambiente test:

1. **Verifica IP stampanti** in `print_job.py`:
   ```python
   # Riga 25-27
   if PRINTER_NAME == 'cucina':
       PRINTER_IP = "192.168.0.10"  # Verifica questo IP
   else:
       PRINTER_IP = "192.168.0.11"  # Verifica questo IP
   ```

2. **Test ping:**
   ```bash
   ping 192.168.0.10
   ping 192.168.0.11
   ```

3. **Disabilita stampa temporaneamente** (solo per test):
   Commenta le righe di stampa in `server.py` (riga 823-828).

---

## 📊 CONFRONTO INSTALLAZIONI

| Caratteristica | Produzione (5000) | Test (44321) |
|---|---|---|
| Directory | `/home/sunsetbar/gestionale-ordini` | `~/gestionale-test/gestionale-ordini-v2` |
| Porta | 5000 | 44321 |
| Database | `ordini.db` | `ordini_v2.db` |
| URL | `http://IP:5000` | `http://IP:44321` |
| Stampanti | Attive | Attive (opzionale disabilitarle) |
| Autostart | Sì (systemd) | No (solo test) |

---

## 🎯 COMANDI RAPIDI

```bash
# AVVIO TEST
cd ~/gestionale-test/gestionale-ordini-v2/backend && python3 server.py

# STOP TEST (se in background)
kill $(cat /tmp/gestionale-test.pid)

# VEDI LOG
tail -f ~/gestionale-test/gestionale-ordini-v2/logs/gestionale.log

# RESET DATABASE (ATTENZIONE!)
rm ~/gestionale-test/gestionale-ordini-v2/ordini_v2.db
# Il DB verrà ricreato al prossimo avvio

# AGGIORNA CODICE
cd ~/gestionale-test/gestionale-ordini-v2
git pull origin claude/review-code-quality-rdIyv

# VERIFICA PORTA
sudo netstat -tulpn | grep :44321
```

---

## 📝 NOTE FINALI

### Differenze con Produzione

1. **Database separato** - Non tocca i dati di produzione
2. **Porta diversa** - Non interferisce con il server esistente
3. **Directory separata** - Installazione completamente isolata
4. **Autostart disabilitato** - Si avvia solo manualmente

### Quando Passare in Produzione

Una volta testato tutto sulla porta 44321:

1. **Ferma server test**
2. **Backup produzione:**
   ```bash
   cp /home/sunsetbar/gestionale-ordini/ordini.db ~/backup-$(date +%Y%m%d).db
   ```
3. **Aggiorna produzione:**
   ```bash
   cd /home/sunsetbar/gestionale-ordini
   git pull origin claude/review-code-quality-rdIyv
   sudo systemctl restart gestionale
   ```

### Supporto

Per problemi o domande:
- Controlla i log: `tail -f logs/gestionale.log`
- Verifica status server: `systemctl status gestionale-test`
- GitHub Issues: https://github.com/hunz88/gestionale-ordini-v2/issues

---

## ✨ FEATURES NUOVE INSTALLATE

### 1. Ordinamento Manuale Articoli
- Riordina gli articoli come preferisci per categoria
- Interfaccia drag & drop intuitiva
- Accesso: `/ordina-menu.html`

### 2. Interfaccia Mobile Moderna
- Design 2026 con step indicator
- Categorie con icone automatiche
- Carrello sempre visibile
- Accesso: `/index-new.html`

### 3. Aggiungi Articoli a Ordini Esistenti ⭐ **NUOVO!**
- Pulsante "➕ Aggiungi" su ogni ordine
- Modal con menu completo
- Carrello temporaneo
- Ristampa automatica
- Accesso: `/history.html` → Clicca "➕ Aggiungi"

---

**Buon Testing! 🚀**

