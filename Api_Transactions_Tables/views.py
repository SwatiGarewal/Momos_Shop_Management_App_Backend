from rest_framework.decorators import api_view
from .serializers import *
from rest_framework.response import Response
from .models import *
from Api_Master_Tables.models import *
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from datetime import datetime


# Create your views here.

# HELPER: Check active customer/user by id --------------------------------
def get_valid_user(request):
    user_id = request.session.get('user_master_id')
    if not user_id:
        return None, Response({"error": "Please login first"}, status=401)
    user = UserMaster.objects.filter(id=user_id, active_status=True).first()
    if not user:
        return None, Response({"error": "Invalid or inactive user"}, status=403)
    return user, None


# CREATE ORDER-----------------------------------------------------------
@transaction.atomic
@api_view(['POST'])
def create_order(request):
  current_user, error = get_valid_user(request)
  if error:
      return error
  try:
    items = request.data.get('items', [])
    if not items:
      return Response({"error": "No items provided"})
    cash_discount = Decimal(request.data.get('cash_discount', '0.00'))
    # create order summary
    order = OrderSummary.objects.create(created_by=current_user)
    created_items = []
    # loop through all items
    for item in items:
        product = get_object_or_404(ProductMaster,id=item['product'])
        quantity = int(item['quantity'])
        if quantity <= 0:
          return Response({"error": "Quantity must be greater than 0"})
        discount_percent = Decimal(item.get('discount_percent', '0.00'))
        if product.stock < quantity:
          return Response({"error": "Not enough stock"})
        product.stock -= quantity
        product.save()
    # create order details
        order_item = OrderDetails.objects.create(
         order=order,
         product=product,
         quantity=quantity,
         discount_percent=discount_percent)
        created_items.append({
         "order_detail_id": order_item.order_details_id,
         "product_id": order_item.product.id,
         "product_name": order_item.product.name,
         "quantity": order_item.quantity,
         "price": order_item.price,
         "sale_value": order_item.sale_value,
         "discount_percent": order_item.discount_percent,
         "discount_rupees": order_item.discount_rupees,
         "taxable_value": order_item.taxable_value})
    # update summary table
    order.cash_discount = cash_discount
    order.save()
    recalculate_order(order)
    return Response({
    "message": "Order Created Successfully",
    "order_id": order.order_id,
    "payment_status": order.payment_status,
    "total_items": len(created_items),
    "items": created_items,
    "total_sale_value": order.total_sale_value,
    "total_discount": order.total_discount_value,
    "total_taxable_value": order.total_taxable_value,
    "cash_discount": order.cash_discount,
    "final_bill": order.net_amount_payable,
    "balance": order.net_amount_payable})
  except ValidationError as e:
        return Response({"error": str(e)})

# ORDER SUMMARY RECALCULATION --------------------------------------------
def recalculate_order(order):
    total_sale = order.items.aggregate(total=Sum('sale_value'))['total'] or Decimal('0.00')
    total_discount = order.items.aggregate(total=Sum('discount_rupees'))['total'] or Decimal('0.00')
    total_taxable = order.items.aggregate(total=Sum('taxable_value'))['total'] or Decimal('0.00')
    order.total_sale_value = total_sale
    order.total_discount_value = total_discount
    order.total_taxable_value = total_taxable
    order.net_amount_payable = (total_taxable - order.cash_discount)
    order.save()

# STOCK ADJUSTMENT --------------------------------------------------------
def adjust_stock(old_product, new_product, old_quantity, new_quantity):
    # Same Product
    if old_product.id == new_product.id:
        difference = new_quantity - old_quantity
        if difference > 0:
            if old_product.stock < difference:
                raise ValidationError(f"Not enough stock for {old_product.name}")
            old_product.stock -= difference
        elif difference < 0:
            old_product.stock += abs(difference)
        old_product.save()
    # Product Changed
    else:
        if new_product.stock < new_quantity:
            raise ValidationError(f"Not enough stock for {new_product.name}")
        old_product.stock += old_quantity
        new_product.stock -= new_quantity
        old_product.save()
        new_product.save()

# # UPDATE ORDER ITEM -------------------------------------------------------
# @api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# @transaction.atomic
# def update_order_detail(request, order_id):
#     order_item = get_object_or_404(OrderDetails,order_details_id=id)
#     old_product = order_item.product
#     old_quantity = order_item.quantity
#     new_product_id = request.data.get("product",old_product.id)
#     new_product = get_object_or_404(ProductMaster,id=new_product_id)
#     new_quantity = int(request.data.get("quantity",old_quantity))
#     new_discount = Decimal(request.data.get("discount_percent",order_item.discount_percent))
#     if new_quantity <= 0:
#         return Response({"error": "Quantity must be greater than zero"})
#     # SAME PRODUCT
#     try:
#       adjust_stock(
#         old_product,
#         new_product,
#         old_quantity,
#         new_quantity)
#     except ValidationError as e:
#        return Response({"error": str(e)})
#     order_item.product = new_product
#     order_item.quantity = new_quantity
#     order_item.discount_percent = new_discount
#     order_item.save()
#     recalculate_order(order_item.order)
#     order_item.order.refresh_from_db()
#     return Response({
#     "message": "Order Updated Successfully",
#     "order_id":order_item.order.order_id,
#     "order_detail_id": order_item.order_details_id,
#     "product":order_item.product.name,
#     "quantity":order_item.quantity,
#     "net_amount":order_item.order.net_amount_payable,
#     "stock_remaining": order_item.product.stock})

