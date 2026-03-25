from django.urls import path
from . import views
app_name = "SinhVien"
urlpatterns = [
    path('', views.home, name='sinhvien_home'),
    path('nhiem-vu/', views.nhiem_vu, name='nhiem_vu_page'),
    path('xem-diem/', views.xem_diem, name='xem_diem_page'),
    path('nhiem-vu/dien-form/<uuid:public_id>/', views.dien_form, name='dien_form'),
    path('nhiem-vu/submit-form/<uuid:public_id>/', views.submit_form, name='submit_form'),
]
