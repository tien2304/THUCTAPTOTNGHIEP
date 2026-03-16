from django.shortcuts import render
from Home.models import GiangVien, PhanCongGVPT
def home_view(request):
    """Trang chủ dành cho Giảng Viên."""
    # Lấy thông tin giảng viên từ user hiện tại
    # Giả định username là ma_gv
    ma_gv = request.user.username
    giang_vien = GiangVien.objects.filter(ma_gv=ma_gv).first()

    # Kiểm tra xem giảng viên này có phải là giảng viên phụ trách không
    is_gvpt = False
    if giang_vien:
        is_gvpt = PhanCongGVPT.objects.filter(giang_vien=giang_vien).exists()

    context = {
        'current_page': 'home',
        'is_gvpt': is_gvpt,
    }
    return render(request, 'GiangVien/Home.html', context)