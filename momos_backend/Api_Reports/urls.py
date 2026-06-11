from django.urls import path
from .views import *

urlpatterns = [
    path('api/reports/sales/', sales_report),  #(?type="")
    path('api/reports/product-sales/', product_sales_report),
    path('api/reports/payment/', payment_report),
    path('api/reports/pivot/', pivot_report),
    path('api/reports/pdf-report/', generate_pdf_report),
    # path('api/reports/excel-report/', generate_excel_report),
]