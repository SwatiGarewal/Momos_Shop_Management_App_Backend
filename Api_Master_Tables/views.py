from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from openpyxl import load_workbook
from django.conf import settings
from django.db import transaction
import os

# Create your views here.

#LOGIN USER---------------------------------------------------------------
@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"error": "Invalid Username or Password"})
    if not user.is_active:
        return Response({"error": "User account is deactivated"})
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "Login Successful",
        "access": str(refresh.access_token),
        "refresh": str(refresh)})

# GET ALL USERS -----------------------------------------
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_users(request):
    users = UserMaster.objects.all().values()
    return Response(users)

# ADD USER ----------------------------------------------
@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    name = request.data.get('name')
    account_type = request.data.get('account_type')
    if User.objects.filter(username=username).exists():
       return Response({"error": "Username already exists"})
    django_user = User.objects.create_user(
    username=username,
    password=password,
    first_name=name)
    if account_type == 'Admin':
     django_user.is_staff = True
     django_user.save()
    user = UserMaster.objects.create(
    username=username,
    password=password,
    name=name,
    account_type=account_type)
    return Response({
        "message": "User Added Successfully",
        "username": user.username})

# GET SINGLE USER -----------------------------------------
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_single_user(request, id):
    user = get_object_or_404(UserMaster, id=id)
    serializer = UserSerializer(user)
    return Response(serializer.data)

# UPDATE USER -----------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_user(request, id):
    if not request.user.is_staff:
        return Response({"error": "Only Admin can perform this action"})
    user_master = get_object_or_404(UserMaster, id=id)
    django_user = get_object_or_404(User, username=user_master.username)
    username = request.data.get("username", user_master.username)
    name = request.data.get("name", user_master.name)
    account_type = request.data.get("account_type", user_master.account_type)
    # Update UserMaster
    user_master.username = username
    user_master.name = name
    user_master.account_type = account_type
    if request.data.get("password"):
        user_master.password = request.data.get("password")
    user_master.save()
    # Update Django User
    django_user.username = username
    django_user.first_name = name
    if request.data.get("password"):
        django_user.set_password(request.data.get("password"))
    if account_type == "Admin":
        django_user.is_staff = True
    else:
        django_user.is_staff = False
    django_user.save()
    return Response({
        "message": "User Updated Successfully"
    })

# UPDATE USER STATUS -----------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_user_status(request, id):
    user_master = get_object_or_404(UserMaster, id=id)
    django_user = get_object_or_404(User, username=user_master.username)
    status = request.data.get("active_status")
    if status is None:
        return Response({"error": "active_status field is required"})
    user_master.active_status = status
    user_master.save()
    django_user.is_active = status
    django_user.save()
    return Response({
        "message": "User Status Updated Successfully",
        "active_status": status
    })

# GET ALL PRODUCTS-----------------------------------------------
@api_view(['GET'])
def get_products(request):
    products = ProductMaster.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

# ADD PRODUCT------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_product(request):
   if not request.user.is_staff:
    return Response({"error": "Only Admin can perform this action"})
   if not request.user.is_active:
    return Response({"error": "User account is deactivated"})
   serializer = ProductSerializer(data=request.data)
   if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Product Added Successfully'})
   return Response(serializer.errors)

# GET SINGLE PRODUCT-------------------------------------------
@api_view(['GET'])
def get_single_product(request, id):
    product = get_object_or_404(ProductMaster,id=id,is_active=True)
    serializer = ProductSerializer(product)
    return Response(serializer.data)

