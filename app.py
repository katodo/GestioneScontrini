from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, flash
import csv
import zipfile
from flask_babel import Babel, _
import sqlite3
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

babel = Babel(app)

def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
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
    conn.commit()
    conn.close()

def initialize():
    if not os.path.exists('expenses.db'):
        init_db()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

@babel.localeselector
def get_locale():
    return session.get('lang', 'en')

@app.context_processor
def inject_global_template_variables():
    return dict(
        get_locale=get_locale,
        get_pastel_color_by_month=get_pastel_color_by_month,
        get_pastel_color_by_year=get_pastel_color_by_year
    )

@app.route('/set_language/<language>')
def set_language(language=None):
    session['lang'] = language
    return redirect(request.referrer)

def get_pastel_color_by_month(date_str):
    try:
        month = date_str.split('-')[1]
    except IndexError:
        print(f"Invalid date format: {date_str}")
        return "#FFFFFF"  # Default to white
    
    pastel_colors = {
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
    
    return pastel_colors.get(month, "#FFFFFF")  # Default to white if month not found

def get_pastel_color_by_year(year):
    try:
        year = int(year)
    except ValueError:
        return "#FFFFFF"
    if year % 2 == 0:
        return '#FFDFBA'  # Light Orange for even years
    else:
        return '#BAFFC9'  # Light Green for odd years

@app.route('/')
def index():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, familiare, date, amount, merchant, description, receipt, receipt_filename
        FROM expenses
        ORDER BY date DESC
    ''')
    expenses = c.fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['POST'])
def add_expense():
    familiare = request.form['familiare']
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
        INSERT INTO expenses (familiare, date, amount, merchant, description, receipt, receipt_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (familiare, date, amount, merchant, description, receipt_blob, receipt_filename))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>')
def edit_expense(id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT id, familiare, date, amount, merchant, description, receipt, receipt_filename FROM expenses WHERE id = ?', (id,))
    expense = c.fetchone()
    conn.close()
    return render_template('edit.html', expense=expense)

@app.route('/update/<int:id>', methods=['POST'])
def update_expense(id):
    familiare = request.form['familiare']
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
            SET familiare = ?, date = ?, amount = ?, merchant = ?, description = ?, receipt = ?, receipt_filename = ?
            WHERE id = ?
        ''', (familiare, date, amount, merchant, description, receipt_blob, receipt_filename, id))
    else:
        c.execute('''
            UPDATE expenses
            SET familiare = ?, date = ?, amount = ?, merchant = ?, description = ?
            WHERE id = ?
        ''', (familiare, date, amount, merchant, description, id))
    
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

@app.route('/receipt/<filename>')
def get_receipt(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/summary')
def summary():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    # Recupero dei totali per familiare e mese
    c.execute('''
        SELECT familiare, strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses
        GROUP BY familiare, month
        ORDER BY month DESC
    ''')
    summary = c.fetchall()

    # Recupero dei totali per esercente e anno
    merchant_expenses_by_year = get_merchant_expenses_by_year()
    conn.close()

    # Arrotondamento dei totali a due cifre decimali
    summary = [(familiare, month, round(amount, 2)) for familiare, month, amount in summary]
    merchant_expenses_by_year = [(year, merchant, round(amount, 2)) for year, merchant, amount in merchant_expenses_by_year]

    return render_template('summary.html', summary=summary, merchant_expenses_by_year=merchant_expenses_by_year)

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

@app.route('/generate_pdf/<table>')
def generate_pdf(table):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica", 10)

    data = []
    row_colors = []
    
    if table == 'summary':
        c.execute('''
            SELECT familiare, strftime('%Y-%m', date) as month, SUM(amount)
            FROM expenses
            GROUP BY familiare, month
            ORDER BY month DESC
        ''')
        rows = c.fetchall()

        data.append([_("Familiare"), _("Month"), _("Total Amount")])
        
        for row in rows:
            data.append([row[0], row[1], round(row[2], 2)])
            row_colors.append([get_pastel_color_by_month(row[1]), get_pastel_color_by_month(row[1]), get_pastel_color_by_month(row[1])])

    elif table == 'merchant_expenses':
        c.execute('''
            SELECT strftime('%Y', date) as year, merchant, SUM(amount)
            FROM expenses
            GROUP BY year, merchant
            ORDER BY year DESC, SUM(amount) DESC
        ''')
        rows = c.fetchall()

        data.append([_("Year"), _("Merchant"), _("Total Amount")])
        
        for row in rows:
            data.append([row[0], row[1], round(row[2], 2)])
            row_colors.append([get_pastel_color_by_year(row[0]), get_pastel_color_by_year(row[0]), get_pastel_color_by_year(row[0])])

    table = Table(data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWHEIGHT', (0, 0), (-1, -1), 0.8 * cm)
    ]))

    for i, row_color in enumerate(row_colors, start=1):
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, i), (-1, i), row_color[0])
        ]))

    width, height = A4
    table.wrapOn(p, width - 4 * cm, height - 4 * cm)
    table.drawOn(p, 2 * cm, height - 1 * cm - len(data) * 0.8 * cm)

    p.showPage()
    p.save()
    buffer.seek(0)
    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, attachment_filename=filename, mimetype='application/pdf')


