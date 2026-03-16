from django.shortcuts import render


def home_view(request):
    # Giả lập dữ liệu (Sau này bạn sẽ thay bằng query từ Database)
    # Ví dụ: giang_vien = GiangVien.objects.filter(sinhvien=request.user).first()

    context = {
        'current_page': 'home',

        # Nếu để None, Template sẽ hiện "Chưa cập " (nhờ thẻ {% else %})
        'giang_vien': None,

        # Nếu có dữ liệu, Template sẽ tự động đổ vào các dòng tương ứng
        'cong_ty': None,

        # Danh sách nhiệm vụ: Nếu để [] (rỗng), Template sẽ hiện "Chưa có nhiệm vụ"
        'danh_sach_nhiem_vu': [],

        # Danh sách tài liệu rỗng
        'tai_lieu': []
    }

    # Render dashboard.html (file này sẽ {% extends 'SinhVien/home.html' %})
    return render(request, 'SinhVien/dashboard.html', context)


def nhiem_vu_view(request):
    context = {
        'current_page': 'nhiem_vu',
        'tasks': []  # Danh sách rỗng cho trang nhiệm vụ
    }
    return render(request, 'SinhVien/nhiem_vu.html', context)