from flask import Blueprint, render_template, request, send_file
from flask_babel import _
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

def get_db_connection():
    conn = sqlite3.connect('expenses.db')
    conn.row_factory = sqlite3.Row
    return conn

@analysis_bp.route('/', methods=['GET', 'POST'])
def analysis():
    conn = get_db_connection()
    
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT familiare FROM expenses")
    familiari = [row['familiare'] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT merchant FROM expenses")
    merchants = [row['merchant'] for row in cur.fetchall()]

    cur.execute("SELECT DISTINCT strftime('%Y', date) as year FROM expenses ORDER BY year DESC")
    years = [row['year'] for row in cur.fetchall()]

    query = "SELECT * FROM expenses WHERE strftime('%Y', date) = ?"
    params = [str(datetime.now().year)]

    if request.method == 'POST':
        familiare = request.form.get('familiare')
        merchant = request.form.get('merchant')
        date_filter = request.form.get('date_filter')
        amount_filter = request.form.get('amount_filter')
        amount_min = request.form.get('amount_min')
        amount_max = request.form.get('amount_max')

        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if familiare:
            query += " AND familiare = ?"
            params.append(familiare)

        if merchant:
            query += " AND merchant = ?"
            params.append(merchant)

        if date_filter:
            if date_filter == 'current_year':
                query += " AND strftime('%Y', date) = ?"
                params.append(str(datetime.now().year))
            elif date_filter == 'before_date':
                date_value = request.form.get('date_value')
                query += " AND date < ?"
                params.append(date_value)
            elif date_filter == 'after_date':
                date_value = request.form.get('date_value')
                query += " AND date > ?"
                params.append(date_value)
            elif date_filter == 'exact_date':
                date_value = request.form.get('date_value')
                query += " AND strftime('%Y-%m', date) = ?"
                params.append(date_value)

        if amount_filter:
            if amount_filter == 'greater_than':
                query += " AND amount > ?"
                params.append(amount_min)
            elif amount_filter == 'less_than':
                query += " AND amount < ?"
                params.append(amount_max)
            elif amount_filter == 'between':
                query += " AND amount BETWEEN ? AND ?"
                params.append(amount_min)
                params.append(amount_max)

    expenses = conn.execute(query, params).fetchall()
    conn.close()

    total_amount = sum([expense['amount'] for expense in expenses])

    return render_template('analysis.html', familiari=familiari, merchants=merchants, years=years, expenses=expenses, total_amount=total_amount)


@analysis_bp.route('/pdf', methods=['POST'])
def generate_pdf():
    conn = get_db_connection()
    
    query = "SELECT * FROM expenses WHERE strftime('%Y', date) = ?"
    params = [str(datetime.now().year)]

    familiare = request.form.get('familiare')
    merchant = request.form.get('merchant')
    date_filter = request.form.get('date_filter')
    amount_filter = request.form.get('amount_filter')
    amount_min = request.form.get('amount_min')
    amount_max = request.form.get('amount_max')

    if request.method == 'POST':
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if familiare:
            query += " AND familiare = ?"
            params.append(familiare)

        if merchant:
            query += " AND merchant = ?"
            params.append(merchant)

        if date_filter:
            if date_filter == 'current_year':
                query += " AND strftime('%Y', date) = ?"
                params.append(str(datetime.now().year))
            elif date_filter == 'before_date':
                date_value = request.form.get('date_value')
                query += " AND date < ?"
                params.append(date_value)
            elif date_filter == 'after_date':
                date_value = request.form.get('date_value')
                query += " AND date > ?"
                params.append(date_value)
            elif date_filter == 'exact_date':
                date_value = request.form.get('date_value')
                query += " AND strftime('%Y-%m', date) = ?"
                params.append(date_value)

        if amount_filter:
            if amount_filter == 'greater_than':
                query += " AND amount > ?"
                params.append(amount_min)
            elif amount_filter == 'less_than':
                query += " AND amount < ?"
                params.append(amount_max)
            elif amount_filter == 'between':
                query += " AND amount BETWEEN ? AND ?"
                params.append(amount_min)
                params.append(amount_max)

    expenses = conn.execute(query, params).fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    data = [[_("Familiare"), _("Date"), _("Amount"), _("Merchant"), _("Description")]]
    for expense in expenses:
        data.append([expense['familiare'], expense['date'], f"{expense['amount']:.2f}", expense['merchant'], expense['description']])

    table = Table(data, colWidths=[4 * cm, 3 * cm, 3 * cm, 4 * cm, 4 * cm])
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

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, attachment_filename='analysis_report.pdf', mimetype='application/pdf')
