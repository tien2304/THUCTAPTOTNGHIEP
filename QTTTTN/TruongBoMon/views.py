from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from Home.models import GiangVien, KyThucTap, PhanCongGVPT


def home_view(request):
    return render(request, 'TruongBoMon/home.html', {'current_page': 'home'})


def phan_cong_gvpt_view(request):
    """Trang phân công giảng viên phụ trách cho Trưởng bộ môn."""
    if request.method == "POST":
        ma_gv = request.POST.get('ma_gv')
        ky_id = request.POST.get('ky_id')

        if ma_gv and ky_id:
            gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
            ky = KyThucTap.objects.filter(id=ky_id).first()

            if gv and ky:
                # Kiểm tra xem đã phân công chưa
                exists = PhanCongGVPT.objects.filter(giang_vien=gv, ky=ky).exists()
                if not exists:
                    PhanCongGVPT.objects.create(giang_vien=gv, ky=ky)
                    messages.success(request, f"Đã phân công {gv.ho_ten} phụ trách {ky.ten_ky}!")
                else:
                    messages.warning(request, "Giảng viên này đã được phân công phụ trách kỳ này rồi.")
            else:
                messages.error(request, "Dữ liệu không hợp lệ.")
        else:
            messages.error(request, "Vui lòng chọn đầy đủ giảng viên và kỳ thực tập.")
        return redirect('TruongBoMon:phan_cong_gvpt')

    # GET: Hiển thị form và lịch sử
    giang_vien_list = GiangVien.objects.all().order_by('ho_ten')
    ky_list = KyThucTap.objects.all().order_by('-id')
    lich_su = PhanCongGVPT.objects.all().order_by('-ngay_phan_cong')

    # Phân trang cho lịch sử
    paginator = Paginator(lich_su, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'current_page': 'phan_cong_gvpt',
        'giang_vien_list': giang_vien_list,
        'ky_list': ky_list,
        'page_obj': page_obj,
    }
    return render(request, 'TruongBoMon/phan_cong_gvpt.html', context)