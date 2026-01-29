#!/bin/bash
# Script per fermare il server PRODUZIONE (porta 5000)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/production.pid"

echo "🛑 Arresto server PRODUZIONE..."

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Server PRODUZIONE fermato (PID: $PID)"
        rm -f "$PID_FILE"
    else
        echo "⚠️  Il processo PID $PID non è in esecuzione"
        rm -f "$PID_FILE"
    fi
else
    # Cerca per nome processo
    PIDS=$(pgrep -f "python3.*server.py.*5000")
    if [ -n "$PIDS" ]; then
        echo "   Trovati processi: $PIDS"
        kill $PIDS
        echo "✅ Server PRODUZIONE fermato"
    else
        echo "⚠️  Nessun server PRODUZIONE in esecuzione"
    fi
fi
