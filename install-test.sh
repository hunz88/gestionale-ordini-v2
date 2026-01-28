#!/bin/bash
################################################################################
# INSTALL-TEST.sh - SUNSET BAR
# Script automatico per installare il gestionale sulla porta 44321 per test
################################################################################

set -e  # Esce se c'è un errore

echo "============================================================"
echo "🌅 SUNSET BAR - Installazione Test (Porta 44321)"
echo "============================================================"
echo ""

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE
# ══════════════════════════════════════════════════════════════════════════════
TEST_PORT=44321
INSTALL_DIR="$HOME/gestionale-test"
REPO_URL="https://github.com/hunz88/gestionale-ordini-v2.git"
BRANCH="claude/review-code-quality-rdIyv"

echo -e "${BLUE}📁 Directory installazione: ${NC}$INSTALL_DIR"
echo -e "${BLUE}🔌 Porta test: ${NC}$TEST_PORT"
echo ""

# ══════════════════════════════════════════════════════════════════════════════
# VERIFICA REQUISITI
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}🔍 Verifica requisiti...${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 non trovato!${NC}"
    echo "Installa con: sudo apt install python3 python3-pip"
    exit 1
fi
echo -e "${GREEN}✓ Python3: $(python3 --version)${NC}"

# pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 non trovato!${NC}"
    echo "Installa con: sudo apt install python3-pip"
    exit 1
fi
echo -e "${GREEN}✓ pip3 installato${NC}"

# Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git non trovato!${NC}"
    echo "Installa con: sudo apt install git"
    exit 1
fi
echo -e "${GREEN}✓ Git installato${NC}"

# Verifica porta libera
if sudo netstat -tulpn 2>/dev/null | grep -q ":$TEST_PORT "; then
    echo -e "${RED}❌ ERRORE: Porta $TEST_PORT già in uso!${NC}"
    echo "Processi sulla porta $TEST_PORT:"
    sudo lsof -i :$TEST_PORT
    echo ""
    read -p "Vuoi killare i processi e continuare? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo kill -9 $(sudo lsof -t -i:$TEST_PORT)
        echo -e "${GREEN}✓ Processi terminati${NC}"
    else
        exit 1
    fi
else
    echo -e "${GREEN}✓ Porta $TEST_PORT libera${NC}"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# CREAZIONE DIRECTORY
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${YELLOW}📁 Creazione directory...${NC}"

if [ -d "$INSTALL_DIR/gestionale-ordini-v2" ]; then
    echo -e "${YELLOW}⚠️  Directory già esistente!${NC}"
    read -p "Vuoi sovrascrivere? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR/gestionale-ordini-v2"
        echo -e "${GREEN}✓ Directory rimossa${NC}"
    else
        echo "Installazione annullata"
        exit 0
    fi
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
echo -e "${GREEN}✓ Directory creata${NC}"

# ══════════════════════════════════════════════════════════════════════════════
# CLONAZIONE REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}📥 Clonazione repository...${NC}"

git clone -b "$BRANCH" "$REPO_URL"
cd gestionale-ordini-v2

echo -e "${GREEN}✓ Repository clonato${NC}"

# ══════════════════════════════════════════════════════════════════════════════
# INSTALLAZIONE DIPENDENZE
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}📦 Installazione dipendenze Python...${NC}"

pip3 install -r requirements.txt --break-system-packages --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dipendenze installate${NC}"
else
    echo -e "${RED}❌ Errore installazione dipendenze${NC}"
    echo "Prova manualmente:"
    echo "  cd $INSTALL_DIR/gestionale-ordini-v2"
    echo "  pip3 install -r requirements.txt"
    exit 1
fi

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAZIONE PORTA
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}⚙️  Configurazione porta $TEST_PORT...${NC}"

# Modifica porta in server.py
sed -i "s/port=5000/port=$TEST_PORT/g" backend/server.py

