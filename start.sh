#!/bin/bash

# Alkemy Print Hub - Startup Script

echo "=========================================="
echo "  ALKEMY PRINT HUB - Starting Server"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

# Create necessary directories
mkdir -p static/uploads/audio
mkdir -p static/uploads/photos
mkdir -p static/uploads/quotes
mkdir -p data

echo ""
echo "🚀 Starting Alkemy Print Hub..."
echo "📍 Server will be available at: http://localhost:5321"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python app.py
