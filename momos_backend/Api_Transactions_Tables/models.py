from django.db import models
from Api_Master_Tables.models import *
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# Create your models here.

# CUSTOMER ORDER SUMMARY --------------------------------------------
class OrderSummary(models.Model):
    date = models.DateField(auto_now_add=True)
    order_id = models.PositiveIntegerField(editable=False,default=1)
    time = models.TimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    total_sale_value = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    total_discount_value = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    total_taxable_value = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    cash_discount = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    net_amount_payable = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    payment_status = models.CharField(
    max_length=20,
    default='Pending')
    def save(self, *args, **kwargs):
        # only for new order
        if not self.id:
            current_date = date.today()
            current_year = current_date.year
            current_month = current_date.month
            # financial year logic
            if current_month >= 4:
                start_year = current_year
                end_year = current_year + 1
            else:
                start_year = current_year - 1
                end_year = current_year
            # FY start/end
            fy_start = date(start_year, 4, 1)
            fy_end = date(end_year, 3, 31)
            # last order in FY
            last_order = OrderSummary.objects.filter(date__range=[fy_start, fy_end]).order_by('-order_id').first()
            if last_order:
                 self.order_id = (last_order.order_id + 1)
            else:
                 self.order_id = 1
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.order_id)

# CUSTOMER ORDER DETAILS ----------------------------------------------------
class OrderDetails(models.Model):
    date = models.DateField(auto_now_add=True)
    order_details_id = models.PositiveIntegerField(editable=False,default=1)
    product_name = models.CharField(max_length=100,blank=True)
    order = models.ForeignKey(OrderSummary,on_delete=models.CASCADE,related_name='items')
    product = models.ForeignKey(ProductMaster,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    sale_value = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    discount_rupees = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    taxable_value = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    def save(self, *args, **kwargs):
        # product price
        self.price = self.product.sale_price
        # quantity * price
        self.sale_value = Decimal(self.quantity) * self.price
        # discount
        self.discount_rupees = (self.sale_value * self.discount_percent) / Decimal('100')
        # taxable value
        self.taxable_value = (self.sale_value - self.discount_rupees)
        # custom FY id
        if not self.id:
            current_date = date.today()
            current_year = current_date.year
            current_month = current_date.month
            if current_month >= 4:
                start_year = current_year
                end_year = current_year + 1
            else:
                start_year = current_year - 1
                end_year = current_year
            fy_start = date(start_year, 4, 1)
            fy_end = date(end_year, 3, 31)
            last_detail = OrderDetails.objects.filter(order=self.order).order_by('-order_details_id').first()
            if last_detail:
               self.order_details_id = last_detail.order_details_id + 1
            else:
               self.order_details_id = 1
        self.product_name = self.product.name
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.order_details_id)

# PAYMENT TRANSACTIONS ----------------------------------------------
class PaymentTransaction(models.Model):
    date = models.DateField(auto_now_add=True)
    payment_id = models.PositiveIntegerField(editable=False,default=1)
    order = models.ForeignKey(OrderSummary,on_delete=models.CASCADE)
    time = models.TimeField(auto_now_add=True)
    amount_received = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    payment_mode = models.ForeignKey(PaymentModeMaster,on_delete=models.CASCADE)    
    remarks = models.TextField(null=True,blank=True)
    def save(self, *args, **kwargs):
    # custom FY payment id
     if not self.id:
        current_date = date.today()
        current_year = current_date.year
        current_month = current_date.month
        if current_month >= 4:
            start_year = current_year
            end_year = current_year + 1
        else:
            start_year = current_year - 1
            end_year = current_year
        fy_start = date(start_year, 4, 1)
        fy_end = date(end_year, 3, 31)
        last_payment = (
            PaymentTransaction.objects
            .filter(date__range=[fy_start, fy_end])
            .order_by('-payment_id')
            .first()
        )
        if last_payment:
            self.payment_id = (
                last_payment.payment_id + 1
            )
        else:
            self.payment_id = 1
     super().save(*args, **kwargs)
    # PAYMENT STATUS UPDATE
     self.order.payment_status = "Paid"
     self.order.save(
        update_fields=['payment_status']) 
    def __str__(self):
        return str(self.payment_id)