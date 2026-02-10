# 🚀 Deployment Fatturazione Elettronica - Raspberry Pi

## 📋 Prerequisiti

Prima di procedere, assicurati di avere:
- ✅ Accesso SSH al Raspberry Pi
- ✅ Credenziali git (se necessario)
- ✅ Dati fiscali della tua azienda (P.IVA, ragione sociale, indirizzo, regime fiscale)

---

## 🔧 Comandi Deployment su Raspberry Pi

### 1️⃣ Connettiti al Raspberry Pi

```bash
ssh sunsetbar@<IP_RASPBERRY>
# Inserisci la password quando richiesto
```

### 2️⃣ Naviga nella directory del progetto

```bash
cd /home/sunsetbar/gestionale-ordini-v2
```

### 3️⃣ Crea e checkout il branch per le fatture

```bash
# Verifica branch corrente
git branch

# Crea il branch locale se non esiste
git checkout -b claude/add-invoice-feature-7jWUI

# Oppure, se esiste già sul remote
git fetch origin
git checkout claude/add-invoice-feature-7jWUI
```

### 4️⃣ Pull delle modifiche dal repository

```bash
# Pull del branch specifico
git pull origin claude/add-invoice-feature-7jWUI

# Se ci sono conflitti, risolvili prima di continuare
```

### 5️⃣ Configura i dati della tua azienda

```bash
# Modifica il file di configurazione con i tuoi dati reali
nano backend/fatture/config_cedente.py
```

**Compila TUTTI i campi marcati con ⚠️:**
- `partita_iva`: La tua P.IVA (es: `IT12345678901`)
- `codice_fiscale`: Il tuo Codice Fiscale
- `denominazione`: Ragione sociale (es: `SUNSET BAR S.R.L.`)
- `regime_fiscale`: `RF01` (ordinario) o `RF19` (forfettario)
- `indirizzo`: Via e numero civico
- `cap`: CAP (5 cifre)
- `citta`: Città
- `provincia`: Sigla provincia (2 lettere, es: `RM`)
- `telefono`: Numero telefono (opzionale)
- `email`: Email (opzionale)

**Dopo le modifiche:**
- Premi `Ctrl+O` per salvare
- Premi `Ctrl+X` per uscire

### 6️⃣ Verifica la configurazione

```bash
# Testa che tutto sia configurato correttamente
python3 backend/fatture/config_cedente.py
```

Dovresti vedere: **✅ CONFIGURAZIONE VALIDA!**

### 7️⃣ Crea le directory necessarie

```bash
# Crea directory per i file XML
mkdir -p /home/sunsetbar/gestionale-ordini-v2/fatture_xml/2026
mkdir -p /home/sunsetbar/gestionale-ordini-v2/fatture_xml/archive

# Verifica permessi
chmod 755 /home/sunsetbar/gestionale-ordini-v2/fatture_xml
```

### 8️⃣ Aggiorna il database

```bash
# Il database verrà aggiornato automaticamente al riavvio del server
# Le nuove tabelle (clienti, fatture, righe_fattura) verranno create
```

### 9️⃣ Riavvia il server

**Se usi systemd:**
```bash
sudo systemctl restart gestionale-ordini
sudo systemctl status gestionale-ordini
```

**Se usi manualmente (meno comune):**
```bash
# Trova processo in esecuzione
ps aux | grep server.py

# Uccidi processo (sostituisci PID con l'ID reale)
kill <PID>

# Riavvia
cd /home/sunsetbar/gestionale-ordini-v2/backend
nohup python3 server.py > ../logs/server.log 2>&1 &
```

### 🔟 Verifica funzionamento

```bash
# Controlla i log
tail -f /home/sunsetbar/gestionale-ordini-v2/logs/gestionale.log

# Dovresti vedere:
# ✓ Aggiunte attive: X
# ✓ Rimozioni attive: X
# 🌅 SUNSET BAR - Server in ascolto
```

---

## ✅ Verifica dall'interfaccia web

1. **Apri il browser** sul tablet/PC
2. **Vai all'indirizzo**: `http://<IP_RASPBERRY>:4000`
3. **Verifica il nuovo pulsante**: Nella barra in alto dovresti vedere l'icona 📄 (Fatture)
4. **Accedi alla gestione fatture**:
   - Clicca su 📄
   - Inserisci credenziali admin (se richiesto):
     - Username: `admin`
     - Password: `Peugeot2590`
5. **Crea il primo cliente di test**:
   - Tab "Clienti" → "➕ Nuovo Cliente"
   - Compila i dati di un cliente fittizio per test
   - Salva

---

## 🧪 Test completo flusso fatturazione

### Test 1: Creazione cliente
1. Vai su http://<IP_RASPBERRY>:4000/gestione_fatture.html
2. Tab "Clienti" → "Nuovo Cliente"
3. Compila form e salva
4. Verifica che il cliente appaia nella lista

### Test 2: Emissione fattura da ordine
1. Torna alla home: http://<IP_RASPBERRY>:4000
2. Seleziona un tavolo
3. Aggiungi alcuni articoli al carrello
4. Clicca sul pulsante "📄 Fattura" (nuovo!)
5. Seleziona il cliente creato
6. Verifica anteprima
7. Clicca "Conferma e Genera"
8. Attendi messaggio: "✅ Fattura X/2026 emessa con successo!"

