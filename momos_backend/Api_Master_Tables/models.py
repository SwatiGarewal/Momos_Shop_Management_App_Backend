from django.db import models
from django.contrib.auth.hashers import make_password

# Create your models here.

# USER MASTER TABLE----------------------------------
class UserMaster(models.Model):
    ACCOUNT_TYPES = (('Admin', 'Admin'),('Standard', 'Standard'),)
    username = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20,choices=ACCOUNT_TYPES)
    active_status = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.username

# PRODUCT MASTER TABLE-----------------------------------------
class ProductMaster(models.Model):
    name = models.CharField(max_length=100,unique=True)
    sale_price = models.DecimalField(max_digits=10,decimal_places=2)
    stock = models.IntegerField(default=0)
    photo = models.ImageField(upload_to='all-products/',null=True,
    blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.name
        
# PAYMENT MODE MASTER TABLE-----------------------------------
class PaymentModeMaster(models.Model):
    payment_mode_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100,unique=True)
    active_status = models.BooleanField(default=True)
    def __str__(self):
        return self.name