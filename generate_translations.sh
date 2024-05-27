#!/bin/bash

# Definisci il percorso del progetto
PROJECT_DIR="$(pwd)"

# Directory dell'ambiente virtuale
VENV_DIR="${PROJECT_DIR}/venv"

# Directory delle traduzioni
TRANSLATIONS_DIR="${PROJECT_DIR}/translations"

# Attiva l'ambiente virtuale
source ${VENV_DIR}/bin/activate

# Assicurati che la directory delle traduzioni esista
mkdir -p $TRANSLATIONS_DIR

# Trova tutti i file Python e HTML escludendo la directory venv
PYTHON_FILES=$(find ${PROJECT_DIR} -type f -name "*.py" -not -path "${VENV_DIR}/*")
HTML_FILES=$(find ${PROJECT_DIR} -type f -name "*.html" -not -path "${VENV_DIR}/*")

# Estrai i messaggi dai file Python e HTML
pybabel extract -F babel.cfg -o ${TRANSLATIONS_DIR}/messages.pot $PYTHON_FILES $HTML_FILES

# Inizializza la directory per la lingua inglese
pybabel init -i ${TRANSLATIONS_DIR}/messages.pot -d ${TRANSLATIONS_DIR} -l en

echo "File di lingua per l'inglese generato con successo in ${TRANSLATIONS_DIR}/en/LC_MESSAGES/messages.po"

# Disattiva l'ambiente virtuale
deactivate