# UPDATE PRODUCT-------------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_product(request, id):
    if not request.user.is_staff:
      return Response({"error": "Only Admin can perform this action"})
    if not request.user.is_active:
      return Response({"error": "User account is deactivated"})
    product = get_object_or_404(ProductMaster,id=id)
    serializer = ProductSerializer(product, data=request.data,partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Product Updated Successfully'})
    return Response(serializer.errors)

#PRODUCT STATUS------------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_product_status(request, id):
    if not request.user.is_staff:
       return Response({"error": "Only Admin can perform this action"})
    if not request.user.is_active:
        return Response({"error": "User account is deactivated"})
    product = get_object_or_404(ProductMaster,id=id)
    is_active = request.data.get('is_active')
    if is_active is None:return Response({"error":"is_active field is required"},status=400)
    product.is_active = is_active
    product.save()
    return Response({
        'message':
        'Product status updated successfully',
        'is_active':
        product.is_active
    })

# ADD PAYMENT MODE --------------------------------
@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_payment_mode(request):
    name = request.data.get('name')
    payment_mode = PaymentModeMaster.objects.create(name=name)
    return Response({
        "message": "Payment Mode Added Successfully",
        "name": payment_mode.name})

# GET ALL PAYMENT MODES --------------------------------
@api_view(['GET'])
def get_payment_modes(request):
    payment_modes = PaymentModeMaster.objects.all().values()
    return Response(payment_modes)

# GET SINGLE PAYMENT MODE -----------------------------------------
@api_view(['GET'])
def get_single_payment_mode(request, id):
    payment_mode = get_object_or_404(PaymentModeMaster, payment_mode_id=id)
    serializer = PaymentModeSerializer(payment_mode)
    return Response(serializer.data)

# UPDATE PAYMENT MODE -----------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_payment_mode(request, id):
    if not request.user.is_staff:
        return Response({"error": "Only Admin can perform this action"})
    payment_mode = get_object_or_404(
        PaymentModeMaster,
        payment_mode_id=id)
    serializer = PaymentModeSerializer(
        payment_mode,
        data=request.data,
        partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Payment Mode Updated Successfully"})
    return Response(serializer.errors)

# UPDATE PAYMENT MODE STATUS -----------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_payment_mode_status(request, id):
    payment_mode = get_object_or_404(
        PaymentModeMaster,
        payment_mode_id=id)
    status = request.data.get("active_status")
    if status is None:
        return Response({
            "error": "active_status field is required"})
    payment_mode.active_status = status
    payment_mode.save()
    return Response({
        "message": "Payment Mode Status Updated Successfully",
        "active_status": payment_mode.active_status})

# IMPORT PRODUCTS FROM EXCEL ------------------------------------------
@transaction.atomic
@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_products(request):
    if not request.user.is_staff:
        return Response({"error": "Only Admin can perform this action"})
    if 'file' not in request.FILES:
        return Response({"error": "Excel file is required"})
    excel_file = request.FILES['file']
    try:
        workbook = load_workbook(excel_file)
        sheet = workbook.active
        imported = 0
        skipped = 0
        errors = []
        # Skip Header Row
        for row in sheet.iter_rows(min_row=2, values_only=True):
            name = " ".join(str(row[0]).split())
            sale_price = row[1]
            stock = row[2]
            photo = row[3]
            is_active = row[4]
            # Required Fields
            if not name or sale_price is None or stock is None:
                skipped += 1
                errors.append(f"{name} -> Missing Required Data")
                continue
            # Duplicate Product
            if ProductMaster.objects.filter(name__iexact=name).exists():
               skipped += 1
               errors.append(f"{name} -> Already Exists")
               continue
            product = ProductMaster(
                name=name,
                sale_price=sale_price,
                stock=stock,
                is_active=True if is_active in [True, "True", 1, "1", None] else False)
            # Optional Photo
            if photo:
                image_path = os.path.join(settings.MEDIA_ROOT,"products",str(photo))
                if os.path.exists(image_path):
                    product.photo = f"products/{photo}"
            product.save()
            imported += 1
        return Response({
            "message": "Products Imported Successfully",
            "Imported Products": imported,
            "Skipped Products": skipped,
            "Errors": errors})
    except Exception as e:
        return Response({"error": str(e)})