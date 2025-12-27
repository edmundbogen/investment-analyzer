"""
Investment Property Analyzer - Flask Backend
Edmund Bogen Team

This application generates investment property analysis reports
and emails them as PDFs to users.
"""

from flask import Flask, render_template, request, jsonify, send_file, make_response
from flask_cors import CORS
import os
from dotenv import load_dotenv
import smtplib

# Load environment variables from .env file
load_dotenv()
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
CORS(app)

# Brand colors
NAVY = HexColor('#1a3e5c')
CYAN = HexColor('#00a8e1')
WHITE = HexColor('#ffffff')
LIGHT_GRAY = HexColor('#f4f4f4')
DARK_GRAY = HexColor('#333333')
SUCCESS = HexColor('#28a745')
WARNING = HexColor('#ffc107')
DANGER = HexColor('#dc3545')

# Email configuration - Update these with your SMTP settings
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER = os.environ.get('EMAIL_USER', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'Edmund Bogen Team <info@bogenhomes.com>')


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report and return it for download."""
    try:
        data = request.get_json()

        # Generate PDF
        pdf_buffer = generate_pdf(data)

        # Create filename from property address
        property_address = data.get('propertyAddress', 'Investment_Property')
        safe_address = property_address.replace(' ', '_').replace(',', '').replace('.', '')[:30]
        filename = f'Investment_Analysis_{safe_address}.pdf'

        # Return PDF as downloadable file
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def format_currency(amount):
    """Format a number as currency."""
    if amount is None:
        return '$0'
    return f"${amount:,.0f}"


def format_percent(value):
    """Format a decimal as percentage."""
    if value is None:
        return '0.00%'
    return f"{value * 100:.2f}%"


def get_status_color(value, good_threshold, warn_threshold=None, higher_is_better=True):
    """Determine status color based on value."""
    if higher_is_better:
        if value >= good_threshold:
            return SUCCESS
        elif warn_threshold and value >= warn_threshold:
            return WARNING
        return DANGER
    else:
        if value <= good_threshold:
            return SUCCESS
        elif warn_threshold and value <= warn_threshold:
            return WARNING
        return DANGER


def generate_pdf(data):
    """Generate the PDF report."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=NAVY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=DARK_GRAY,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=NAVY,
        spaceBefore=20,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY
    )

    # Build content
    story = []

    # Header
    story.append(Paragraph("THE EDMUND BOGEN TEAM", title_style))
    story.append(Paragraph("AT DOUGLAS ELLIMAN REAL ESTATE", subtitle_style))
    story.append(Spacer(1, 10))

    # Report Title
    story.append(Paragraph("INVESTMENT PROPERTY ANALYSIS", ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=CYAN,
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )))

    # Date and prepared for
    story.append(Paragraph(
        f"Prepared for: {data.get('userName', 'N/A')}<br/>Date: {datetime.now().strftime('%B %d, %Y')}",
        ParagraphStyle('PreparedFor', parent=normal_style, alignment=TA_CENTER, spaceAfter=20)
    ))

    story.append(Spacer(1, 10))

    # Property Summary Section
    story.append(Paragraph("PROPERTY SUMMARY", section_style))

    address = f"{data.get('propertyAddress', 'N/A')}, {data.get('propertyCity', '')}, {data.get('propertyState', 'FL')} {data.get('propertyZip', '')}"

    property_data = [
        ['Address:', address],
        ['Property Type:', data.get('propertyType', 'N/A')],
        ['Units:', str(data.get('numUnits', 1))],
        ['Bedrooms / Bathrooms:', f"{data.get('bedrooms', 'N/A')} / {data.get('bathrooms', 'N/A')}"],
        ['Square Footage:', f"{data.get('sqft', 0):,} SF"],
        ['Year Built:', str(data.get('yearBuilt', 'N/A'))],
        ['Lot Size:', f"{data.get('lotSize', 0)} acres"],
    ]

    property_table = Table(property_data, colWidths=[2*inch, 4.5*inch])
    property_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(property_table)
    story.append(Spacer(1, 15))

    # Financial Snapshot Section
    story.append(Paragraph("FINANCIAL SNAPSHOT", section_style))

    financial_data = [
        ['Purchase Price:', format_currency(data.get('purchasePrice', 0)), 'Monthly Rent:', format_currency(data.get('grossRentMonthly', 0))],
        ['Down Payment:', format_currency(data.get('downPayment', 0)), 'Vacancy Loss:', format_currency(data.get('grossRentMonthly', 0) * data.get('vacancyRate', 0) * -1)],
        ['Closing Costs:', format_currency(data.get('closingCosts', 0)), 'Other Income:', format_currency(data.get('otherIncomeMonthly', 0))],
        ['Rehab Costs:', format_currency(data.get('rehabCosts', 0)), 'Effective Income:', format_currency(data.get('effectiveIncomeMonthly', 0))],
        ['Loan Amount:', format_currency(data.get('loanAmount', 0)), 'Operating Expenses:', format_currency(data.get('totalExpensesMonthly', 0) * -1)],
        ['Total Cash Needed:', format_currency(data.get('totalCashNeeded', 0)), 'NOI (Monthly):', format_currency(data.get('noiMonthly', 0))],
        ['', '', 'Mortgage Payment:', format_currency(data.get('monthlyPayment', 0) * -1)],
    ]

    financial_table = Table(financial_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    financial_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('TEXTCOLOR', (2, 0), (2, -1), NAVY),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, -1), (-1, -1), 1, LIGHT_GRAY),
    ]))
    story.append(financial_table)
    story.append(Spacer(1, 10))

    # Monthly Cash Flow highlight
    monthly_cf = data.get('monthlyCashFlow', 0)
    annual_cf = data.get('annualCashFlow', 0)

    cf_color = SUCCESS if monthly_cf > 0 else DANGER

    cashflow_data = [
        ['MONTHLY CASH FLOW', format_currency(monthly_cf)],
        ['ANNUAL CASH FLOW', format_currency(annual_cf)],
    ]

    cashflow_table = Table(cashflow_data, colWidths=[3.25*inch, 3.25*inch])
    cashflow_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), WHITE),
        ('TEXTCOLOR', (1, 0), (1, -1), WHITE),
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(cashflow_table)
    story.append(Spacer(1, 20))

    # Key Metrics Section
    story.append(Paragraph("KEY INVESTMENT METRICS", section_style))

    cap_rate = data.get('capRate', 0)
    coc = data.get('cashOnCash', 0)
    dscr = data.get('dscr', 0)
    grm = data.get('grm', 0)
    one_pct = data.get('onePercentRule', 0)

    metrics_data = [
        ['Metric', 'Value', 'Target', 'Status'],
        ['Cap Rate', format_percent(cap_rate), '>= 8%', 'GOOD' if cap_rate >= 0.08 else ('AVERAGE' if cap_rate >= 0.06 else 'LOW')],
        ['Cash-on-Cash Return', format_percent(coc), '>= 10%', 'GOOD' if coc >= 0.10 else ('AVERAGE' if coc >= 0.06 else 'LOW')],
        ['Debt Service Coverage Ratio', f"{dscr:.2f}", '>= 1.25x', 'STRONG' if dscr >= 1.25 else ('MARGINAL' if dscr >= 1.0 else 'WEAK')],
        ['Gross Rent Multiplier', f"{grm:.2f}", '<= 12', 'GOOD' if grm <= 12 else 'HIGH'],
        ['1% Rule', format_percent(one_pct), '>= 1%', 'PASS' if one_pct >= 0.01 else 'FAIL'],
    ]

    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.25*inch, 1.25*inch, 1.5*inch])
    metrics_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
    ]))

    # Color code the status column
    for i, row in enumerate(metrics_data[1:], start=1):
        status = row[3]
        if status in ['GOOD', 'STRONG', 'PASS']:
            metrics_table.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), SUCCESS)]))
        elif status in ['AVERAGE', 'MARGINAL']:
            metrics_table.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), WARNING)]))
        else:
            metrics_table.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), DANGER)]))

    story.append(metrics_table)
    story.append(Spacer(1, 20))

    # Quick Rules Check
    story.append(Paragraph("QUICK RULES CHECK", section_style))

    rules_data = [
        ['Rule', 'Result', 'Description'],
        ['1% Rule', 'PASS' if data.get('rule1Pass', False) else 'FAIL', 'Monthly rent should be >= 1% of purchase price'],
        ['2% Rule', 'PASS' if data.get('rule2Pass', False) else 'FAIL', 'Monthly rent should be >= 2% of purchase price (strong cash flow)'],
        ['50% Rule', 'PASS' if data.get('rule50Pass', False) else 'REVIEW', 'Operating expenses should be <= 50% of rent'],
        ['70% Rule (Flip)', 'PASS' if data.get('rule70Pass', False) else 'FAIL', 'Purchase + rehab should be <= 70% of ARV'],
        ['Cash Flow Positive', 'YES' if data.get('cashFlowPositivePass', False) else 'NO', 'Property generates positive cash flow after all expenses'],
    ]

    rules_table = Table(rules_data, colWidths=[1.5*inch, 1*inch, 4*inch])
    rules_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
    ]))

    # Color code results
    for i, row in enumerate(rules_data[1:], start=1):
        result = row[1]
        if result in ['PASS', 'YES']:
            rules_table.setStyle(TableStyle([
                ('TEXTCOLOR', (1, i), (1, i), SUCCESS),
                ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold'),
            ]))
        elif result == 'REVIEW':
            rules_table.setStyle(TableStyle([
                ('TEXTCOLOR', (1, i), (1, i), WARNING),
                ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold'),
            ]))
        else:
            rules_table.setStyle(TableStyle([
                ('TEXTCOLOR', (1, i), (1, i), DANGER),
                ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold'),
            ]))

    story.append(rules_table)
    story.append(Spacer(1, 20))

    # Deal Verdict
    verdict = data.get('verdict', 'REVIEW')
    verdict_color = SUCCESS if verdict == 'STRONG BUY' else (CYAN if verdict == 'CONSIDER' else (WARNING if verdict == 'REVIEW' else DANGER))

    verdict_data = [['DEAL VERDICT', verdict]]
    verdict_table = Table(verdict_data, colWidths=[3.25*inch, 3.25*inch])
    verdict_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('FONTSIZE', (1, 0), (1, 0), 18),
        ('TEXTCOLOR', (0, 0), (0, 0), WHITE),
        ('TEXTCOLOR', (1, 0), (1, 0), verdict_color),
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 30))

    # Financing Details
    story.append(Paragraph("FINANCING DETAILS", section_style))

    financing_data = [
        ['Interest Rate:', format_percent(data.get('interestRate', 0))],
        ['Loan Term:', f"{data.get('loanTermYears', 30)} years"],
        ['Down Payment:', f"{data.get('downPaymentPercent', 0) * 100:.0f}%"],
        ['LTV Ratio:', f"{(1 - data.get('downPaymentPercent', 0)) * 100:.0f}%"],
        ['Monthly P&I:', format_currency(data.get('monthlyPayment', 0))],
        ['Annual Debt Service:', format_currency(data.get('annualDebtService', 0))],
    ]

    financing_table = Table(financing_data, colWidths=[2*inch, 2*inch])
    financing_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), NAVY),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(financing_table)
    story.append(Spacer(1, 30))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=5
    )

    story.append(Paragraph("─" * 80, footer_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Compliments of The Edmund Bogen Team at Douglas Elliman Real Estate", footer_style))
    story.append(Paragraph("From Palm Beach to Miami, we can help you find your next investment property.", footer_style))
    story.append(Paragraph("www.bogenhomes.com", ParagraphStyle('FooterLink', parent=footer_style, textColor=CYAN)))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "DISCLAIMER: This analysis is for informational purposes only. Actual results may vary. "
        "Please consult with qualified professionals before making investment decisions.",
        ParagraphStyle('Disclaimer', parent=footer_style, fontSize=7, textColor=HexColor('#888888'))
    ))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return buffer


