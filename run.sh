#!/bin/bash

# Exit on error
set -e

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "🔹 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔹 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "🔹 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run the main Python script
echo "🔹 lezz gooo"
code .
