#!/bin/bash

# Exit on error
set -e

# Virtual environment directory (local to project folder)
VENV_DIR= 'venv'
# Check if venv exists
if [ ! -d '$VENV_DIR' ]; then
    echo "🔹 Creating virtual environment..."
    python -m venv '$VENV_DIR'
fi

# Activate venv
echo "🔹 Activating virtual environment..."
if [['$OSTYPE' == 'msys']] || [['$OSTYPE' == 'win32']]; then
    source '$VENV_DIR/Scripts/activate'
else
    source '$VENV_DIR/bin/activate'

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "🔹 Installing dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
fi

# Run the main Python script
echo "🔹 lezz gooo"
code .
