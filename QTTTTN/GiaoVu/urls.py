from django.urls import path
from . import views

app_name = 'GiaoVu'

urlpatterns = [
    path('', views.home_view, name='giaovu_home'),
    path('ky-thuc-tap/', views.ky_thuc_tap, name='giaovu_kythuctap'),
    path('ky-thuc-tap/edit/', views.edit_ky_thuc_tap_view, name='giaovu_edit_kythuctap'),
    path('quan-ly-sinh-vien/import/', views.import_sinh_vien_view, name='giaovu_import_sinhvien'),
    path('quan-ly-sinh-vien/edit/', views.edit_sinh_vien_view, name='giaovu_edit_sinhvien'),
    path('quan-ly-sinh-vien/delete/<str:ma_sv>/', views.delete_sinh_vien_view, name='giaovu_delete_sinhvien'),
    path('quan-ly-sinh-vien/', views.ql_sinh_vien_view, name='giaovu_qlsinhvien'),
    path('quan-ly-giang-vien/import/', views.import_giang_vien_view, name='giaovu_import_giangvien'),
    path('quan-ly-giang-vien/edit/', views.edit_giang_vien_view, name='giaovu_edit_giangvien'),
    path('quan-ly-giang-vien/delete/<str:ma_gv>/', views.delete_giang_vien_view, name='giaovu_delete_giangvien'),
    path('quan-ly-giang-vien/', views.ql_giang_vien_view, name='giaovu_qlgiangvien'),
    path('tai-lieu/', views.ql_tai_lieu_view, name='giaovu_tailieu'),
    path('tai-lieu/edit/', views.edit_tai_lieu_view, name='giaovu_edit_tailieu'),
    path('nhiem-vu/', views.nhiem_vu_view, name='giaovu_nhiemvu'),
    path('nhiem-vu/<int:nv_id>/', views.chi_tiet_nhiem_vu_view, name='giaovu_chi_tiet_nhiem_vu'),
    path('nhiem-vu/edit/', views.edit_nhiem_vu_view, name='giaovu_edit_nhiemvu'),
    path('nhiem-vu/delete/<int:nv_id>/', views.delete_nhiem_vu_view, name='giaovu_delete_nhiemvu'),
    path('giang-vien-huong-dan/', views.giang_vien_hd_view, name='giaovu_giangvienhd'),
    path('giang-vien-huong-dan/<str:ma_gv>/', views.chi_tiet_gvhd_view, name='chi_tiet_gvhd'),
    path('hoi-dong/', views.hoidong_view, name='giaovu_hoidong'),
    path('hoi-dong/<int:hd_id>/', views.chi_tiet_hoidong_view, name='chi_tiet_hoidong'),
    path('update-thoi-gian-hoi-dong/<int:hd_id>/', views.cap_nhat_thoi_gian_hoi_dong, name='update_thoi_gian_hoi_dong'),
    path('quan-ly-diem/', views.ql_diem_view, name='giaovu_diem'),
    path('quan-ly-diem/cap-nhat-diem-dn/<str:ma_sv>/', views.cap_nhat_diem_dn, name='giaovu_cap_nhat_diem_dn'),
    path('update-password/', views.update_password, name='update_password'),
]
