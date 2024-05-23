#!/bin/bash

# Remove any existing virtual environment
if [ -d "venv" ]; then
    rm -rf venv
fi

# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip to the latest version
pip install --upgrade pip

# Install the required dependencies
pip install -r requirements.txt

# Deactivate the virtual environment
deactivate

echo "Dependencies installed successfully."
