#!/bin/bash

# Attivare l'ambiente virtuale
source venv/bin/activate

# Eseguire l'applicazione Flask
python app.py

# Disattivare l'ambiente virtuale dopo che l'applicazione termina
deactivate
