from django.urls import path
from . import views
app_name = "GiangVien"

urlpatterns = [
    path('', views.home_view, name='giangvien_home'),
    path('forms/', views.form_list, name='form_list'),
    path('sinh-vien-huong-dan/',views.sinhvien_huongdan,name='sinhvien_huongdan'),
    path('sinh-vien-huong-dan/<str:ma_sv>/',views.chi_tiet_sinh_vien,name='chi_tiet_sv'),
    path('sinh-vien-huong-dan/<str:ma_sv>/save-diem/',views.save_diem,name='save_diem'),
    path('bai-nop/<int:id>/',views.chi_tiet_bai_nop,name='chi_tiet_bai_nop'),
path('update-sinh-vien/<str:ma_sv>/', views.update_sinh_vien_info, name='update_sinh_vien_info'),

    path('tao-form/', views.tao_form, name='tao_form'),
    path('form/<uuid:public_id>/', views.form_detail, name='form_detail'),
    path('submit/<uuid:public_id>/', views.submit_form, name='submit_form'),
path('public/<uuid:public_id>/', views.public_form, name='public_form'),
path('tao-form/<uuid:public_id>/', views.edit_form, name='edit_form'),
    # path('auto-assign/<int:form_id>/', views.run_auto_assign, name='auto_assign'),

path('phan-cong/', views.phan_cong_dashboard, name='phan_cong'),
# path('phan-cong/auto/', views.run_auto_assign_ui, name='auto_assign_ui'),
path('phan-cong/update/', views.update_phan_cong, name='update_phan_cong'),
path('xoa-form/<uuid:public_id>/', views.xoa_form, name='xoa_form'),
# path('phan-cong/select/', views.select_sinh_vien),
# path('phan-cong/confirm/', views.confirm_assign),
# path('phan-cong/save/', views.save_assign),

    #HOI_DONG
path('hoi-dong/', views.hoi_dong_list, name='hoi_dong_list'),
path('hoi-dong/tao/', views.tao_hoi_dong, name='tao_hoi_dong'),
path('hoi-dong/<int:id>/', views.hoi_dong_detail, name='hoi_dong_detail'),
path('hoi-dong/<int:id>/them-sv/', views.them_sinh_vien, name='them_sinh_vien'),
path('hoi-dong/<int:id>/cham-diem/<str:ma_sv>/',views.cham_diem_hoi_dong,name='cham_diem_hoi_dong'),

path('hoi-dong/load-sv/', views.load_sinh_vien),
path('update-password/', views.update_password, name='update_password'),

]
