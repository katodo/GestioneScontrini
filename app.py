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
            receipt BLOB
        )
    ''')
    conn.commit()
    conn.close()

def initialize():
    if not os.path.exists('expenses.db'):
        init_db()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

def get_pastel_color(month):
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
    return colors.get(month.split('-')[1], '#FFFFFF')

@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT id, user, date, amount, merchant, description, receipt FROM expenses ORDER BY date DESC')
    expenses = c.fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['POST'])
def add_expense():
    user = request.form['user']
    date = request.form['date']
    amount = request.form['amount']
    merchant = request.form['merchant']
    description = request.form['description']
    receipt = request.files.get('receipt')

    if receipt:
        filename = secure_filename(receipt.filename)
        receipt.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
            receipt_blob = f.read()
    else:
        receipt_blob = None

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO expenses (user, date, amount, merchant, description, receipt)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user, date, amount, merchant, description, receipt_blob))
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

@app.route('/add_receipt/<int:id>', methods=['POST'])
def add_receipt(id):
    receipt = request.files['receipt']
    filename = secure_filename(receipt.filename)
    receipt.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
        receipt_blob = f.read()

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        UPDATE expenses
        SET receipt = ?
        WHERE id = ?
    ''', (receipt_blob, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/receipt/<int:id>')
def get_receipt(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT receipt FROM expenses WHERE id = ?', (id,))
    receipt_blob = c.fetchone()[0]
    conn.close()

    if receipt_blob:
        return send_file(
            io.BytesIO(receipt_blob),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='receipt.jpg'
        )
    return "No receipt found"

@app.route('/receipt_thumbnail/<int:id>')
def get_receipt_thumbnail(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT receipt FROM expenses WHERE id = ?', (id,))
    receipt_blob = c.fetchone()[0]
    conn.close()

    if receipt_blob:
        image = Image.open(io.BytesIO(receipt_blob))
        image.thumbnail((100, 100))
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

@app.route('/summary')
def summary():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        SELECT user, strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        GROUP BY user, month
        ORDER BY month ASC
    ''')
    summary = c.fetchall()
    conn.close()
    return render_template('summary.html', summary=summary, get_pastel_color=get_pastel_color)

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

