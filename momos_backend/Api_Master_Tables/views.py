from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
from .serializers import ProductSerializer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

# Create your views here.



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
        return Response({'message': 'ProductMaster Added Successfully'})
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
    serializer = ProductSerializer(product, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'ProductMaster Updated Successfully'})
    return Response(serializer.errors)

# DEACTIVATE PRODUCT------------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def deactivate_product(request, id):
    if not request.user.is_staff:
       return Response({"error": "Only Admin can perform this action"})
    if not request.user.is_active:
       return Response({"error": "User account is deactivated"})
    product = get_object_or_404(ProductMaster,id=id)
    product.is_active = False
    product.save()
    return Response({'message': 'ProductMaster Deactivated Successfully'})

# ACTIVATE PRODUCT-----------------------------------------------
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def activate_product(request, id):
    if not request.user.is_staff:
       return Response({"error": "Only Admin can perform this action"})
    if not request.user.is_active:
       return Response({"error": "User account is deactivated"})
    product = get_object_or_404(ProductMaster,id=id)
    product.is_active = True
    product.save()
    return Response({'message': 'ProductMaster Activated Successfully'})

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

# GET ALL PAYMENT MODES --------------------------------
@api_view(['GET'])
def get_payment_modes(request):
    payment_modes = PaymentModeMaster.objects.all().values()
    return Response(payment_modes)

# ADD PAYMENT MODE --------------------------------
@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_payment_mode(request):
    name = request.data.get('name')
    payment_mode = PaymentModeMaster.objects.create(name=name)
    return Response({
        "message": "Payment Mode Added Successfully",
        "name": payment_mode.name})