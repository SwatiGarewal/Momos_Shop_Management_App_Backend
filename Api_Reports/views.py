from rest_framework.decorators import api_view
from rest_framework.response import Response
from Api_Transactions_Tables.models import *
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from openpyxl import Workbook
from django.utils.timezone import now
from openpyxl.styles import Font, Alignment, Border, Side
from datetime import datetime
from django.db.models import Sum, Count


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

#PDF GENERATER-------------------------
def get_date_range(request):
    from_date = request.GET.get('from_date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if not from_date or not to_date:
        return None, None
    from_date = datetime.strptime(from_date, '%d-%m-%Y').date()
    to_date = datetime.strptime(to_date, '%d-%m-%Y').date()
    return from_date, to_date

def generate_pdf_report(request, from_date=None, to_date=None):
    from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
    to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
    
    sales = OrderSummary.objects.filter(
        date__range=[from_date, to_date]
    ).annotate(items_count=Count('items')).filter(items_count__gt=0)
    
    total_orders = sales.count()
    total_qty = OrderDetails.objects.filter(order__in=sales).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_sale = sales.aggregate(Sum('total_sale_value'))['total_sale_value__sum'] or 0
    total_discount = sales.aggregate(Sum('total_discount_value'))['total_discount_value__sum'] or 0
    total_taxable = sales.aggregate(Sum('total_taxable_value'))['total_taxable_value__sum'] or 0
    total_received = PaymentTransaction.objects.filter(order__in=sales).aggregate(Sum('amount_received'))['amount_received__sum'] or 0
    
    for order in sales:
        order.details = OrderDetails.objects.filter(order=order)
        
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

#EXCEL GENERATER-------------------------------------------
def generate_excel_report(request, from_date, to_date):
    from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
    to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
    
    # Filter out blank orders
    sales = OrderSummary.objects.filter(
        date__range=[from_date, to_date]
    ).annotate(items_count=Count('items')).filter(items_count__gt=0)
    
    for order in sales:
        order.details = OrderDetails.objects.filter(order=order)
        
    total_qty = OrderDetails.objects.filter(order__in=sales).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_sale = sales.aggregate(Sum('total_sale_value'))['total_sale_value__sum'] or 0
    total_discount = sales.aggregate(Sum('total_discount_value'))['total_discount_value__sum'] or 0
    total_taxable = sales.aggregate(Sum('total_taxable_value'))['total_taxable_value__sum'] or 0
    total_received = PaymentTransaction.objects.filter(order__in=sales).aggregate(Sum('amount_received'))['amount_received__sum'] or 0
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"
    
    # STYLES
    title_font = Font(size=18, bold=True)
    subtitle_font = Font(size=14, bold=True)
    bold_font = Font(bold=True)
    center = Alignment(horizontal='center', vertical='center')
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    
    # HEADINGS
    ws.merge_cells('A1:K1')
    ws['A1'] = "MOMO SHOP MANAGEMENT SYSTEM"
    ws['A1'].font = title_font
    ws['A1'].alignment = center
    
    ws.merge_cells('A2:K2')
    ws['A2'] = "SALES REPORT"
    ws['A2'].font = subtitle_font
    ws['A2'].alignment = center
    
    ws.merge_cells('A3:F3')
    ws['A3'] = f"From: {from_date.strftime('%d-%m-%Y')}   To: {to_date.strftime('%d-%m-%Y')}"
    ws.merge_cells('G3:K3')
    ws['G3'] = f"Generated On: {now().strftime('%d-%m-%Y %I:%M %p')}"
    ws['G3'].alignment = Alignment(horizontal='right')
    
    headers = ["S.No", "Order ID", "Date", "Time", "Product Name", "Quantity", "Rate", "Sale", "Discount", "Taxable", "Payment Status"]
    header_row = 5
    for col_num, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header
        cell.font = bold_font
        cell.alignment = center
        cell.border = thin_border
        
# DATA ROWS
    row_num = 6
    for serial_no, sale in enumerate(sales, start=1):
        start_row = row_num
        item_count = len(sale.details)
        end_row = start_row + item_count - 1

        for index, detail in enumerate(sale.details, start=1):
            ws.cell(row=row_num, column=5).value = f"{index}. {detail.product.name}"
            ws.cell(row=row_num, column=6).value = detail.quantity
            ws.cell(row=row_num, column=7).value = float(detail.price)
            
            for col in range(1, 12):
                cell = ws.cell(row=row_num, column=col)
                cell.border = thin_border
                cell.alignment = center
            row_num += 1

        ws.cell(row=start_row, column=1).value = serial_no
        ws.cell(row=start_row, column=2).value = sale.order_id
        ws.cell(row=start_row, column=3).value = sale.date.strftime("%B %d, %Y")
        ws.cell(row=start_row, column=4).value = sale.time.strftime("%I:%M %p")
        
        ws.cell(row=start_row, column=8).value = float(sale.total_sale_value)
        ws.cell(row=start_row, column=9).value = float(sale.total_discount_value)
        ws.cell(row=start_row, column=10).value = float(sale.total_taxable_value)
        ws.cell(row=start_row, column=11).value = sale.payment_status

        if item_count > 1:
            for col in [1, 2, 3, 4, 8, 9, 10, 11]:
                ws.merge_cells(start_row=start_row, start_column=col, end_row=end_row, end_column=col)
                
                for r in range(start_row, end_row + 1):
                    ws.cell(row=r, column=col).alignment = center
    # TOTAL ROW
    total_row = row_num + 1
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=5)
    ws.cell(row=total_row, column=1).value = "TOTAL"
    ws.cell(row=total_row, column=6).value = total_qty
    ws.cell(row=total_row, column=8).value = float(total_sale)
    ws.cell(row=total_row, column=9).value = float(total_discount)
    ws.cell(row=total_row, column=10).value = float(total_taxable)
    
    for col in range(1, 12):
        ws.cell(row=total_row, column=col).font = bold_font
        ws.cell(row=total_row, column=col).alignment = center
        ws.cell(row=total_row, column=col).border = thin_border
        
    # SUMMARY
    summary_row = total_row + 4
    
    ws.merge_cells(start_row=summary_row, start_column=1, end_row=summary_row, end_column=3)
    ws.cell(row=summary_row, column=1).value = "SUMMARY"
    ws.cell(row=summary_row, column=1).font = Font(size=14, bold=True)
    ws.cell(row=summary_row, column=1).alignment = Alignment(horizontal='left', vertical='center')
    
    
    ws.merge_cells(start_row=summary_row + 2, start_column=1, end_row=summary_row + 2, end_column=3)
    ws.cell(row=summary_row + 2, column=1).value = "Total Orders"
    ws.merge_cells(start_row=summary_row + 2, start_column=4, end_row=summary_row + 2, end_column=5)
    ws.cell(row=summary_row + 2, column=4).value = f": {sales.count()}"
    
    ws.merge_cells(start_row=summary_row + 2, start_column=6, end_row=summary_row + 2, end_column=8)
    ws.cell(row=summary_row + 2, column=6).value = "Total Discount"
    ws.merge_cells(start_row=summary_row + 2, start_column=9, end_row=summary_row + 2, end_column=11)
    ws.cell(row=summary_row + 2, column=9).value = f": {float(total_discount)}"

    # Row 2: Total Items Sold & Total Taxable Amount
    ws.merge_cells(start_row=summary_row + 3, start_column=1, end_row=summary_row + 3, end_column=3)
    ws.cell(row=summary_row + 3, column=1).value = "Total Items Sold"
    ws.merge_cells(start_row=summary_row + 3, start_column=4, end_row=summary_row + 3, end_column=5)
    ws.cell(row=summary_row + 3, column=4).value = f": {total_qty}"
    
    ws.merge_cells(start_row=summary_row + 3, start_column=6, end_row=summary_row + 3, end_column=8)
    ws.cell(row=summary_row + 3, column=6).value = "Total Taxable Amount"
    ws.merge_cells(start_row=summary_row + 3, start_column=9, end_row=summary_row + 3, end_column=11)
    ws.cell(row=summary_row + 3, column=9).value = f": {float(total_taxable)}"

    ws.merge_cells(start_row=summary_row + 4, start_column=1, end_row=summary_row + 4, end_column=3)
    ws.cell(row=summary_row + 4, column=1).value = "Total Sale Amount"
    ws.merge_cells(start_row=summary_row + 4, start_column=4, end_row=summary_row + 4, end_column=5)
    ws.cell(row=summary_row + 4, column=4).value = f": {float(total_sale)}"
    
    ws.merge_cells(start_row=summary_row + 4, start_column=6, end_row=summary_row + 4, end_column=8)
    ws.cell(row=summary_row + 4, column=6).value = "Total Received"
    ws.merge_cells(start_row=summary_row + 4, start_column=9, end_row=summary_row + 4, end_column=11)
    ws.cell(row=summary_row + 4, column=9).value = f": {float(total_received)}"

    for r in range(summary_row + 2, summary_row + 5):
        for col in range(1, 6):
            cell = ws.cell(row=r, column=col)
            cell.border = thin_border
            cell.font = bold_font
            cell.alignment = Alignment(horizontal='left', vertical='center')

        for col in range(6, 12):
            cell = ws.cell(row=r, column=col)
            cell.border = thin_border
            if col >= 9:
                cell.font = bold_font
            cell.alignment = Alignment(horizontal='left', vertical='center')
    # COLUMN WIDTHS
    widths = {'A': 8, 'B': 12, 'C': 15, 'D': 15, 'E': 35, 'F': 12, 'G': 12, 'H': 15, 'I': 15, 'J': 15, 'K': 18}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
    wb.save(response)
    return response