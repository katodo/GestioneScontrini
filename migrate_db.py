import sqlite3

def migrate_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    # Verifica se la colonna 'user' esiste già
    c.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in c.fetchall()]
    if 'user' in columns:
        # Rinominare la tabella originale
        c.execute("ALTER TABLE expenses RENAME TO expenses_old")
        
        # Creare la nuova tabella con la struttura aggiornata
        c.execute('''
            CREATE TABLE expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                familiare TEXT NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                merchant TEXT NOT NULL,
                description TEXT,
                receipt BLOB,
                receipt_filename TEXT
            )
        ''')
        
        # Copiare i dati dalla vecchia tabella alla nuova tabella
        c.execute('''
            INSERT INTO expenses (id, familiare, date, amount, merchant, description, receipt, receipt_filename)
            SELECT id, user, date, amount, merchant, description, receipt, receipt_filename
            FROM expenses_old
        ''')
        
        # Eliminare la vecchia tabella
        c.execute("DROP TABLE expenses_old")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_db()
