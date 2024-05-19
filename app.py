from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import sqlite3
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

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

@app.route('/check_merchant', methods=['GET', 'POST'])
def check_merchant():
    if request.method == 'POST':
        year = request.form['year']
        merchant = request.form['merchant']
        
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('''
            SELECT user, date, amount, description, receipt, receipt_filename
            FROM expenses
            WHERE strftime('%Y', date) = ? AND merchant = ?
            ORDER BY date DESC
        ''', (year, merchant))
        expenses = c.fetchall()
        total_amount = sum([expense[2] for expense in expenses])
        conn.close()
        
        return render_template('check_merchant.html', year=year, merchant=merchant, expenses=expenses, total_amount=total_amount)
    else:
        return render_template('check_merchant.html', year=None, merchant=None, expenses=None, total_amount=None)

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
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        print(f"Attempting to delete record with id: {id}")
        c.execute('DELETE FROM expenses WHERE id = ?', (id,))
        if c.rowcount == 0:
            print(f"No record found with id: {id}")
        conn.commit()
        conn.close()
        print(f"Record with id: {id} deleted successfully")
    except Exception as e:
        print(f"Error deleting record with id: {id}, error: {e}")
    return redirect(url_for('index'))

@app.route('/receipt/<int:id>')
def get_receipt(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT receipt, receipt_filename FROM expenses WHERE id = ?', (id,))
    row = c.fetchone()
    receipt_blob, receipt_filename = row
    conn.close()

    if receipt_blob:
        if receipt_filename.endswith('.pdf'):
            return send_file(
                io.BytesIO(receipt_blob),
                mimetype='application/pdf',
                as_attachment=False,
                download_name=receipt_filename
            )
        else:
            return send_file(
                io.BytesIO(receipt_blob),
                mimetype='image/jpeg',
                as_attachment=False,
                download_name=receipt_filename
            )
    return "No receipt found"

@app.route('/receipt_thumbnail/<int:id>')
def get_receipt_thumbnail(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT receipt, receipt_filename FROM expenses WHERE id = ?', (id,))
    row = c.fetchone()
    receipt_blob, receipt_filename = row
    conn.close()

    if receipt_blob and receipt_filename.endswith(('.jpg', '.jpeg', '.png')):
        image = Image.open(io.BytesIO(receipt_blob))
        image.thumbnail((64, 64))
        thumbnail_io = io.BytesIO()
        image.save(thumbnail_io, format='JPEG')
        thumbnail_io.seek(0)

        return send_file(
            thumbnail_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='thumbnail.jpg'
        )
    return "No thumbnail available"

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

@app.route('/summary')
def summary():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        SELECT user, strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        GROUP BY user, month
        ORDER BY month DESC
    ''')
    summary = c.fetchall()

    merchant_expenses_by_year = get_merchant_expenses_by_year()
    conn.close()
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

# Rest of the code remains the same


@app.route('/delete_receipt/<int:id>', methods=['POST'])
def delete_receipt(id):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        print(f"Attempting to delete receipt for record with id: {id}")
        c.execute('''
            UPDATE expenses
            SET receipt = NULL, receipt_filename = NULL
            WHERE id = ?
        ''', (id,))
        conn.commit()
        conn.close()
        print(f"Receipt for record with id: {id} deleted successfully")
    except Exception as e:
        print(f"Error deleting receipt for record with id: {id}, error: {e}")
    return redirect(url_for('edit_expense', id=id))


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT user FROM expenses')
    users = [row[0] for row in c.fetchall()]
    c.execute('SELECT DISTINCT merchant FROM expenses')
    merchants = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify({'users': users, 'merchants': merchants})

if __name__ == '__main__':
    initialize()
    app.run(debug=True, host='0.0.0.0', port=5005)
