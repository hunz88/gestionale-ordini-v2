#!/bin/bash
# Script per avviare il server in TEST (porta 44321)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

echo "🔧 Avvio server TEST (porta 44321)..."

# Controlla se è già in esecuzione
if pgrep -f "python3.*server.py.*44321" > /dev/null; then
    echo "❌ Il server TEST è già in esecuzione!"
    echo "   Usa ./stop-test.sh per fermarlo prima."
    exit 1
fi

# Avvia in background
export FLASK_PORT=44321
nohup python3 server.py > ../logs/test.log 2>&1 &
PID=$!

# Salva il PID
echo $PID > ../test.pid

sleep 2

# Verifica che sia partito
if ps -p $PID > /dev/null; then
    echo "✅ Server TEST avviato con successo!"
    echo "   PID: $PID"
    echo "   Porta: 44321"
    echo "   Log: $SCRIPT_DIR/logs/test.log"
    echo ""
    echo "   Accedi da: http://$(hostname -I | awk '{print $1}'):44321"
    echo ""
    echo "   ⚠️  ATTENZIONE: Questo è un server di TEST"
    echo "   Per fermarlo: ./stop-test.sh"
else
    echo "❌ Errore nell'avvio del server"
    rm -f ../test.pid
    exit 1
fi
