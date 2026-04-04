from django.urls import path
from . import views
app_name = "SinhVien"
urlpatterns = [
    path('', views.home, name='sinhvien_home'),
    path('nhiem-vu/', views.nhiem_vu, name='nhiem_vu_page'),
    path('xem-diem/', views.xem_diem, name='xem_diem_page'),
    path('nhiem-vu/dien-form/<uuid:public_id>/', views.dien_form, name='dien_form'),
    path('nhiem-vu/submit-form/<uuid:public_id>/', views.submit_form, name='submit_form'),
    path('tong-hop-nxet/', views.tong_hop_nxet, name='tong-hop-nxet'),
    path('nhiem-vu/nop-bai/', views.nop_bai_action, name='nop_bai_action'),
    path('update-password/', views.update_password, name='update_password'),
]