@app.route('/export_archive')
def export_archive():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT id, familiare, date, amount, merchant, description, receipt_filename FROM expenses')
    expenses = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Familiare', 'Date', 'Amount', 'Merchant', 'Description', 'Receipt Filename'])
    for row in expenses:
        writer.writerow([f'|{str(item)}|' if isinstance(item, str) and idx != 6 else item for idx, item in enumerate(row)])

    output.seek(0)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('expenses.csv', output.getvalue())
        for expense in expenses:
            if expense[6]:  # receipt_filename
                with open(os.path.join(app.config['UPLOAD_FOLDER'], expense[6]), 'rb') as f:
                    zip_file.writestr(expense[6], f.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', attachment_filename='expenses.zip', as_attachment=True)


@app.route('/import_archive', methods=['POST'])
def import_archive():
    if 'csvFile' not in request.files:
        flash(_('No file part'))
        return redirect(url_for('index'))

    file = request.files['csvFile']
    if file.filename == '':
        flash(_('No selected file'))
        return redirect(url_for('index'))

    if file and file.filename.endswith('.zip'):
        zip_file = zipfile.ZipFile(file)
        csv_file = zip_file.open('expenses.csv')
        stream = io.StringIO(csv_file.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        next(csv_input)  # Skip the header row

        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        for row in csv_input:
            familiare, date, amount, merchant, description, receipt_filename = row[1].strip('|'), row[2].strip('|'), float(row[3]), row[4].strip('|'), row[5].strip('|'), row[6]

            # Verifica se il record esiste già
            c.execute('''
                SELECT COUNT(*)
                FROM expenses
                WHERE date = ? AND merchant = ? AND amount = ?
            ''', (date, merchant, amount))
            if c.fetchone()[0] == 0:  # Se non esiste
                receipt_blob = None
                if receipt_filename:
                    with zip_file.open(receipt_filename) as f:
                        receipt_blob = f.read()
                    with open(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename), 'wb') as out_file:
                        out_file.write(receipt_blob)

                c.execute('''
                    INSERT INTO expenses (familiare, date, amount, merchant, description, receipt, receipt_filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (familiare, date, amount, merchant, description, receipt_blob, receipt_filename))
        conn.commit()
        conn.close()

        flash(_('File successfully imported'))
        return redirect(url_for('index'))

    flash(_('Invalid file format'))
    return redirect(url_for('index'))

@app.route('/check_merchant', methods=['GET', 'POST'])
def check_merchant():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    if request.method == 'POST':
        year = request.form['year']
        merchant = request.form['merchant']
        
        c.execute('''
            SELECT familiare, date, amount, description, receipt, receipt_filename
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


if __name__ == '__main__':
    initialize()
    app.run(debug=True, host='0.0.0.0', port=5005)
