# 🚀 Deployment Produzione 2026

## 📋 Piano di Deployment

### Decisioni Architetturali

**✅ DIRECTORY PRODUZIONE:**
```
/home/sunsetbar/gestionale-2026/
```

**✅ PORTA PRODUZIONE:**
- **Opzione A (consigliata):** Porta `5000` (standard produzione)
- **Opzione B:** Porta `44321` (se vuoi mantenere uguale al test)

**Vantaggio Opzione A:** Separazione chiara test vs produzione
**Vantaggio Opzione B:** Stessa porta, più semplice

---

## 🔧 Step di Deployment

### FASE 1: Backup Sistema Vecchio (5 minuti)

```bash
# Connettiti al Raspberry
cd /home/sunsetbar

# Crea backup del sistema vecchio
sudo tar -czf gestionale-ordini-v2-backup-$(date +%Y%m%d).tar.gz gestionale-ordini-v2/

# Verifica backup
ls -lh gestionale-ordini-v2-backup-*.tar.gz
```

✅ **IMPORTANTE:** Controlla che il file backup sia stato creato prima di procedere!

---

### FASE 2: Clone Repository Nuovo Sistema (10 minuti)

```bash
cd /home/sunsetbar

# Clone del repository nella nuova directory
git clone https://github.com/hunz88/gestionale-ordini-v2.git gestionale-2026

# Entra nella directory
cd gestionale-2026

# Checkout del branch con tutti i fix
git checkout claude/review-code-quality-rdIyv
```

---

### FASE 3: Setup Database Produzione (5 minuti)

```bash
cd /home/sunsetbar/gestionale-2026

# Copia il database dal sistema vecchio (con tutti gli articoli e ordini)
cp /home/sunsetbar/gestionale-ordini/ordini.db backend/ordini.db

# Oppure se vuoi partire pulito (solo articoli, senza ordini vecchi):
python3 << 'ENDOFPYTHON'
import sqlite3
import os

# Crea directory backend se non esiste
os.makedirs('backend', exist_ok=True)

# Database vecchio con articoli
conn_old = sqlite3.connect('/home/sunsetbar/gestionale-ordini/ordini.db')
cursor_old = conn_old.cursor()

# Nuovo database (verrà creato dal server, ma possiamo pre-popolare articoli)
# Il server creerà le tabelle al primo avvio

print("✅ Database preparato - il server creerà le tabelle al primo avvio")
conn_old.close()
ENDOFPYTHON
```

---

### FASE 4: Configurazione Porta (1 minuto)

**Scegli UNA delle due opzioni:**

#### Opzione A: Porta 5000 (CONSIGLIATA)

```bash
cd /home/sunsetbar/gestionale-2026

# Crea script avvio produzione
cat > start-production.sh << 'EOF'
#!/bin/bash
export FLASK_PORT=5000
cd "$(dirname "$0")"
nohup python3 backend/server.py > logs/production.log 2>&1 &
echo $! > .pid_production
echo "✅ Server PRODUZIONE avviato su porta 5000"
echo "   PID: $(cat .pid_production)"
echo "   Log: logs/production.log"
echo "   URL: http://192.168.0.167:5000"
EOF

chmod +x start-production.sh
```

#### Opzione B: Porta 44321 (ALTERNATIVA)

```bash
cd /home/sunsetbar/gestionale-2026

# Crea script avvio produzione con porta 44321
cat > start-production.sh << 'EOF'
#!/bin/bash
export FLASK_PORT=44321
cd "$(dirname "$0")"
nohup python3 backend/server.py > logs/production.log 2>&1 &
echo $! > .pid_production
echo "✅ Server PRODUZIONE avviato su porta 44321"
echo "   PID: $(cat .pid_production)"
echo "   Log: logs/production.log"
echo "   URL: http://192.168.0.167:44321"
EOF

chmod +x start-production.sh
```

---

### FASE 5: Script Stop Produzione

```bash
cd /home/sunsetbar/gestionale-2026

cat > stop-production.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

if [ -f .pid_production ]; then
    PID=$(cat .pid_production)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm .pid_production
        echo "✅ Server PRODUZIONE fermato (PID: $PID)"
    else
        echo "⚠️  Processo $PID non trovato"
        rm .pid_production
    fi
else
    echo "⚠️  File PID non trovato, cerco processo..."
    PID=$(pgrep -f "python3 backend/server.py")
    if [ -n "$PID" ]; then
        kill $PID
        echo "✅ Server fermato (PID: $PID)"
    else
        echo "❌ Nessun server in esecuzione"
    fi
fi
EOF

chmod +x stop-production.sh
```

---

### FASE 6: Avvio Primo Server Produzione (5 minuti)

