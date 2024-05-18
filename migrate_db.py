import sqlite3

def migrate_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    # Verifica se le colonne esistono già
    c.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'description' not in columns:
        # Aggiungi la colonna "description" alla tabella "expenses"
        c.execute("ALTER TABLE expenses ADD COLUMN description TEXT")
        print("Colonna 'description' aggiunta con successo alla tabella 'expenses'.")
    else:
        print("La colonna 'description' esiste già nella tabella 'expenses'.")
    
    if 'receipt_filename' not in columns:
        # Aggiungi la colonna "receipt_filename" alla tabella "expenses"
        c.execute("ALTER TABLE expenses ADD COLUMN receipt_filename TEXT")
        print("Colonna 'receipt_filename' aggiunta con successo alla tabella 'expenses'.")
    else:
        print("La colonna 'receipt_filename' esiste già nella tabella 'expenses'.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_db()
