# 🚀 Deployment Produzione - Porta 5123
## Guida COPY-PASTE - Basta seguire in ordine!

---

## 📋 STEP 1: Backup Sistema Vecchio (30 secondi)

**Copia e incolla nel terminale del Raspberry:**

```bash
cd /home/sunsetbar
sudo tar -czf gestionale-BACKUP-$(date +%Y%m%d-%H%M).tar.gz gestionale-ordini-v2/ gestionale-test/
ls -lh gestionale-BACKUP-*.tar.gz
echo "✅ BACKUP COMPLETATO"
```

✅ Aspetta che finisca, vedrai "✅ BACKUP COMPLETATO"

---

## 📋 STEP 2: Clone Repository in Produzione (1 minuto)

**Copia e incolla:**

```bash
cd /home/sunsetbar
git clone https://github.com/hunz88/gestionale-ordini-v2.git gestionale-2026
cd gestionale-2026
git checkout claude/review-code-quality-rdIyv
echo "✅ REPOSITORY CLONATO"
```

✅ Aspetta "✅ REPOSITORY CLONATO"

---

## 📋 STEP 3: Copia Database Funzionante dal Test (10 secondi)

**Copia e incolla:**

```bash
cd /home/sunsetbar/gestionale-2026
mkdir -p backend
cp /home/sunsetbar/gestionale-test/gestionale-ordini-v2/backend/ordini.db backend/ordini.db
ls -lh backend/ordini.db
echo "✅ DATABASE COPIATO CON TUTTI GLI ARTICOLI"
```

✅ Vedrai il file database e "✅ DATABASE COPIATO"

---

## 📋 STEP 4: Crea Script Avvio Produzione (20 secondi)

**Copia e incolla TUTTO questo blocco:**

```bash
cd /home/sunsetbar/gestionale-2026

cat > start-production.sh << 'EOF'
#!/bin/bash
export FLASK_PORT=5123
cd "$(dirname "$0")"
mkdir -p logs
nohup python3 backend/server.py > logs/production.log 2>&1 &
echo $! > .pid_production
sleep 2
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ SERVER PRODUZIONE 2026 AVVIATO!"
echo "═══════════════════════════════════════════════════════"
echo "   🌐 URL: http://192.168.0.167:5123"
echo "   🔐 Login: user / sunset2024"
echo "   📊 PID: $(cat .pid_production)"
echo "   📁 Log: logs/production.log"
echo ""
echo "Per vedere i log in tempo reale:"
echo "   tail -f logs/production.log"
echo ""
echo "Per fermare il server:"
echo "   ./stop-production.sh"
echo "═══════════════════════════════════════════════════════"
EOF

chmod +x start-production.sh
echo "✅ SCRIPT AVVIO CREATO"
```

---

## 📋 STEP 5: Crea Script Stop Produzione (10 secondi)

**Copia e incolla:**

```bash
cd /home/sunsetbar/gestionale-2026

cat > stop-production.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "🛑 Arresto server PRODUZIONE..."

if [ -f .pid_production ]; then
    PID=$(cat .pid_production)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm .pid_production
        echo "✅ Server PRODUZIONE fermato (PID: $PID)"
    else
        echo "⚠️  Processo già fermato"
        rm .pid_production
    fi
else
    echo "⚠️  File PID non trovato, cerco processo..."
    PID=$(pgrep -f "python3 backend/server.py.*5123")
    if [ -n "$PID" ]; then
        kill $PID
        echo "✅ Server fermato (PID: $PID)"
    else
        echo "ℹ️  Nessun server in esecuzione sulla porta 5123"
    fi
fi
EOF

chmod +x stop-production.sh
echo "✅ SCRIPT STOP CREATO"
```

---

## 📋 STEP 6: Ferma Server Test (se attivo) (5 secondi)

**Copia e incolla:**

```bash
cd /home/sunsetbar/gestionale-test/gestionale-ordini-v2
./stop-test.sh
echo "✅ SERVER TEST FERMATO"
```

---

## 📋 STEP 7: AVVIA SERVER PRODUZIONE! 🚀 (10 secondi)

