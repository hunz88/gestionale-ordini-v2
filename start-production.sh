#!/bin/bash
# Script per avviare il server in PRODUZIONE (porta 5000)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

echo "🌅 Avvio server PRODUZIONE (porta 5000)..."

# Controlla se è già in esecuzione
if pgrep -f "python3.*server.py.*5000" > /dev/null; then
    echo "❌ Il server PRODUZIONE è già in esecuzione!"
    echo "   Usa ./stop-production.sh per fermarlo prima."
    exit 1
fi

# Avvia in background
export FLASK_PORT=5000
nohup python3 server.py > ../logs/production.log 2>&1 &
PID=$!

# Salva il PID
echo $PID > ../production.pid

sleep 2

# Verifica che sia partito
if ps -p $PID > /dev/null; then
    echo "✅ Server PRODUZIONE avviato con successo!"
    echo "   PID: $PID"
    echo "   Porta: 5000"
    echo "   Log: $SCRIPT_DIR/logs/production.log"
    echo ""
    echo "   Accedi da: http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "   Per fermarlo: ./stop-production.sh"
else
    echo "❌ Errore nell'avvio del server"
    rm -f ../production.pid
    exit 1
fi
