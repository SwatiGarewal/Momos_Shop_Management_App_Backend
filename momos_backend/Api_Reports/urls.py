from django.urls import path
from .views import *

urlpatterns = [
    path('api/reports/sales/<str:from_date>/<str:to_date>/', sales_report),
    path('api/reports/product-sales/<str:from_date>/<str:to_date>/', product_sales_report),
    path('api/reports/payment/<str:from_date>/<str:to_date>/', payment_report),
    path('api/reports/pivot/<str:from_date>/<str:to_date>/', pivot_report),
    path('api/reports/pdf-report/<str:from_date>/<str:to_date>/', generate_pdf_report),
    path('api/reports/excel-report/<str:from_date>/<str:to_date>/', generate_excel_report),
]