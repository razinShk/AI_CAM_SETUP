#!/bin/bash

echo "🏆 SportsCam Laptop Testing Setup"
echo "================================"

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To start testing:"
echo "1. Run: source venv/bin/activate"
echo "2. Run: python laptop_server.py"
echo "3. Open: http://localhost:5000"
echo ""
