from rest_framework.decorators import api_view
from rest_framework.response import Response
from Api_Transactions_Tables.models import *
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from openpyxl import Workbook
from django.utils.timezone import now
from django.db.models import Sum
from openpyxl.styles import Font, Alignment, Border, Side

# Create your views here.

# SALES REPORT---------------------------------------------------
@api_view(['GET'])
def sales_report(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    orders = OrderSummary.objects.filter(date__range=[from_date, to_date])
    total_sales = orders.aggregate(total=Sum('net_amount_payable'))
    return Response({"from_date": from_date,"to_date": to_date,"total_sales": total_sales['total']})

# PRODUCT SALES REPORT-------------------------------------------
@api_view(['GET'])
def product_sales_report(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    products = OrderDetails.objects.filter(date__range=[from_date, to_date])
    report = products.values('product_id','product__name').annotate(total_quantity=Sum('quantity'))
    return Response(report)

# PAYMENT REPORT------------------------------------------------
@api_view(['GET'])
def payment_report(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    payments = PaymentTransaction.objects.filter(date__range=[from_date, to_date])
    report = payments.values('payment_mode__name').annotate(total_amount=Sum('amount_received'))
    return Response(report)

# PIVOT TABLE REPORT--------------------------------------------
@api_view(['GET'])
def pivot_report(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    report = OrderDetails.objects.filter(date__range=[from_date, to_date]).values('product_id','product__name','order__payment_status').annotate(
    total_quantity=Sum('quantity'),
    total_sales=Sum('sale_value'),
    total_taxable=Sum('taxable_value'))
    return Response(report)

#pdf Report Generate--------------------------------
def get_date_range(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if not from_date or not to_date:
        return None, None
    from_date = datetime.strptime(from_date,'%d-%m-%Y').date()
    to_date = datetime.strptime(to_date,'%d-%m-%Y').date()
    return from_date, to_date
def generate_pdf_report(request, from_date=None, to_date=None):
    from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
    to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
    sales = OrderSummary.objects.filter(date__range=[from_date, to_date])
    total_orders = sales.count()
    total_qty = OrderDetails.objects.filter(order__in=sales).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_sale = sales.aggregate(Sum('total_sale_value'))['total_sale_value__sum'] or 0
    total_discount = sales.aggregate(Sum('total_discount_value'))['total_discount_value__sum'] or 0
    total_taxable = sales.aggregate(Sum('total_taxable_value'))['total_taxable_value__sum'] or 0
    total_received = PaymentTransaction.objects.filter(order__in=sales).aggregate(Sum('amount_received'))['amount_received__sum'] or 0
    for order in sales:
        products = OrderDetails.objects.filter(order=order)
        order.rates = ", ".join([str(p.price) for p in products])
    context = {
        'sales': sales,
        'from_date': from_date,
        'to_date': to_date,
        'generated_on': now(),
        'total_orders': total_orders,
        'total_qty': total_qty,
        'total_sale': total_sale,
        'total_discount': total_discount,
        'total_taxable': total_taxable,
        'total_received': total_received,
        'sum_quantity': total_qty,
        'sum_price': OrderDetails.objects.filter(order__in=sales).aggregate(Sum('price'))['price__sum'] or 0,
        'sum_sale': total_sale,
        'sum_discount': total_discount,
        'sum_taxable': total_taxable,
    }
    template = get_template('sales_report.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

#Excel Report Generate---------------------------------------------------------
def generate_excel_report(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    sales = OrderSummary.objects.filter(date__range=[from_date, to_date])
    for order in sales:
        products = OrderDetails.objects.filter(order=order)
        order.product_names = ", ".join([p.product.name for p in products])
        order.quantities = ", ".join([str(p.quantity) for p in products])
        order.rates = ", ".join([str(p.price) for p in products])
    total_qty = (OrderDetails.objects.filter(order__in=sales).aggregate(Sum('quantity'))['quantity__sum']or 0)
    total_sale = (sales.aggregate(Sum('total_sale_value'))['total_sale_value__sum']or 0)
    total_discount = (sales.aggregate(Sum('total_discount_value'))['total_discount_value__sum']or 0)
    total_taxable = (sales.aggregate(Sum('total_taxable_value'))['total_taxable_value__sum']or 0)
    total_received = (PaymentTransaction.objects.filter(date__range=[from_date, to_date]).aggregate(Sum('amount_received'))['amount_received__sum']or 0)
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"
    # STYLES
    title_font = Font(size=18,bold=True)
    subtitle_font = Font(size=14,bold=True)
    bold_font = Font(bold=True)
    center = Alignment(horizontal='center',vertical='center')
    thin_border = Border(left=Side(style='thin'),right=Side(style='thin'),top=Side(style='thin'),bottom=Side(style='thin'))
    # HEADINGS
    ws.merge_cells('A1:J1')
    ws['A1'] = "MOMO SHOP MANAGEMENT SYSTEM"
    ws['A1'].font = title_font
    ws['A1'].alignment = center
    ws.merge_cells('A2:J2')
    ws['A2'] = "SALES REPORT"
    ws['A2'].font = subtitle_font
    ws['A2'].alignment = center
    ws.merge_cells('A3:F3')
    ws['A3'] = (f"From: {from_date.strftime('%d-%m-%Y')}"f"To: {to_date.strftime('%d-%m-%Y')}")
    ws.merge_cells('G3:J3')
    ws['G3'] = (f"Generated On:"f"{now().strftime('%d-%m-%Y %I:%M %p')}")
    ws['G3'].alignment = Alignment(horizontal='right')
    # TABLE HEADER
    headers = [
        "Order ID",
        "Date",
        "Time",
        "Product Name",
        "Quantity",
        "Rate",
        "Sale",
        "Discount",
        "Taxable",
        "Payment Status"
    ]
    header_row = 5
    for col_num, header in enumerate(headers,start=1):
        cell = ws.cell(row=header_row,column=col_num)
        cell.value = header
        cell.font = bold_font
        cell.alignment = center
        cell.border = thin_border
    # DATA ROWS
    row_num = 6
    for item in sales:
        ws.cell(row=row_num,column=1).value = item.order_id
        ws.cell(row=row_num,column=2).value = item.date.strftime("%d-%m-%Y")
        ws.cell(row=row_num,column=3).value = item.time.strftime("%I:%M %p")
        ws.cell(row=row_num,column=4).value = item.product_names
        ws.cell(row=row_num,column=5).value = item.quantities
        ws.cell(row=row_num,column=6).value = item.rates
        ws.cell(row=row_num,column=7).value = float(item.total_sale_value)
        ws.cell(row=row_num,column=8).value = float(item.total_discount_value)
        ws.cell(row=row_num,column=9).value = float(item.total_taxable_value)
        ws.cell(row=row_num,column=10).value = item.payment_status
        for col in range(1, 11):
            ws.cell(row=row_num,column=col).border = thin_border
        row_num += 1
    # TOTAL ROW
    total_row = row_num + 1
    ws.cell(row=total_row,column=3).value = "TOTAL"
    ws.cell(row=total_row,column=5).value = total_qty
    ws.cell(row=total_row,column=7).value = float(total_sale)
    ws.cell(row=total_row,column=8).value = float(total_discount)
    ws.cell(row=total_row,column=9).value = float(total_taxable)
    for col in range(1, 11):
        ws.cell(row=total_row,column=col).font = bold_font
        ws.cell(row=total_row,column=col).alignment = center
        ws.cell(row=total_row,column=col).border = thin_border
    # SUMMARY
    summary_row = total_row + 4
    ws.merge_cells(f'A{summary_row}:J{summary_row}')
    ws[f'A{summary_row}'] = "SUMMARY"
    ws[f'A{summary_row}'].font = Font(size=14,bold=True)
    # ws[f'A{summary_row}'].alignment = center
    ws.cell(row=summary_row + 2,column=1).value = "Total Orders"
    ws.cell(row=summary_row + 2,column=2).value = sales.count()
    ws.cell(row=summary_row + 2,column=6).value = "Total Discount"
    ws.cell(row=summary_row + 2,column=7).value = float(total_discount)
    ws.cell(row=summary_row + 3,column=1).value = "Total Items Sold"
    ws.cell(row=summary_row + 3,column=2).value = total_qty
    ws.cell(row=summary_row + 3,column=6).value = "Total Taxable"
    ws.cell(row=summary_row + 3,column=7).value = float(total_taxable)
    ws.cell(row=summary_row + 4,column=1).value = "Total Sale"
    ws.cell(row=summary_row + 4,column=2).value = float(total_sale)
    ws.cell(row=summary_row + 4,column=6).value = "Total Received"
    ws.cell(row=summary_row + 4,column=7).value = float(total_received)
    # COLUMN WIDTHS
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 35
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 20
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 18
    # DOWNLOAD
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = ('attachment; filename="sales_report.xlsx"')
    wb.save(response)
    return response