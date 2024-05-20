from flask import Flask, render_template, request, redirect, url_for, session
from flask_babel import Babel, _  # Aggiorna l'importazione
import sqlite3
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

babel = Babel()

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            merchant TEXT NOT NULL,
            description TEXT,
            receipt BLOB,
            receipt_filename TEXT
        )
    ''')
    conn.commit()
    conn.close()

def initialize():
    if not os.path.exists('expenses.db'):
        init_db()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

def get_locale():
    return session.get('lang', 'en')

babel.init_app(app, locale_selector=get_locale)

@app.context_processor
def inject_global_template_variables():
    return dict(get_locale=get_locale)

@app.route('/set_language/<language>')
def set_language(language=None):
    session['lang'] = language
    return redirect(request.referrer)

@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, user, date, amount, merchant, description, receipt, receipt_filename
        FROM expenses
        ORDER BY date DESC
    ''')
    expenses = c.fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses, get_pastel_color=get_pastel_color_by_month)

@app.route('/add', methods=['POST'])
def add_expense():
    user = request.form['user']
    date = request.form['date']
    amount = request.form['amount']
    merchant = request.form['merchant']
    description = request.form['description']
    receipt = request.files.get('receipt')
    receipt_blob = None
    receipt_filename = None

    if receipt:
        receipt_filename = secure_filename(receipt.filename)
        receipt.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename))
        with open(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename), 'rb') as f:
            receipt_blob = f.read()

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO expenses (user, date, amount, merchant, description, receipt, receipt_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user, date, amount, merchant, description, receipt_blob, receipt_filename))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>')
def edit_expense(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT id, user, date, amount, merchant, description, receipt, receipt_filename FROM expenses WHERE id = ?', (id,))
    expense = c.fetchone()
    conn.close()
    return render_template('edit.html', expense=expense)

@app.route('/update/<int:id>', methods=['POST'])
def update_expense(id):
    user = request.form['user']
    date = request.form['date']
    amount = request.form['amount']
    merchant = request.form['merchant']
    description = request.form['description']
    receipt = request.files.get('receipt')

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    
    if receipt:
        receipt_filename = secure_filename(receipt.filename)
        receipt.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename))
        with open(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename), 'rb') as f:
            receipt_blob = f.read()
        c.execute('''
            UPDATE expenses
            SET user = ?, date = ?, amount = ?, merchant = ?, description = ?, receipt = ?, receipt_filename = ?
            WHERE id = ?
        ''', (user, date, amount, merchant, description, receipt_blob, receipt_filename, id))
    else:
        c.execute('''
            UPDATE expenses
            SET user = ?, date = ?, amount = ?, merchant = ?, description = ?
            WHERE id = ?
        ''', (user, date, amount, merchant, description, id))
    
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/summary')
def summary():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    # Recupero dei totali per utente e mese
    c.execute('''
        SELECT user, strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        GROUP BY user, month
        ORDER BY month DESC
    ''')
    summary = c.fetchall()

    # Recupero dei totali per esercente e anno
    merchant_expenses_by_year = get_merchant_expenses_by_year()
    conn.close()

    # Arrotondamento dei totali a due cifre decimali
    summary = [(user, month, round(amount, 2)) for user, month, amount in summary]
    merchant_expenses_by_year = [(year, merchant, round(amount, 2)) for year, merchant, amount in merchant_expenses_by_year]

    return render_template('summary.html', summary=summary, merchant_expenses_by_year=merchant_expenses_by_year, get_pastel_color_by_month=get_pastel_color_by_month, get_pastel_color_by_year=get_pastel_color_by_year)