**Copia e incolla:**

```bash
cd /home/sunsetbar/gestionale-2026
./start-production.sh
```

✅ Vedrai il box con tutte le info del server!

---

## 📋 STEP 8: Verifica che Funzioni (1 minuto)

**Apri browser e vai su:**

```
http://192.168.0.167:5123
```

**Login:**
- User: `user`
- Password: `sunset2024`

**Dovresti vedere:**
- ✅ Menu con tutti gli articoli (155 articoli)
- ✅ Pagina "Ordini Attivi"
- ✅ Tutto funzionante!

---

## 📋 STEP 9: Test Veloce Dividi Conto (2 minuti)

1. **Crea ordine:**
   - Tavolo: 99
   - 3× Caffè (o altro articolo)
   - Invia

2. **Apri "Dividi Conto"**
   - Clicca su un articolo per pagarlo
   - Conferma pagamento parziale

3. **Riapri "Dividi Conto"**
   - ✅ Deve mostrare SOLO gli articoli rimanenti
   - ✅ Totale corretto

---

## ✅ FATTO! Sistema in Produzione

**Il tuo nuovo sistema è attivo su:**
```
http://192.168.0.167:5123
```

---

## 🔧 Comandi Utili da Ricordare

### Avvia server produzione
```bash
cd /home/sunsetbar/gestionale-2026
./start-production.sh
```

### Ferma server produzione
```bash
cd /home/sunsetbar/gestionale-2026
./stop-production.sh
```

### Riavvia server produzione
```bash
cd /home/sunsetbar/gestionale-2026
./stop-production.sh && ./start-production.sh
```

### Guarda log in tempo reale
```bash
cd /home/sunsetbar/gestionale-2026
tail -f logs/production.log
```

### Verifica se è attivo
```bash
ps aux | grep "python.*server.py"
```

### Aggiorna codice (se ci sono fix futuri)
```bash
cd /home/sunsetbar/gestionale-2026
./stop-production.sh
git pull origin claude/review-code-quality-rdIyv
./start-production.sh
```

---

## 📊 Struttura Finale

```
/home/sunsetbar/
├── gestionale-ordini-v2/           ← Vecchio (non toccare)
├── gestionale-test/                ← Test (porta 44321)
│   └── gestionale-ordini-v2/
└── gestionale-2026/                ← PRODUZIONE (porta 5123) ⭐
    ├── backend/
    │   ├── server.py
    │   └── ordini.db              ← Database con tutti gli articoli
    ├── logs/
    │   └── production.log
    ├── start-production.sh
    └── stop-production.sh
```

---

## 🆘 Troubleshooting

**Problema: Server non parte**
```bash
cd /home/sunsetbar/gestionale-2026
cat logs/production.log
```
Cerca errori nel log.

**Problema: "Porta già in uso"**
```bash
sudo lsof -i :5123
kill <PID>
./start-production.sh
```

**Problema: "Articoli non visibili"**
```bash
cd /home/sunsetbar/gestionale-2026
python3 -c "
import sqlite3
conn = sqlite3.connect('backend/ordini.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM voce')
print(f'Articoli: {cursor.fetchone()[0]}')
conn.close()
"
```
Se vedi 0, ri-copia il database:
```bash
cp /home/sunsetbar/gestionale-test/gestionale-ordini-v2/backend/ordini.db backend/ordini.db
./stop-production.sh && ./start-production.sh
```

---

## 🎯 Checklist Deployment

- [ ] STEP 1: Backup completato
- [ ] STEP 2: Repository clonato in gestionale-2026
- [ ] STEP 3: Database copiato da test
- [ ] STEP 4: Script start-production.sh creato
- [ ] STEP 5: Script stop-production.sh creato
- [ ] STEP 6: Server test fermato
- [ ] STEP 7: Server produzione avviato
- [ ] STEP 8: Browser aperto su porta 5123
- [ ] STEP 9: Test dividi conto OK

---

**🎉 Quando tutto funziona, il sistema è pronto per l'uso quotidiano!**

Ultimo aggiornamento: 29 Gennaio 2026
