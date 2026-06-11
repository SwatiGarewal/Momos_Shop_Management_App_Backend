from rest_framework.decorators import api_view
from rest_framework.response import Response
from Api_Transactions_Tables.models import *
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from openpyxl import Workbook
from django.utils.timezone import now
from django.db.models.functions import ExtractMonth
from django.db.models import Sum, Count
import calendar

# Create your views here.

# SALES REPORT---------------------------------------------------
@api_view(['GET'])
def sales_report(request):
    report_type = request.GET.get('type')
    today = timezone.now().date()
    if report_type == 'daily':
        orders = OrderSummary.objects.filter(date=today)
    elif report_type == 'weekly':
        start_week = today - timedelta(days=7)
        orders = OrderSummary.objects.filter(date__gte=start_week)
    elif report_type == 'monthly':
        orders = OrderSummary.objects.filter(date__month=today.month,date__year=today.year)
    else:
        orders = OrderSummary.objects.all()
    total_sales = orders.aggregate(total=Sum('net_amount_payable'))
    return Response({
        "Report Type": report_type,
        "Total Sales": total_sales['total']})

# PRODUCT SALES REPORT-------------------------------------------
@api_view(['GET'])
def product_sales_report(request):
    report_type = request.GET.get('type')
    today = timezone.now().date()
    if report_type == 'daily':
        products = OrderDetails.objects.filter(date=today)
    elif report_type == 'weekly':
        start_week = today - timedelta(days=7)
        products = OrderDetails.objects.filter(date__gte=start_week)
    elif report_type == 'monthly':
        products = OrderDetails.objects.filter(date__month=today.month,date__year=today.year)
    else:
        products = OrderDetails.objects.all()
    report = products.values('product__name').annotate(total_quantity=Sum('quantity'))
    return Response(report)

# PAYMENT REPORT------------------------------------------------
@api_view(['GET'])
def payment_report(request):
    report_type = request.GET.get('type')
    today = timezone.now().date()
    if report_type == 'daily':
        payments = PaymentTransaction.objects.filter(date=today)
    elif report_type == 'weekly':
        start_week = today - timedelta(days=7)
        payments = PaymentTransaction.objects.filter(date__gte=start_week)
    elif report_type == 'monthly':
        payments = PaymentTransaction.objects.filter(date__month=today.month,date__year=today.year)
    else:
        payments = PaymentTransaction.objects.all()
    report = payments.values('payment_mode__name').annotate(total_amount=Sum('amount_received'))
    return Response(report)

# PIVOT TABLE REPORT--------------------------------------------
@api_view(['GET'])
def pivot_report(request):
    report_type = request.GET.get('type', 'yearly')
    report = OrderDetails.objects.values('product_id','order__payment_status').annotate(
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
def generate_pdf_report(request,from_date=None,to_date=None,report_type=None):
    from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
    to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
    if not from_date or not to_date:return HttpResponse("from_date and to_date required",status=400)
    template = get_template('sales_report.html')
    # DAILY REPORT
    if report_type == 'daily':
        sales = OrderDetails.objects.filter(date__range=[from_date, to_date])
        total_orders = (sales.values('order').distinct().count())
        total_qty = (sales.aggregate(Sum('quantity'))['quantity__sum']or 0)
        total_sale = (sales.aggregate(Sum('sale_value'))['sale_value__sum']or 0)
        total_discount = (sales.aggregate(Sum('discount_rupees'))['discount_rupees__sum']or 0)
        total_taxable = (sales.aggregate(Sum('taxable_value'))['taxable_value__sum']or 0)
        total_received = (PaymentTransaction.objects.filter(date__range=[from_date,to_date]).aggregate(Sum('amount_received'))['amount_received__sum']or 0)
        context = {
            'sales': sales,
            'report_type': 'DAILY',
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
            'sum_price':sales.aggregate(Sum('price'))['price__sum']or 0,
            'sum_sale': total_sale,
            'sum_discount':total_discount,
            'sum_taxable':total_taxable,}
    # MONTHLY REPORT
    elif report_type == 'monthly' or report_type is None:
        sales = (OrderDetails.objects.filter(date__range=[from_date,to_date]).values('date').annotate(
        day_total_order=Count('order',distinct=True),
        day_total_quantity=Sum('quantity'),
        day_total_sale=Sum('sale_value'),
        day_total_discount=Sum('discount_rupees'),
        day_total_taxable=Sum('taxable_value')).order_by('date'))
        for item in sales:
            item['day_total_payment_received'] = (PaymentTransaction.objects.filter(
            date=item['date']).aggregate(Sum('amount_received'))['amount_received__sum']or 0)
        total_orders = sum(item['day_total_order']or 0 for item in sales)
        total_qty = sum(item['day_total_quantity']or 0 for item in sales)
        total_sale = sum(item['day_total_sale']or 0 for item in sales)
        total_discount = sum(item['day_total_discount']or 0 for item in sales)
        total_taxable = sum(item['day_total_taxable']or 0 for item in sales)
        total_received = sum(item['day_total_payment_received']or 0 for item in sales)
        context = {
            'sales': sales,
            'report_type': report_type.upper() if report_type else '',
            'from_date': from_date,
            'to_date': to_date,
            'generated_on': now(),
            'total_orders': total_orders,
            'total_qty': total_qty,
            'total_sale': total_sale,
            'total_discount': total_discount,
            'total_taxable': total_taxable,
            'total_received': total_received,
            'sum_day_total_order':total_orders,
            'sum_day_total_quantity':total_qty,
            'sum_day_total_sale':total_sale,
            'sum_day_total_discount':total_discount,
            'sum_day_total_taxable':total_taxable,
            'sum_day_total_payment_received':total_received,
        }
    # YEARLY REPORT
    elif report_type == 'yearly':
        sales = (OrderDetails.objects.filter(date__range=[from_date,to_date]).annotate(
        month=ExtractMonth('date')).values('month').annotate(
        total_order=Count('order',distinct=True),
        total_item_sold=Sum('quantity'),
        total_sale=Sum('sale_value'),
        total_discount=Sum('discount_rupees'),
        total_taxable=Sum('taxable_value')).order_by('month'))
        for item in sales:
            item['month_name'] = calendar.month_name[
            item['month']]
            item['total_payment_received'] = (PaymentTransaction.objects.filter(date__range=[from_date,to_date],date__month=item['month']).aggregate(Sum('amount_received'))['amount_received__sum']or 0)
        context = {
            'sales': sales,
            'report_type': 'YEARLY',
            'from_date': from_date,
            'to_date': to_date,
            'generated_on': now(),
            'sum_total_order': sum(x['total_order']or 0 for x in sales),
            'sum_total_item_sold': sum(x['total_item_sold'] or 0 for x in sales),
            'sum_total_sale':sum(x['total_sale']or 0 for x in sales),
            'sum_total_discount':sum(x['total_discount']or 0 for x in sales),
            'sum_total_taxable': sum(x['total_taxable']or 0 for x in sales),
            'sum_total_payment_received': sum(x['total_payment_received']or 0 for x in sales),}
        context['sum_total_orders'] = context['sum_total_order']
        context['sum_total_qty'] = context['sum_total_item_sold']
    else:
        return HttpResponse("Invalid report type",status=400)
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = ('attachment; ''filename="sales_report.pdf"')
    pisa.CreatePDF(html,dest=response)
    return response
