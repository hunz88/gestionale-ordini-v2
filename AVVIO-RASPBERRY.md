# 🌅 Guida Avvio Gestionale Ordini - Raspberry Pi

## 📋 DOPO OGNI RIAVVIO DEL RASPBERRY

Quando riavvii il Raspberry, devi decidere quale versione far partire:

### ✅ PRODUZIONE (porta 5000) - Per uso normale

```bash
cd /home/user/gestionale-ordini-v2
./start-production.sh
```

### 🔧 TEST (porta 44321) - Per testare nuove modifiche

```bash
cd /home/user/gestionale-ordini-v2
./start-test.sh
```

---

## 🛑 Per fermare il server

### Ferma PRODUZIONE:
```bash
cd /home/user/gestionale-ordini-v2
./stop-production.sh
```

### Ferma TEST:
```bash
cd /home/user/gestionale-ordini-v2
./stop-test.sh
```

---

## 🔄 Aggiornare il codice con nuove modifiche

Quando ci sono nuove modifiche dal repository:

```bash
cd /home/user/gestionale-ordini-v2

# 1. Ferma il server attivo
./stop-production.sh   # o ./stop-test.sh

# 2. Aggiorna il codice
git pull origin claude/review-code-quality-rdIyv

# 3. Riavvia il server
./start-production.sh  # o ./start-test.sh
```

---

## 📊 Controllare lo stato del server

```bash
# Vedi se PRODUZIONE è attiva
ps aux | grep "5000"

# Vedi se TEST è attivo
ps aux | grep "44321"

# Leggi i log PRODUZIONE
tail -f /home/user/gestionale-ordini-v2/logs/production.log

# Leggi i log TEST
tail -f /home/user/gestionale-ordini-v2/logs/test.log
```

---

## 🌐 Accesso al sistema

- **PRODUZIONE**: `http://IP-RASPBERRY:5000`
- **TEST**: `http://IP-RASPBERRY:44321`

Per trovare l'IP del Raspberry:
```bash
hostname -I
```

---

## ⚙️ Avvio automatico al boot (PRODUZIONE)

Se vuoi che il server PRODUZIONE parta automaticamente al riavvio:

```bash
# 1. Crea il servizio systemd
sudo nano /etc/systemd/system/gestionale-production.service
```

Inserisci questo contenuto:
```ini
[Unit]
Description=Gestionale Ordini PRODUZIONE
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/user/gestionale-ordini-v2/backend
Environment="FLASK_PORT=5000"
ExecStart=/usr/bin/python3 /home/user/gestionale-ordini-v2/backend/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Abilita e avvia il servizio
sudo systemctl daemon-reload
sudo systemctl enable gestionale-production.service
sudo systemctl start gestionale-production.service

# 3. Controlla lo stato
sudo systemctl status gestionale-production.service
```

Per **disabilitare** l'avvio automatico:
```bash
sudo systemctl disable gestionale-production.service
sudo systemctl stop gestionale-production.service
```

---

## 🆘 Risoluzione problemi

### Il server non parte
```bash
# Controlla i log
cat /home/user/gestionale-ordini-v2/logs/production.log

# Verifica che la porta sia libera
sudo netstat -tlnp | grep 5000
```

### Due server in esecuzione contemporaneamente
```bash
# Ferma tutto
./stop-production.sh
./stop-test.sh

# Riavvia solo quello che ti serve
./start-production.sh
```

### Errore "porta già in uso"
```bash
# Trova il processo che usa la porta
sudo lsof -i :5000

# Ferma il processo (usa il PID che vedi)
kill <PID>
```

---

## 📝 Note importanti

1. **PRODUZIONE (5000)**: Usa questo per il lavoro quotidiano
2. **TEST (44321)**: Usa questo solo per testare nuove funzioni
3. **Non far girare entrambi insieme** se usano lo stesso database
4. **Fai sempre backup** prima di aggiornamenti importanti
5. **Controlla i log** se qualcosa non funziona

---

## 🔐 Credenziali

- **Admin**: user / sunset2024

---

Ultima modifica: 29 Gennaio 2026