def get_merchant_expenses_by_year():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        SELECT strftime('%Y', date) as year, merchant, SUM(amount)
        FROM expenses
        GROUP BY year, merchant
        ORDER BY year DESC, SUM(amount) DESC
    ''')
    merchant_expenses_by_year = c.fetchall()
    conn.close()
    return merchant_expenses_by_year

@app.route('/check_merchant', methods=['GET', 'POST'])
def check_merchant():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    if request.method == 'POST':
        year = request.form['year']
        merchant = request.form['merchant']
        
        c.execute('''
            SELECT user, date, amount, description, receipt, receipt_filename
            FROM expenses
            WHERE strftime('%Y', date) = ? AND merchant = ?
            ORDER BY date DESC
        ''', (year, merchant))
        expenses = c.fetchall()
        total_amount = round(sum([expense[2] for expense in expenses]), 2)
        
        c.execute('SELECT DISTINCT strftime("%Y", date) as year FROM expenses ORDER BY year DESC')
        years = [row[0] for row in c.fetchall()]
        c.execute('SELECT DISTINCT merchant FROM expenses ORDER BY merchant')
        merchants = [row[0] for row in c.fetchall()]
        conn.close()
        
        return render_template('check_merchant.html', year=year, merchant=merchant, expenses=expenses, total_amount=total_amount, years=years, merchants=merchants)
    else:
        c.execute('SELECT DISTINCT strftime("%Y", date) as year FROM expenses ORDER BY year DESC')
        years = [row[0] for row in c.fetchall()]
        c.execute('SELECT DISTINCT merchant FROM expenses ORDER BY merchant')
        merchants = [row[0] for row in c.fetchall()]
        conn.close()
        
        return render_template('check_merchant.html', year=None, merchant=None, expenses=None, total_amount=None, years=years, merchants=merchants)

@app.route('/receipt/<int:id>')
def get_receipt(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT receipt, receipt_filename FROM expenses WHERE id = ?', (id,))
    receipt = c.fetchone()
    conn.close()

    if receipt is None:
        return "Receipt not found", 404

    receipt_data, receipt_filename = receipt
    return send_file(io.BytesIO(receipt_data), attachment_filename=receipt_filename, as_attachment=True)

@app.route('/receipt_thumbnail/<int:id>')
def get_receipt_thumbnail(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT receipt FROM expenses WHERE id = ?', (id,))
    receipt = c.fetchone()
    conn.close()

    if receipt is None or receipt[0] is None:
        return "Thumbnail not available", 404

    image = Image.open(io.BytesIO(receipt[0]))
    image.thumbnail((64, 64))
    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/delete_receipt/<int:id>', methods=['POST'])
def delete_receipt(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('UPDATE expenses SET receipt = NULL, receipt_filename = NULL WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('edit_expense', id=id))

def get_pastel_color_by_year(year):
    try:
        year = int(year)
    except ValueError:
        return '#FFFFFF'
    if year % 2 == 0:
        return '#FFDFBA'  # Light Orange for even years
    else:
        return '#BAFFC9'  # Light Green for odd years

def get_pastel_color_by_month(month):
    if '-' not in month:
        print(f"Invalid month format: {month}")
        return '#FFFFFF'
    
    colors = {
        '01': '#FFB3BA',  # January - Light Red
        '02': '#FFDFBA',  # February - Light Orange
        '03': '#FFFFBA',  # March - Light Yellow
        '04': '#BAFFC9',  # April - Light Green
        '05': '#BAE1FF',  # May - Light Blue
        '06': '#E3BAFF',  # June - Light Purple
        '07': '#FFB3FF',  # July - Light Pink
        '08': '#FFC9E3',  # August - Light Magenta
        '09': '#C9FFC9',  # September - Light Lime
        '10': '#C9FFFF',  # October - Light Cyan
        '11': '#E1FFC9',  # November - Light Mint
        '12': '#FFF0BA'   # December - Light Beige
    }
    
    month_part = month.split('-')[1]
    color = colors.get(month_part, '#FFFFFF')
    print(f"Month: {month}, Color: {color}")
    return color

if __name__ == '__main__':
    initialize()
    app.run(debug=True, host='0.0.0.0', port=5005)
