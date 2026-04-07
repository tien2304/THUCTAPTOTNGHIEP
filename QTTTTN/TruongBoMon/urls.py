from django.urls import path
from . import views
app_name = 'TruongBoMon'
urlpatterns = [
    path('', views.home_view, name='truongboomon_home'),
    path('phan-cong-gvpt/', views.phan_cong_gvpt_view, name='phan_cong_gvpt'),
    path('duyet-gvhd/', views.duyet_gvhd_view, name='duyet_gvhd'),
    path('duyet-gvhd/action/', views.action_duyet_gvhd, name='action_duyet_gvhd'),
    path('duyet-gvhd/update-ajax/', views.update_gvhd_ajax, name='update_gvhd_ajax'),
    path('duyet-gvhd/<str:ma_gv>/', views.chi_tiet_gvhd_view, name='chi_tiet_gvhd'),
    
    # Sinh viên hướng dẫn (Cổng Giảng viên cho Trưởng bộ môn)
    path('sinh-vien-huong-dan/', views.sinhvien_huongdan, name='sinhvien_huongdan'),
    path('sinh-vien-huong-dan/<str:ma_sv>/', views.chi_tiet_sinh_vien, name='chi_tiet_sv'),
    path('sinh-vien-huong-dan/<str:ma_sv>/save-diem/', views.save_diem, name='save_diem'),
    path('bai-nop/<int:id>/', views.chi_tiet_bai_nop, name='chi_tiet_bai_nop'),
    path('update-sinh-vien/<str:ma_sv>/', views.update_sinh_vien_info, name='update_sinh_vien_info'),

    # Hội đồng bảo vệ (Cổng Giảng viên cho Trưởng bộ môn)
    path('hoi-dong/', views.hoi_dong_list, name='hoi_dong_list'),
    path('hoi-dong/<int:id>/', views.hoi_dong_detail, name='hoi_dong_detail'),
    path('hoi-dong/<int:id>/cham-diem/<str:ma_sv>/', views.cham_diem_hoi_dong, name='cham_diem_hoi_dong'),

    # Các chức năng quản lý khác của Trưởng bộ môn
    path('duyet-hoidong/', views.duyet_hoidong_view, name='duyet_hoidong'),
    path('duyet-hoidong/<int:hd_id>/', views.chi_tiet_hoidong_view, name='chi_tiet_hoidong'),
    path('diem/', views.diem_view, name='diem_view'),
    path('diem/cong-bo/<int:ky_id>/', views.cong_bo_diem_action, name='truongboomon_cong_bo_diem'),
    path('cau-hinh-diem/', views.cau_hinh_diem_view, name='cau_hinh_diem'),

    path('update-password/', views.update_password, name='update_password'),
]
