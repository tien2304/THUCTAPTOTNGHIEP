from django.urls import path
from . import views
app_name = 'TruongBoMon'
urlpatterns = [
    path('', views.home_view, name='truongboomon_home'),
    path('phan-cong-gvpt/', views.phan_cong_gvpt_view, name='phan_cong_gvpt'),
]