```bash
cd /home/sunsetbar/gestionale-2026

# Crea directory logs
mkdir -p logs

# Avvia server produzione
./start-production.sh

# Aspetta 5 secondi
sleep 5

# Verifica che sia partito
tail -30 logs/production.log

# Dovresti vedere:
# "🌅 SUNSET BAR - Gestionale Ordini"
# "🔧 Inizializzazione database..."
# "✓ Tabelle create: XXX"
```

---

### FASE 7: Test Funzionamento (10 minuti)

**Apri browser e vai su:**
- Se hai scelto porta 5000: `http://192.168.0.167:5000`
- Se hai scelto porta 44321: `http://192.168.0.167:44321`

**Test checklist:**
1. ✅ Login funziona (user / sunset2024)
2. ✅ Menu carica tutti gli articoli
3. ✅ Crea ordine nuovo (es. Tavolo 99: 2× Caffè)
4. ✅ Ordine appare in "Ordini Attivi"
5. ✅ Clicca "Aggiungi" → aggiungi 1× Brioche
6. ✅ Apri "Dividi Conto"
7. ✅ Totale corretto (€4.50)
8. ✅ Paga parziale 1× Caffè (€1.50)
9. ✅ Riapri "Dividi Conto"
10. ✅ Mostra solo 1× Caffè + 1× Brioche = €3.00 (NON 2× Caffè!)

---

### FASE 8: Configurazione Autostart (opzionale)

Se vuoi che il server parta automaticamente al boot del Raspberry:

```bash
# Crea servizio systemd
sudo nano /etc/systemd/system/gestionale-2026.service
```

Contenuto:
```ini
[Unit]
Description=Gestionale Ordini 2026
After=network.target

[Service]
Type=forking
User=sunsetbar
WorkingDirectory=/home/sunsetbar/gestionale-2026
Environment="FLASK_PORT=5000"
ExecStart=/home/sunsetbar/gestionale-2026/start-production.sh
ExecStop=/home/sunsetbar/gestionale-2026/stop-production.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Poi:
```bash
# Ricarica systemd
sudo systemctl daemon-reload

# Abilita autostart
sudo systemctl enable gestionale-2026.service

# Avvia servizio
sudo systemctl start gestionale-2026.service

# Verifica stato
sudo systemctl status gestionale-2026.service
```

---

### FASE 9: Spegnimento Sistema Vecchio

**SOLO DOPO che hai verificato che il nuovo funziona perfettamente!**

```bash
# Ferma il vecchio sistema (se ancora attivo)
cd /home/sunsetbar/gestionale-ordini-v2
./stop-production.sh

# Oppure trova e ferma manualmente
ps aux | grep "python.*server.py"
kill <PID>
```

---

## 📊 Riepilogo Finale

### Sistema Vecchio (da NON usare più):
```
Directory: /home/sunsetbar/gestionale-ordini-v2/
Porta: 5000 (vecchia)
Backup: /home/sunsetbar/gestionale-ordini-v2-backup-YYYYMMDD.tar.gz
```

### Sistema Nuovo PRODUZIONE 2026:
```
Directory: /home/sunsetbar/gestionale-2026/
Porta: 5000 (o 44321 se hai scelto opzione B)
Database: /home/sunsetbar/gestionale-2026/backend/ordini.db
Log: /home/sunsetbar/gestionale-2026/logs/production.log
Start: ./start-production.sh
Stop: ./stop-production.sh
```

### Sistema Test (per sviluppo futuro):
```
Directory: /home/sunsetbar/gestionale-test/gestionale-ordini-v2/
Porta: 44321
Log: logs/test.log
```

---

## 🔄 Comandi Utili Produzione

```bash
# Avvia server
cd /home/sunsetbar/gestionale-2026
./start-production.sh

# Ferma server
./stop-production.sh

# Riavvia server
./stop-production.sh && ./start-production.sh

# Guarda log in tempo reale
tail -f logs/production.log

# Verifica se è attivo
ps aux | grep "python.*server.py"

# Aggiorna codice (solo se ci sono fix)
git pull origin claude/review-code-quality-rdIyv
./stop-production.sh
./start-production.sh
```

---

## ⚠️ Note Importanti

1. **Porta Firewall:** Se usi porta 5000, assicurati che sia aperta nel firewall
2. **Database:** Il database è in `backend/ordini.db` - FANNE BACKUP REGOLARE!
3. **Log:** Controlla `logs/production.log` per errori
4. **Stampanti:** IP stampanti sono configurate in `print_job.py`:
   - Cucina: 192.168.0.10
   - Bancone: 192.168.0.11

---

## 🆘 Troubleshooting

**Server non parte:**
```bash
cd /home/sunsetbar/gestionale-2026
cat logs/production.log
```

**Porta già in uso:**
```bash
sudo lsof -i :5000
# Ferma il processo che usa la porta
kill <PID>
```

**Database non trovato:**
```bash
ls -la backend/ordini.db
# Se non esiste, il server lo creerà al primo avvio
```

---

Ultimo aggiornamento: 29 Gennaio 2026
Branch: claude/review-code-quality-rdIyv