# UPDATE COMPLETE ORDER --------------------------------------------------
@api_view(['PUT'])
@transaction.atomic
def update_order(request, order_id):
    current_user, error = get_valid_user(request)
    if error:
        return error
    order = get_object_or_404(OrderSummary,order_id=order_id)
    items = request.data.get("items", [])
    deleted_items = request.data.get("deleted_items", [])
    cash_discount = Decimal(request.data.get("cash_discount",order.cash_discount))
    order.cash_discount = cash_discount
    order.save()
    existing_items = {
        item.order_details_id: item
        for item in order.items.all()}
        # UPDATE EXISTING ITEMS 
    for item in items:
        order_detail_id = item.get("order_detail_id")
        # Existing Item
        if order_detail_id:
            order_item = existing_items.get(order_detail_id)
            if not order_item:
                return Response({"error": f"Order Detail {order_detail_id} not found"})
            old_product = order_item.product
            old_quantity = order_item.quantity
            new_product = get_object_or_404(ProductMaster,id=item["product"])
            new_quantity = int(item.get("quantity",order_item.quantity))
            new_discount = Decimal(item.get("discount_percent", order_item.discount_percent))
            try:
               adjust_stock(old_product,new_product,old_quantity,new_quantity)
            except ValidationError as e:
                return Response({"error": str(e)})
            # Update Order Item
            order_item.product = new_product
            order_item.quantity = new_quantity
            order_item.discount_percent = new_discount
            order_item.save()
    # ADD NEW ITEMS ----------------
    for item in items:
       if item.get("order_detail_id"):
        continue
       product = get_object_or_404(ProductMaster,id=item["product"])
       quantity = int(item["quantity"])
       discount = Decimal(item.get("discount_percent", 0))
    # Check if product already exists in this order
       existing_item = OrderDetails.objects.filter(order=order,product=product).first()
    # Product already exists -> Increase quantity
       if existing_item:
        try:
            adjust_stock(
                existing_item.product,
                existing_item.product,
                existing_item.quantity,
                existing_item.quantity + quantity)
        except ValidationError as e:
            return Response({"error": str(e)})
        existing_item.quantity += quantity
        existing_item.discount_percent = discount
        existing_item.save()
    # New Product
       else:
         if product.stock < quantity:
            return Response({"error": f"Not enough stock for {product.name}"})
         product.stock -= quantity
         product.save()
         OrderDetails.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            discount_percent=discount)
    # DELETE ITEMS ----------------
    for detail_id in deleted_items:
        order_item = get_object_or_404(OrderDetails,order_details_id=detail_id,order=order)
        product = order_item.product
        product.stock += order_item.quantity
        product.save()
        order_item.delete()
    # RECALCULATE ORDER ----------------
    recalculate_order(order)
    order.refresh_from_db()
    updated_items = []
    for item in order.items.all():
        updated_items.append({
        "order_detail_id": item.order_details_id,
        "product_id": item.product.id,
        "product_name": item.product.name,
        "quantity": item.quantity,
        "price": item.price,
        "sale_value": item.sale_value,
        "discount_percent": item.discount_percent,
        "discount_rupees": item.discount_rupees,
        "taxable_value": item.taxable_value})
    return Response({
    "message": "Order Updated Successfully",
    "order_id": order.order_id,
    "total_items": len(updated_items),
    "items": updated_items,
    "total_sale": order.total_sale_value,
    "total_discount": order.total_discount_value,
    "total_taxable": order.total_taxable_value,
    "cash_discount": order.cash_discount,
    "net_amount": order.net_amount_payable})

# CREATE PAYMENT--------------------------------------------------------
@api_view(['POST'])
def create_payment(request):
    current_user, error = get_valid_user(request)
    if error:
        return error
    order_id = request.data.get('order_id')
    if not order_id:
        return Response({"error": "order_id is required"}, status=400)
    amount_received = Decimal(request.data['amount_received'])
    payment_mode_id = request.data["payment_mode_id"]   
    remarks = request.data.get('remarks','')
    payment_mode = get_object_or_404(PaymentModeMaster,payment_mode_id=payment_mode_id,active_status=True)
    order = get_object_or_404(OrderSummary,order_id=order_id)
    if order.payment_status == 'Paid':
       return Response({"error": "This order is already fully paid"}, status=400)
    if amount_received > order.net_amount_payable:
       return Response({"error": "Amount exceeds payable bill amount"})
    total_paid = PaymentTransaction.objects.filter(order=order).aggregate(total=Sum('amount_received'))['total'] or Decimal('0.00')
    remaining_amount = (order.net_amount_payable - total_paid)
    if amount_received > remaining_amount:
       return Response({"error": "Payment exceeds remaining balance"})
    balance = remaining_amount - amount_received
    if amount_received > remaining_amount:
       return Response({"error": "Payment exceeds remaining amount"})
    payment = PaymentTransaction.objects.create(
        order=order,
        amount_received=amount_received,
        balance=balance,
        payment_mode=payment_mode,
        remarks=remarks)
    if balance == 0:
       order.payment_status = 'Paid'
    else:
       order.payment_status = 'Partial'
    order.save()
    return Response({
        "message": "Payment Successful",
        "Payment ID": payment.payment_id,
        "Order ID": order.order_id,
        "Bill Amount": order.net_amount_payable,
        "Amount Received": payment.amount_received,
        "Balance": payment.balance,
        "Payment Mode ID": payment.payment_mode.payment_mode_id,
        "Payment Mode": payment.payment_mode.name,
        "Payment Status": order.payment_status})

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
def order_summary_list(request, order_id=None, from_date=None, to_date=None):
    if order_id:
        orders = OrderSummary.objects.filter(order_id=order_id)
    else:
        from_date = datetime.strptime(from_date,"%d-%m-%Y").date()
        to_date = datetime.strptime(to_date,"%d-%m-%Y").date()
        orders = OrderSummary.objects.filter(date__range=[from_date, to_date])
    serializer = OrderSummarySerializer(orders,many=True)
    return Response(serializer.data)