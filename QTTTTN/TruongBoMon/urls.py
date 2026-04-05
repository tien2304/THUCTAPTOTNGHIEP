from django.urls import path
from . import views
app_name = 'TruongBoMon'
urlpatterns = [
    path('', views.home_view, name='truongboomon_home'),
    path('phan-cong-gvpt/', views.phan_cong_gvpt_view, name='phan_cong_gvpt'),
    path('duyet-gvhd/', views.duyet_gvhd_view, name='duyet_gvhd'),
    path('duyet-gvhd/action/', views.action_duyet_gvhd, name='action_duyet_gvhd'),
    path('duyet-gvhd/<str:ma_gv>/', views.chi_tiet_gvhd_view, name='chi_tiet_gvhd'),
    path('update-password/', views.update_password, name='update_password'),
]
