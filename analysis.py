from flask import Blueprint, render_template, request, send_file
from flask_babel import _
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
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

    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

    query = "SELECT * FROM expenses WHERE strftime('%Y', date) = ?"
    params = [str(datetime.now().year)]

    if request.method == 'POST':
        familiari_selected = request.form.getlist('familiare')
        merchants_selected = request.form.getlist('merchant')
        date_start = request.form.get('date_start')
        date_end = request.form.get('date_end')
        years_selected = request.form.getlist('years')
        months_selected = request.form.getlist('months')
        amount_filter = request.form.get('amount_filter')
        amount_value = request.form.get('amount_value')

        query = "SELECT * FROM expenses WHERE 1=1"
        params = []

        if familiari_selected:
            query += " AND familiare IN ({})".format(','.join('?' for _ in familiari_selected))
            params.extend(familiari_selected)

        if merchants_selected:
            query += " AND merchant IN ({})".format(','.join('?' for _ in merchants_selected))
            params.extend(merchants_selected)

        if date_start and date_end:
            query += " AND date BETWEEN ? AND ?"
            params.append(date_start)
            params.append(date_end)
        elif date_end:
            query += " AND date <= ?"
            params.append(date_end)
        elif date_start:
            query += " AND date >= ?"
            params.append(date_start)

        if years_selected:
            query += " AND strftime('%Y', date) IN ({})".format(','.join('?' for _ in years_selected))
            params.extend(years_selected)

        if months_selected:
            query += " AND strftime('%m', date) IN ({})".format(','.join('?' for _ in months_selected))
            params.extend(months_selected)

        if amount_filter and amount_value:
            if amount_filter == 'greater_than':
                query += " AND amount > ?"
                params.append(amount_value)
            elif amount_filter == 'less_than':
                query += " AND amount < ?"
                params.append(amount_value)

    expenses = conn.execute(query, params).fetchall()
    conn.close()

    total_amount = sum([expense['amount'] for expense in expenses])

    return render_template('analysis.html', familiari=familiari, merchants=merchants, years=years, months=months, expenses=expenses, total_amount=total_amount)


@analysis_bp.route('/pdf', methods=['POST'])
def generate_pdf():
    conn = get_db_connection()
    
    familiari_selected = request.form.getlist('familiare')
    merchants_selected = request.form.getlist('merchant')
    date_start = request.form.get('date_start')
    date_end = request.form.get('date_end')
    years_selected = request.form.getlist('years')
    months_selected = request.form.getlist('months')
    amount_filter = request.form.get('amount_filter')
    amount_value = request.form.get('amount_value')

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if familiari_selected:
        query += " AND familiare IN ({})".format(','.join('?' for _ in familiari_selected))
        params.extend(familiari_selected)

    if merchants_selected:
        query += " AND merchant IN ({})".format(','.join('?' for _ in merchants_selected))
        params.extend(merchants_selected)

    if date_start and date_end:
        query += " AND date BETWEEN ? AND ?"
        params.append(date_start)
        params.append(date_end)
    elif date_end:
        query += " AND date <= ?"
        params.append(date_end)
    elif date_start:
        query += " AND date >= ?"
        params.append(date_start)

    if years_selected:
        query += " AND strftime('%Y', date) IN ({})".format(','.join('?' for _ in years_selected))
        params.extend(years_selected)

    if months_selected:
        query += " AND strftime('%m', date) IN ({})".format(','.join('?' for _ in months_selected))
        params.extend(months_selected)

    if amount_filter and amount_value:
        if amount_filter == 'greater_than':
            query += " AND amount > ?"
            params.append(amount_value)
        elif amount_filter == 'less_than':
            query += " AND amount < ?"
            params.append(amount_value)

    expenses = conn.execute(query, params).fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    styleN = styles["BodyText"]

    data = [[_("Familiare"), _("Date"), _("Amount"), _("Merchant"), _("Description")]]
    for expense in expenses:
        data.append([
            expense['familiare'],
            expense['date'],
            f"{expense['amount']:.2f}",
            expense['merchant'],
            Paragraph(expense['description'], styleN)
        ])

    table = Table(data, colWidths=[4 * cm, 2.5 * cm, 2.5 * cm, 4 * cm, 8 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, attachment_filename='analysis_report.pdf', mimetype='application/pdf')
