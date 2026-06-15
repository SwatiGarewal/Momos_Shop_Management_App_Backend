from rest_framework.decorators import api_view
from .serializers import *
from rest_framework.response import Response
from .models import *
from Api_Master_Tables.models import *
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from datetime import datetime


# Create your views here.

# CREATE ORDER-----------------------------------------------------------
@transaction.atomic
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
  if not request.user.is_active:
      return Response({"error": "User account is deactivated"})
  try:
    items = request.data.get('items', [])
    if not items:
      return Response({"error": "No items provided"})
    cash_discount = Decimal(request.data.get('cash_discount', '0.00'))
    # create order summary
    order = OrderSummary.objects.create()
    total_sale = Decimal('0.00')
    total_discount = Decimal('0.00')
    total_taxable = Decimal('0.00')
    # loop through all items
    for item in items:
        product = get_object_or_404(ProductMaster,id=item['product'])
        quantity = int(item['quantity'])
        if quantity <= 0:
          return Response({"error": "Quantity must be greater than 0"})
        discount_percent = Decimal(item.get('discount_percent', '0.00'))
    # create order details
        order_item = OrderDetails.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            discount_percent=discount_percent)
    # totals calculation
        total_sale += order_item.sale_value
        total_discount += order_item.discount_rupees
        total_taxable += order_item.taxable_value
    # update summary table
    order.total_sale_value = total_sale
    order.total_discount_value = total_discount
    order.total_taxable_value = total_taxable
    order.cash_discount = cash_discount
    order.net_amount_payable = (total_taxable - cash_discount)
    order.save()
    return Response({
        "message": "Order Created Successfully",
        "Order ID": order.order_id,
        "Total Sale Value": order.total_sale_value,
        "Total Discount": order.total_discount_value,
        "Total Taxable Value": order.total_taxable_value,
        "Cash Discount": order.cash_discount,
        "Final Bill": order.net_amount_payable})
  except ValidationError as e:
        return Response({"error": str(e)})

# CREATE PAYMENT--------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    if not request.user.is_active:
       return Response({"error": "User account is deactivated"})
    order_id = request.data['order']
    amount_received = Decimal(request.data['amount_received'])
    payment_mode_name = request.data['payment_mode']    
    remarks = request.data.get('remarks','')
    payment_mode = get_object_or_404(PaymentModeMaster,name=payment_mode_name)
    order = get_object_or_404(OrderSummary,order_id=order_id)
    if amount_received > order.net_amount_payable:
       return Response({"error": "Amount exceeds payable bill amount"})
    total_paid = PaymentTransaction.objects.filter(order=order).aggregate(total=Sum('amount_received'))['total'] or Decimal('0.00')
    remaining_amount = (order.net_amount_payable - total_paid)
    if amount_received > remaining_amount:
       return Response({"error": "Payment exceeds remaining amount"})
    existing_payment = PaymentTransaction.objects.filter(order=order).exists()
    if existing_payment:
        return Response({"error": "Payment already done for this order"})
    payment = PaymentTransaction.objects.create(
        order=order,
        amount_received=amount_received,
        payment_mode=payment_mode,
        remarks=remarks)
    new_total_paid = total_paid + amount_received
    if new_total_paid >= order.net_amount_payable:
       order.payment_status = 'Paid'
    else:
       order.payment_status = 'Partial'
    order.save()
    return Response({
        "message": "Payment Successful",
        "Payment ID": payment.payment_id,
        "Order ID": order.order_id,
        "Amount Received": payment.amount_received,
        "Payment Mode": payment.payment_mode.name})

# Order Details------------------------

@api_view(['GET'])
def order_details_list(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    orders = OrderDetails.objects.filter(date__range=[from_date, to_date])
    serializer = OrderDetailsSerializer(orders,many=True)
    return Response(serializer.data)

#Order Summary----------------------------------------
@api_view(['GET'])
def order_summary_list(request, from_date, to_date):
    from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
    to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
    orders = OrderSummary.objects.filter(date__range=[from_date, to_date])
    serializer = OrderSummarySerializer(orders,many=True)
    return Response(serializer.data)