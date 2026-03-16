from django.urls import path
from . import views

app_name = 'SinhVien'

urlpatterns = [
    path('', views.home_view, name='sinhvien_home'),
path('nhiem-vu/', views.nhiem_vu_view, name='nhiem_vu_page'),
]
# t
