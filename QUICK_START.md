# 🚀 QUICK START - Alkemy Print Hub su Raspberry Pi 5

Guida rapida per installare e avviare Alkemy Print Hub sul tuo Raspberry Pi 5.

---

## 📥 STEP 1: Scarica l'Applicazione

Sul tuo **Raspberry Pi 5**, apri il terminale e esegui:

```bash
# Vai nella home directory
cd ~

# Clona/scarica il progetto
git clone https://github.com/hunz88/alkemy-print-hub.git

# Entra nella cartella
cd alkemy-print-hub
```

> **Nota:** Se il repository non è ancora pubblico, scarica i file dalla directory locale `/home/user/alkemy-print-hub`

---

## ⚙️ STEP 2: Setup Automatico

Esegui lo script di setup automatico:

```bash
# Rendi eseguibile lo script
chmod +x start.sh

# Lancia il setup e avvio
./start.sh
```

Lo script farà **automaticamente**:
- ✅ Crea virtual environment Python
- ✅ Installa tutte le dipendenze
- ✅ Crea file .env (da configurare)
- ✅ Inizializza database con dati esempio
- ✅ Avvia il server su porta 5321

---

## 🔑 STEP 3: Configura OpenAI API (Opzionale ma Consigliato)

Per abilitare le **trascrizioni vocali reali**:

1. **Ottieni API key** da OpenAI:
   - Vai su: https://platform.openai.com/api-keys
   - Crea una nuova API key

2. **Modifica il file .env**:
   ```bash
   nano .env
   ```

3. **Incolla la tua API key**:
   ```env
   OPENAI_API_KEY=sk-tua-chiave-api-qui
   ```

4. **Salva** (Ctrl+O, Invio, Ctrl+X)

5. **Riavvia** l'applicazione (Ctrl+C poi `./start.sh`)

> **Nota:** Senza API key, l'app funziona ugualmente con trascrizioni mock per testing!

---

## 🌐 STEP 4: Accedi all'Applicazione

Apri il browser su:

### **Dal Raspberry Pi stesso:**
```
http://localhost:5321
```

### **Da un altro dispositivo sulla stessa rete:**
```
http://[IP_DEL_RASPBERRY]:5321
```

Per trovare l'IP del Raspberry Pi:
```bash
hostname -I
```

---

## 🎨 STEP 5: Prima Configurazione

1. **Vai su Impostazioni** (icona ingranaggio in alto a destra)

2. **Configura le tue tariffe**:
   - Tariffa oraria lavoro (default: 15€/h)
   - Margine percentuale (default: 30%)

3. **Salva Impostazioni**

4. **Vai alla Dashboard** e inizia a creare progetti!

---

## 📦 Dati di Esempio

L'applicazione viene inizializzata con:

### **Materiali (4):**
- PLA Bianco Sunlu (stock 75%)
- PETG Trasparente (stock 45% - alert)
- Acrilico Trasparente 3mm (stock 50%)
- Compensato 5mm (stock 20% - alert)

### **Progetti (2):**
- Portachiavi personalizzati (completato)
- Targhe acriliche (in stampa)

Puoi **modificarli o eliminarli** dal menu Materiali e Dashboard.

---

## 🔄 Comandi Utili

### **Avviare il server:**
```bash
cd ~/alkemy-print-hub
./start.sh
```

### **Fermare il server:**
Premi `Ctrl+C` nel terminale

### **Riavviare dopo modifiche:**
```bash
# Ferma (Ctrl+C), poi:
./start.sh
```

### **Vedere lo status:**
```bash
# Se usi systemd (vedi sotto)
sudo systemctl status alkemy-print-hub
```

---

## 🔧 OPZIONE: Avvio Automatico (Systemd)

Per far partire l'app **automaticamente** all'avvio del Raspberry Pi:

1. **Crea il service file:**
   ```bash
   sudo nano /etc/systemd/system/alkemy-print-hub.service
   ```

2. **Incolla questo contenuto** (sostituisci `/home/pi` con il tuo percorso se diverso):
   ```ini
   [Unit]
   Description=Alkemy Print Hub - Gestionale Stampanti 3D/Laser
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/alkemy-print-hub
   ExecStart=/home/pi/alkemy-print-hub/venv/bin/python /home/pi/alkemy-print-hub/app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Salva** (Ctrl+O, Invio, Ctrl+X)

4. **Abilita e avvia il servizio:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable alkemy-print-hub
   sudo systemctl start alkemy-print-hub
   ```

5. **Verifica che funzioni:**
   ```bash
   sudo systemctl status alkemy-print-hub
   ```

6. **Comandi utili:**
   ```bash
   # Fermare il servizio
   sudo systemctl stop alkemy-print-hub

   # Riavviare il servizio
   sudo systemctl restart alkemy-print-hub

   # Vedere i log
   sudo journalctl -u alkemy-print-hub -f
   ```

---

## 🐳 ALTERNATIVA: Docker (Se preferisci)

Se hai Docker installato sul Raspberry Pi:

```bash
# Build e avvio con un solo comando
docker-compose up -d

# Vedere i log
docker-compose logs -f

# Fermare
docker-compose down
```

---

## ✅ Checklist Veloce

- [ ] Scaricato il progetto `alkemy-print-hub`
- [ ] Eseguito `./start.sh`
- [ ] Configurato `.env` con API key OpenAI (opzionale)
- [ ] Aperto http://localhost:5321 nel browser
- [ ] Configurato tariffe in Impostazioni
- [ ] Testato creazione progetto con voice note
- [ ] (Opzionale) Configurato systemd per avvio automatico

---

## 🆘 Problemi Comuni

### **Problema: "Porta 5321 già in uso"**
```bash
# Trova il processo sulla porta 5321
sudo lsof -i :5321

# Termina il processo (sostituisci PID con il numero visualizzato)
kill -9 PID

# Oppure usa un'altra porta modificando .env:
FLASK_PORT=5322
```

### **Problema: "ModuleNotFoundError: No module named 'flask'"**
```bash
# Assicurati di essere nel virtual environment
source venv/bin/activate

# Reinstalla dipendenze
pip install -r requirements.txt
```

### **Problema: Microfono non funziona nel browser**
- Verifica permessi microfono nelle impostazioni del browser
- Per accesso da remoto, usa **HTTPS** (richiesto da RecordRTC)

### **Problema: Database non si crea**
```bash
# Crea manualmente la cartella data
mkdir -p data

# Riavvia l'applicazione
./start.sh
```

---

## 📞 Supporto

Per assistenza completa, consulta il **README.md** principale.

**Progetto:** Alkemy Print Hub - Sistema Gestionale Stampanti 3D/Laser

---

## 🎉 Tutto Pronto!

Il tuo **Alkemy Print Hub** è ora attivo e funzionante!

**URL:** http://localhost:5321

**Buona stampa! 🖨️✨**

---

**Versione:** 1.0.0
**Data:** 30 Gennaio 2026
**Sistema:** Raspberry Pi 5 - Python 3 + Flask
