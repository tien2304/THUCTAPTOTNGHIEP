from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import SinhVien, GiangVien

def get_redirect_url(user):
    """Xác định URL trang chủ dựa trên vai trò và chức vụ."""
    # 0. Nếu là Superuser (Admin)
    if user.is_superuser:
        return '/admin/'

    # 1. Kiểm tra nếu là Sinh viên
    if SinhVien.objects.filter(ma_sv=user.username).exists():
        return 'SinhVien:sinhvien_home'
    
    # 2. Kiểm tra nếu là Giảng viên / Nhân viên
    gv = GiangVien.objects.filter(ma_gv=user.username).first()
    if gv:
        if gv.chuc_vu == 'Giáo vụ':
            return 'GiaoVu:giaovu_kythuctap'
        elif gv.chuc_vu == 'Trưởng bộ môn':
            return 'TruongBoMon:truongboomon_home'
        else: # Giảng viên
            return 'GiangVien:giangvien_home'
    
    # 3. Mặc định nếu không khớp
    return 'login'

def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_redirect_url(request.user))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            target_url = get_redirect_url(user)
            # Tránh vòng lặp vô tận nếu target_url là 'login'
            if target_url == 'login':
                return redirect('login') 
            return redirect(target_url)
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')

    return render(request, 'Home/login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')
