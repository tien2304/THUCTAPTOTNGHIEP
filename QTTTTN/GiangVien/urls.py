from django.urls import path
from . import views

app_name = 'GiangVien'

urlpatterns = [
    path('', views.home_view, name='giangvien_home'),
]
