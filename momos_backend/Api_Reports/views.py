from rest_framework.decorators import api_view
from rest_framework.response import Response
from Api_Transactions_Tables.models import *
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

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
    report = OrderDetails.objects.values(
        'product__name',
        'order__payment_status'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('taxable_value')
    )
    return Response(report)