### Test 3: Download XML
1. Vai su http://<IP_RASPBERRY>:4000/gestione_fatture.html
2. Tab "Fatture"
3. Dovresti vedere la fattura appena creata
4. Clicca "👁️ Dettagli" per vedere il dettaglio
5. Clicca "💾 XML" per scaricare il file
6. Verifica che il file XML si scarichi correttamente

---

## 📂 Struttura file creati

```
/home/sunsetbar/gestionale-ordini-v2/
├── backend/
│   ├── server.py                      [MODIFICATO - nuovi endpoint API]
│   ├── fatture/                       [NUOVO]
│   │   ├── fattura_elettronica.py     # Generatore XML FatturaPA
│   │   └── config_cedente.py          # Configurazione dati azienda
│   └── frontend/
│       ├── gestione_fatture.html      [NUOVO - interfaccia gestione]
│       ├── index.html                 [MODIFICATO - aggiunto pulsante e modal]
│       └── tablet.html                [MODIFICATO - aggiunto pulsante]
├── fatture_xml/                       [NUOVO]
│   ├── 2026/                          # File XML anno corrente
│   └── archive/                       # Archivio anni precedenti
├── test_fatture_setup.py              [NUOVO - script test]
└── ordini_v2.db                       [AGGIORNATO - nuove tabelle]
```

---

## 🗃️ Nuove tabelle database create

Il sistema crea automaticamente 3 nuove tabelle:

### `clienti`
- Anagrafica clienti (P.IVA, CF, indirizzo, SDI, PEC, etc.)

### `fatture`
- Dati fatture emesse (numero, anno, cliente, totali, stato, percorso XML)

### `righe_fattura`
- Dettaglio articoli per ogni fattura

---

## 🔐 Accesso sicuro

- **Gestione Fatture**: Protetta da autenticazione (admin/Peugeot2590)
- **API Fatture**: Protette da autenticazione
- **File XML**: Accessibili solo via API autenticata

---

## 📥 Download fatture XML settimanale

Ogni settimana:

1. Accedi a http://<IP_RASPBERRY>:4000/gestione_fatture.html
2. Tab "Fatture"
3. Seleziona settimana/mese da scaricare
4. Per ogni fattura, clicca "💾 XML"
5. Salva tutti i file XML in una cartella locale
6. Carica i file sul portale Agenzia delle Entrate

**Alternativa via SSH:**
```bash
# Copia tutti gli XML dell'anno corrente
scp sunsetbar@<IP>:/home/sunsetbar/gestionale-ordini-v2/fatture_xml/2026/*.xml ./fatture_2026/
```

---

## 🆘 Troubleshooting

### Il pulsante "Fattura" non appare
- Verifica che il server sia riavviato
- Pulisci cache browser (Ctrl+Shift+R)
- Controlla log: `tail -f /home/sunsetbar/gestionale-ordini-v2/logs/gestionale.log`

### Errore "Cliente non trovato"
- Crea almeno un cliente nella sezione Gestione Fatture

### Errore generazione XML
- Verifica configurazione: `python3 backend/fatture/config_cedente.py`
- Controlla log errori nel file: `/home/sunsetbar/gestionale-ordini-v2/logs/gestionale.log`

### Database non aggiornato
```bash
# Forza ricreazione tabelle (ATTENZIONE: backup prima!)
cd /home/sunsetbar/gestionale-ordini-v2
python3 -c "from backend.server import app, db; app.app_context().push(); db.create_all(); print('✅ Tabelle create')"
```

### Permessi file XML
```bash
# Correggi permessi directory
chmod 755 /home/sunsetbar/gestionale-ordini-v2/fatture_xml
chmod 755 /home/sunsetbar/gestionale-ordini-v2/fatture_xml/2026
```

---

## 📝 Note importanti

1. **Backup regolare**: Fai backup del database `ordini_v2.db` prima di ogni modifica importante
2. **File XML permanenti**: I file XML NON vengono mai cancellati automaticamente
3. **Numerazione fatture**: Reset automatico a gennaio (2027/0001, 2028/0001, etc.)
4. **IVA predefinita**: Sistema usa 22% di default, modificabile per articolo se necessario
5. **Regime fiscale**: Verifica il tuo regime fiscale con il commercialista prima di emettere fatture

---

## 🎯 Prossimi passi (opzionali)

- [ ] Configurare backup automatico database
- [ ] Impostare aliquote IVA personalizzate per articolo
- [ ] Aggiungere stampa PDF fattura (oltre a XML)
- [ ] Integrare invio automatico SDI tramite API intermediario
- [ ] Configurare notifiche email per fatture emesse

---

## 📞 Supporto

Per problemi o domande:
- Controlla log: `/home/sunsetbar/gestionale-ordini-v2/logs/gestionale.log`
- Testa configurazione: `python3 test_fatture_setup.py`
- Verifica stato servizio: `sudo systemctl status gestionale-ordini`

---

**✅ FATTO! Il sistema di fatturazione elettronica è operativo! 🎉**