# Modifica BASE_DIR
ESCAPED_DIR=$(echo "$INSTALL_DIR/gestionale-ordini-v2" | sed 's/\//\\\//g')
sed -i "s/BASE_DIR = \"\/home\/sunsetbar\/gestionale-ordini-v2\"/BASE_DIR = \"$ESCAPED_DIR\"/g" backend/server.py

echo -e "${GREEN}✓ Porta configurata su $TEST_PORT${NC}"

# ══════════════════════════════════════════════════════════════════════════════
# CREAZIONE DIRECTORY LOGS
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p logs
echo -e "${GREEN}✓ Directory logs creata${NC}"

# ══════════════════════════════════════════════════════════════════════════════
# CREA SCRIPT AVVIO
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}📝 Creazione script di avvio...${NC}"

cat > start-test.sh << 'EOFSTART'
#!/bin/bash
cd "$(dirname "$0")/backend"
echo "🌅 Avvio Sunset Bar Gestionale Test..."
echo "🔌 Porta: 44321"
echo "📁 Directory: $(pwd)"
echo ""
echo "Per fermare: Ctrl+C"
echo "============================================================"
python3 server.py
EOFSTART

chmod +x start-test.sh
echo -e "${GREEN}✓ Script start-test.sh creato${NC}"

# ══════════════════════════════════════════════════════════════════════════════
# CREA SCRIPT STOP
# ══════════════════════════════════════════════════════════════════════════════
cat > stop-test.sh << 'EOFSTOP'
#!/bin/bash
echo "🛑 Fermando server test..."
pkill -f "python3.*server.py"
echo "✓ Server fermato"
EOFSTOP

chmod +x stop-test.sh
echo -e "${GREEN}✓ Script stop-test.sh creato${NC}"

# ══════════════════════════════════════════════════════════════════════════════
# RIEPILOGO
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "============================================================"
echo -e "${GREEN}✅ INSTALLAZIONE COMPLETATA!${NC}"
echo "============================================================"
echo ""
echo -e "${BLUE}📊 RIEPILOGO:${NC}"
echo "   📁 Directory: $INSTALL_DIR/gestionale-ordini-v2"
echo "   🔌 Porta: $TEST_PORT"
echo "   💾 Database: ordini_v2.db (verrà creato al primo avvio)"
echo ""
echo -e "${BLUE}🚀 AVVIO:${NC}"
echo "   cd $INSTALL_DIR/gestionale-ordini-v2"
echo "   ./start-test.sh"
echo ""
echo -e "${BLUE}🌐 URL ACCESSO:${NC}"
# Ottieni IP locale
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "   http://localhost:$TEST_PORT"
echo "   http://$LOCAL_IP:$TEST_PORT"
echo ""
echo -e "${BLUE}📱 INTERFACCE:${NC}"
echo "   Mobile Nuova:    http://$LOCAL_IP:$TEST_PORT/index-new.html"
echo "   Mobile Classica: http://$LOCAL_IP:$TEST_PORT/"
echo "   Tablet:          http://$LOCAL_IP:$TEST_PORT/tablet.html"
echo "   Ordini Attivi:   http://$LOCAL_IP:$TEST_PORT/history.html"
echo "   Admin:           http://$LOCAL_IP:$TEST_PORT/admin.html"
echo "   Riordina Menu:   http://$LOCAL_IP:$TEST_PORT/ordina-menu.html"
echo ""
echo -e "${BLUE}🔑 CREDENZIALI ADMIN:${NC}"
echo "   Username: admin"
echo "   Password: Peugeot2590"
echo ""
echo -e "${BLUE}🛑 STOP:${NC}"
echo "   ./stop-test.sh"
echo ""
echo -e "${YELLOW}📖 Per info dettagliate vedi: INSTALL.md${NC}"
echo "============================================================"
echo ""
echo -e "${GREEN}Pronto per il test! Buon lavoro! 🚀${NC}"
echo ""