def send_email(data, pdf_buffer):
    """Send the PDF report via email."""
    user_email = data.get('userEmail')
    user_name = data.get('userName')
    property_address = data.get('propertyAddress', 'Investment Property')

    if not EMAIL_USER or not EMAIL_PASSWORD:
        # If email not configured, just log and return success (for testing)
        print(f"Email would be sent to: {user_email}")
        print(f"PDF generated for: {property_address}")
        return True

    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = user_email
    msg['Subject'] = f'Your Investment Property Analysis - {property_address}'

    # Email body
    body = f"""
Dear {user_name},

Thank you for using the Edmund Bogen Team Investment Property Analyzer!

Please find attached your comprehensive investment analysis for:
{property_address}

This report includes:
• Property summary and financial snapshot
• Key investment metrics (Cap Rate, Cash-on-Cash, DSCR, GRM)
• Quick rules check (1%, 2%, 50%, 70% rules)
• Cash flow analysis
• Deal verdict and recommendation

If you have any questions about this analysis or would like to discuss investment opportunities in South Florida, please don't hesitate to reach out.

Best regards,

The Edmund Bogen Team
Douglas Elliman Real Estate
www.bogenhomes.com

---
From Palm Beach to Miami, we can help you find your next investment property.
    """

    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF
    pdf_attachment = MIMEApplication(pdf_buffer.read(), _subtype='pdf')
    safe_address = property_address.replace(' ', '_').replace(',', '')[:30]
    pdf_attachment.add_header(
        'Content-Disposition',
        'attachment',
        filename=f'Investment_Analysis_{safe_address}.pdf'
    )
    msg.attach(pdf_attachment)

    # Send email
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {user_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise


if __name__ == '__main__':
    app.run(debug=True, port=5000)
