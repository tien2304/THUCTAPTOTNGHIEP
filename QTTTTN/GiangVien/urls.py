from django.urls import path
from . import views
app_name = "GiangVien"

urlpatterns = [
    path('', views.home_view, name='giangvien_home'),
    path('forms/', views.form_list, name='form_list'),
    path('sinh-vien-huong-dan/',views.sinhvien_huongdan,name='sinhvien_huongdan'),
    path('tao-form/', views.tao_form, name='tao_form'),
    path('form/<uuid:public_id>/', views.public_form, name='public_form'),

    path('submit/<uuid:public_id>/', views.submit_form, name='submit_form'),]
