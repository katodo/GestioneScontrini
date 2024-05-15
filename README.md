# Gestione Scontrini

Gestione Scontrini è un'applicazione web per la gestione delle spese domestiche. Permette di inserire gli scontrini, organizzarli in un database SQLite, visualizzare le spese e generare un riepilogo mensile per ogni utente.

## Prerequisiti

Prima di iniziare, assicurati di avere installato i seguenti software:

- Python 3.x
- Pip (gestore dei pacchetti di Python)

## Installazione

1. Clona il repository dal tuo account GitHub:

    ```bash
    git clone https://github.com/katodo/GestioneScontrini.git
    cd GestioneScontrini
    ```

2. Crea un ambiente virtuale (opzionale ma consigliato):

    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows usa `venv\Scripts\activate`
    ```

3. Installa le dipendenze:

    ```bash
    pip install -r requirements.txt
    ```

## Avvio dell'applicazione

1. Avvia l'applicazione:

    ```bash
    python app.py
    ```

2. Apri il browser e vai all'indirizzo:

    ```
    http://localhost:5005
    ```

## Utilizzo

### Inserimento delle spese

1. Compila i campi "Utente", "Data", "Importo" e "Esercente".
2. (Opzionale) Carica una foto dello scontrino.
3. Clicca su "Aggiungi" per salvare la spesa.

### Visualizzazione delle spese

La pagina principale mostra una tabella con tutte le spese inserite, ordinate per data. Ogni riga mostra le seguenti informazioni:

- Utente
- Data
- Importo
- Esercente
- Ricevuta (se presente)

Puoi eliminare una spesa cliccando sul pulsante "Elimina" nella riga corrispondente.

### Caricamento della ricevuta

Se non hai caricato una ricevuta al momento dell'inserimento della spesa, puoi farlo in seguito:

1. Clicca sul pulsante "Carica" nella colonna "Ricevuta" della spesa desiderata.
2. Seleziona l'immagine della ricevuta e clicca su "Carica".

### Visualizzazione del riepilogo

1. Clicca su "Riepilogo" nella parte inferiore della pagina.
2. La pagina di riepilogo mostra le spese totali per ogni utente, raggruppate per mese. Ogni mese è colorato con un colore pastello diverso per una visualizzazione più chiara.

## Contatti

Per qualsiasi domanda o problema, puoi contattare Mauro Soligo all'indirizzo email: mauro.soligo@katodo.com

## Licenza

Questo progetto è distribuito sotto la licenza GPLv3. Consulta il file `LICENSE` per ulteriori dettagli.

