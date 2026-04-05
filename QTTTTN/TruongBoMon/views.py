from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from Home.models import (GiangVien, KyThucTap, PhanCongGVPT, PhanCongGVHD, HoiDong, 
                         HoiDong_GiangVien, HoiDong_SinhVien, BangDiem, SinhVien, TyLeDiem,
                         BaiNop, NhiemVu, PhieuTraLoi, ChiTietTraLoi)


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

def duyet_gvhd_view(request):
    """Trang duyệt phân công Giảng viên hướng dẫn cho Trưởng bộ môn."""
    ky_list = KyThucTap.objects.all().order_by('-id')
    selected_ky_id = request.GET.get('ky_id')
    
    if selected_ky_id:
        selected_ky_id = int(selected_ky_id)
        selected_ky = ky_list.filter(id=selected_ky_id).first()
    else:
        selected_ky = ky_list.first()
        selected_ky_id = selected_ky.id if selected_ky else None
        
    ds_phan_cong = []
    if selected_ky:
        # Lấy danh sách phân công GVHD, loại bỏ giáo vụ
        phan_cong_qs = PhanCongGVHD.objects.filter(ky_id=selected_ky_id).select_related('sinh_vien', 'giang_vien').exclude(giang_vien__chuc_vu='Giáo vụ')
        
        gv_dict = {}
        for pc in phan_cong_qs:
            gv = pc.giang_vien
            sv = pc.sinh_vien
            trang_thai = pc.trang_thai
            if gv not in gv_dict:
                gv_dict[gv] = []
            gv_dict[gv].append({'sv': sv, 'trang_thai': trang_thai, 'pc_id': pc.id})
            
        for gv, sv_list in gv_dict.items():
            # Kiểm tra trạng thái duyệt (nếu tất cả == 2 thì là đã duyệt)
            is_approved = all(item['trang_thai'] == 2 for item in sv_list)
            
            ds_phan_cong.append({
                'giang_vien': gv,
                'so_luong': len(sv_list),
                'ds_sv': sorted(sv_list, key=lambda x: x['sv'].ma_sv),
                'is_approved': is_approved,
            })
            
    # Sắp xếp theo số lượng sv HD giảm dần
    ds_phan_cong = sorted(ds_phan_cong, key=lambda x: x['so_luong'], reverse=True)

    context = {
        'current_page': 'duyet_gvhd',
        'ky_list': ky_list,
        'selected_ky': selected_ky,
        'selected_ky_id': selected_ky_id,
        'ds_phan_cong': ds_phan_cong,
    }
    return render(request, 'TruongBoMon/duyet_gvhd.html', context)

def action_duyet_gvhd(request):
    if request.method == 'POST':
        ky_id = request.POST.get('ky_id')
        ma_gv = request.POST.get('ma_gv')
        action = request.POST.get('action')
        ly_do = request.POST.get('ly_do_tu_choi', '')
        
        if not ky_id:
            messages.error(request, 'Không tìm thấy kỳ.')
            return redirect('TruongBoMon:duyet_gvhd')
            
        ds_phan_cong = PhanCongGVHD.objects.filter(ky_id=ky_id)
        if ma_gv:
            ds_phan_cong = ds_phan_cong.filter(giang_vien__ma_gv=ma_gv)
            
        if not ds_phan_cong.exists():
            messages.error(request, 'Không có phân công nào để thao tác.')
            if ma_gv:
                return redirect(f'/truong-bo-mon/duyet-gvhd/{ma_gv}/?ky_id={ky_id}')
            return redirect(f'/truong-bo-mon/duyet-gvhd/?ky_id={ky_id}')
            
        if action == 'approve':
            ds_phan_cong.update(trang_thai=2, ly_do_tu_choi=None)
            messages.success(request, 'Đã phê duyệt phân công thành công!')
        elif action == 'reject':
            ds_phan_cong.update(trang_thai=3, ly_do_tu_choi=ly_do)
            messages.success(request, 'Đã từ chối phân công!')
            
        if ma_gv:
            return redirect(f'/truong-bo-mon/duyet-gvhd/{ma_gv}/?ky_id={ky_id}')
        return redirect(f'/truong-bo-mon/duyet-gvhd/?ky_id={ky_id}')
    return redirect('TruongBoMon:duyet_gvhd')

def chi_tiet_gvhd_view(request, ma_gv):
    """Trang xem danh sách sinh viên được hướng dẫn bởi 1 giảng viên cụ thể"""
    ky_id = request.GET.get('ky_id')
    giang_vien = GiangVien.objects.filter(ma_gv=ma_gv).first()
    
    if not giang_vien:
        messages.error(request, "Không tìm thấy giảng viên này.")
        return redirect('TruongBoMon:duyet_gvhd')
        
    ky = None
    ds_phan_cong = []
    
    if ky_id:
        ky = KyThucTap.objects.filter(id=ky_id).first()
        if ky:
            ds_phan_cong = PhanCongGVHD.objects.filter(giang_vien=giang_vien, ky=ky).select_related('sinh_vien', 'ky')
            
    is_approved = True
    if ds_phan_cong:
        is_approved = all(pc.trang_thai == 2 for pc in ds_phan_cong)
        
    hoc_vi_dict = {
        'Thạc sĩ': 'ThS',
        'Tiến sĩ': 'TS',
        'Phó Giáo sư': 'PGS.TS', # Hoặc 'PGS', tuỳ thuộc chuẩn ngữ cảnh VN thường gọi 'PGS' hoặc 'PGS.TS'
        'Giáo sư': 'GS.TS', # Hoặc 'GS'
    }
    
    # Chuẩn hoá phổ biến cho học vị bằng tiếng Việt tắt
    raw_hoc_vi = giang_vien.hoc_vi
    if raw_hoc_vi == 'Thạc sĩ':
        hoc_vi_tat = 'ThS'
    elif raw_hoc_vi == 'Tiến sĩ':
        hoc_vi_tat = 'TS'
    elif raw_hoc_vi == 'Phó Giáo sư':
        hoc_vi_tat = 'PGS'
    elif raw_hoc_vi == 'Giáo sư':
        hoc_vi_tat = 'GS'
    else:
        hoc_vi_tat = raw_hoc_vi
            
    context = {
        'current_page': 'duyet_gvhd',
        'giang_vien': giang_vien,
        'hoc_vi_tat': hoc_vi_tat,
        'ky': ky,
        'ds_phan_cong': ds_phan_cong,
        'is_approved': is_approved,
    }
    return render(request, 'TruongBoMon/chi_tiet_gvhd.html', context)


def duyet_hoidong_view(request):
    """Trang duyệt danh sách Hội đồng – Trưởng Bộ Môn."""
    all_ky = KyThucTap.objects.all().order_by('-id')
    ky_id = request.GET.get('ky_id')
    
    if ky_id:
        selected_ky = KyThucTap.objects.filter(id=ky_id).first()
    else:
        selected_ky = all_ky.first()
        
    ds_hoidong = []
    if selected_ky:
        hoidong_qs = HoiDong.objects.filter(ky=selected_ky).order_by('ngay_bao_ve', 'thoi_gian_bat_dau')
        
        for hd in hoidong_qs:
            gv_list = HoiDong_GiangVien.objects.filter(hoi_dong=hd).select_related('giang_vien')
            sv_list = HoiDong_SinhVien.objects.filter(hoi_dong=hd).select_related('sinh_vien')
            
            ds_hoidong.append({
                'id': hd.id,
                'ten': hd.ten_hoi_dong,
                'thoi_gian': f"{hd.thoi_gian_bat_dau.strftime('%H:%M')} - {hd.thoi_gian_ket_thuc.strftime('%H:%M')}" if hd.thoi_gian_bat_dau and hd.thoi_gian_ket_thuc else "Chưa thiết lập",
                'ngay_bao_ve': hd.ngay_bao_ve,
                'dia_diem': hd.dia_diem,
                'gv_count': gv_list.count(),
                'sv_count': sv_list.count(),
                'giang_vien': [g.giang_vien for g in gv_list],
                'sinh_vien': [s.sinh_vien for s in sv_list]
            })
            
    context = {
        'current_page': 'duyet_hoi_dong',
        'all_ky': all_ky,
        'selected_ky': selected_ky,
        'selected_ky_id': selected_ky.id if selected_ky else None,
        'ds_hoidong': ds_hoidong,
    }
    return render(request, 'TruongBoMon/duyet_hoidong.html', context)

def chi_tiet_hoidong_view(request, hd_id):
    """Trang chi tiết Hội đồng – Trưởng Bộ Môn."""
    hoidong = HoiDong.objects.filter(id=hd_id).select_related('ky').first()
    
    if not hoidong:
        messages.error(request, "Không tìm thấy hội đồng này.")
        return redirect('TruongBoMon:duyet_hoidong')
        
    ds_giang_vien = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong).select_related('giang_vien')
    ds_sinh_vien = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong).select_related('sinh_vien')
    
    context = {
        'current_page': 'duyet_hoi_dong',
        'hoidong': hoidong,
        'ds_giang_vien': ds_giang_vien,
        'ds_sinh_vien': ds_sinh_vien,
    }
    return render(request, 'TruongBoMon/chi_tiet_hoidong.html', context)


def diem_view(request):
    """Trang xem điểm của tất cả sinh viên – Trưởng Bộ Môn."""
    all_ky = KyThucTap.objects.all().order_by('-id')
    ky_id = request.GET.get('ky_id')
    
    if ky_id:
        selected_ky = KyThucTap.objects.filter(id=ky_id).first()
    else:
        selected_ky = all_ky.first()
        
    ds_diem = []
    page_obj = None
    if selected_ky:
        # Tự động tạo BangDiem cho SV nếu chưa có (để đảm bảo hiển thị hết SV kì ni)
        sinh_viens = SinhVien.objects.filter(ky_hien_tai=selected_ky)
        for sv in sinh_viens:
            BangDiem.objects.get_or_create(sinh_vien=sv, ky=selected_ky)

        # Lấy danh sách toàn bộ điểm của sinh viên trong kỳ này
        diem_qs = BangDiem.objects.filter(ky=selected_ky).select_related('sinh_vien').order_by('sinh_vien__ma_sv')
        
        # Phân trang: 10 sinh viên 1 trang
        paginator = Paginator(diem_qs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
    context = {
        'current_page': 'diem',
        'all_ky': all_ky,
        'selected_ky': selected_ky,
        'selected_ky_id': selected_ky.id if selected_ky else None,
        'page_obj': page_obj,
    }
    return render(request, 'TruongBoMon/diem.html', context)

def cau_hinh_diem_view(request):
    """Trang cấu hình tỷ lệ điểm – Trưởng Bộ Môn."""
    if request.method == "POST":
        ky_id = request.POST.get('ky_id')
        gvhd_weight = float(request.POST.get('gvhd', 0)) / 100.0
        hoidong_weight = float(request.POST.get('hoidong', 0)) / 100.0
        dn_weight = float(request.POST.get('dn', 0)) / 100.0

        # Kiểm tra tổng trọng số (thường là 1.0)
        total = round(gvhd_weight + hoidong_weight + dn_weight, 2)
        if total != 1.0:
            messages.warning(request, f"Lưu ý: Tổng trọng số là {int(total*100)}%, có thể không phải là 100%.")

        if ky_id:
            ky = KyThucTap.objects.filter(id=ky_id).first()
            if ky:
                # Cập nhật hoặc tạo mới
                tyle, created = TyLeDiem.objects.update_or_create(
                    ky=ky,
                    defaults={
                        'diem_gvhd': gvhd_weight,
                        'diem_hoidong': hoidong_weight,
                        'diem_doanhnghiep': dn_weight
                    }
                )
                if created:
                    messages.success(request, f"Đã thiết lập tỷ lệ điểm mới cho {ky.ten_ky}!")
                else:
                    messages.success(request, f"Đã cập nhật tỷ lệ điểm cho {ky.ten_ky}!")
            else:
                messages.error(request, "Học kỳ không hợp lệ.")
        else:
            messages.error(request, "Vui lòng chọn học kỳ.")
        return redirect('TruongBoMon:cau_hinh_diem')

    # GET request
    all_ky = KyThucTap.objects.all().order_by('-id')
    lich_su = TyLeDiem.objects.all().select_related('ky').order_by('-id')
    
    # Phân trang
    paginator = Paginator(lich_su, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'current_page': 'cau_hinh_diem',
        'all_ky': all_ky,
        'page_obj': page_obj,
    }
    return render(request, 'TruongBoMon/cau_hinh_diem.html', context)

def get_is_gvpt(request):
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    if gv:
        return PhanCongGVPT.objects.filter(giang_vien=gv).exists()
    return False

def sinhvien_huongdan(request):
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    ky_id = request.GET.get("ky")
    query = request.GET.get("q")
    danh_sach = PhanCongGVHD.objects.filter(giang_vien=gv, trang_thai=2).select_related('sinh_vien', 'ky')
    if ky_id:
        danh_sach = danh_sach.filter(ky_id=ky_id)
    if query:
        danh_sach = danh_sach.filter(
            Q(sinh_vien__ma_sv__icontains=query) |
            Q(sinh_vien__ho_ten__icontains=query) |
            Q(sinh_vien__lop__icontains=query)
        )
    ky_list = KyThucTap.objects.all().order_by('-id')
    current_ky = KyThucTap.objects.filter(id=ky_id).first() if ky_id else None
    for item in danh_sach:
        sv = item.sinh_vien
        if not sv.noi_thuc_tap:
             phieu = PhieuTraLoi.objects.filter(sinh_vien=sv).order_by("-id").first()
             if phieu:
                 for ans in phieu.answers.all():
                     if (ans.cau_hoi.system_tag or "").strip() == "don_vi_tt":
                         sv.noi_thuc_tap = ans.gia_tri
                         sv.save()
                         break
        item.noi_thuc_tap = sv.noi_thuc_tap or ""
    context = {
        'danh_sach': danh_sach,
        'ky_list': ky_list,
        'current_ky': current_ky,
        'query': query,
        'current_page': 'sinhvien'
    }
    return render(request, 'TruongBoMon/sinhvien_huongdan.html', context)

def chi_tiet_sinh_vien(request, ma_sv):
    sv = get_object_or_404(SinhVien, ma_sv=ma_sv)
    ky = sv.ky_hien_tai
    nhiem_vus = NhiemVu.objects.filter(ky=ky).order_by("han_nop")
    milestones = []
    for nv in nhiem_vus:
        bai_nop = BaiNop.objects.filter(sinh_vien=sv, nhiem_vu=nv).first()
        if bai_nop:
            status = "ĐÃ NỘP"
            file = bai_nop.ten_file
            file_url = bai_nop.file_path.url
            ngay = bai_nop.thoi_gian_nop
            bai_id = bai_nop.id
        else:
            status = "CHƯA NỘP"
            file = "--"
            file_url = "#"
            ngay = "--"
            bai_id = None
        milestones.append({
            "id": bai_id,
            "ten": nv.ten_nhiem_vu,
            "ngay": ngay,
            "file": file,
            "file_url": file_url,
            "status": status,
            "is_submitted": True if bai_nop else False
        })
    bang_diem = BangDiem.objects.filter(sinh_vien=sv, ky=ky).order_by('-id').first()
    context = {
        "sv": sv,
        "milestones": milestones,
        "bang_diem": bang_diem,
        "current_page": 'sinhvien'
    }
    return render(request, "TruongBoMon/chi_tiet_sinh_vien.html", context)

def save_diem(request, ma_sv):
    sv = SinhVien.objects.get(ma_sv=ma_sv)
    ky = sv.ky_hien_tai or KyThucTap.objects.order_by('-id').first()
    diem = request.POST.get("diem")
    if diem:
        diem = float(diem)
    bd, _ = BangDiem.objects.get_or_create(sinh_vien=sv, ky=ky)
    bd.diem_qua_trinh = diem
    bd.save()
    return redirect("TruongBoMon:chi_tiet_sv", ma_sv=ma_sv)

def chi_tiet_bai_nop(request, id):
    bai = get_object_or_404(BaiNop, id=id)
    if request.method == "POST":
        nhan_xet = request.POST.get('nhan_xet', '').strip()
        bai.nhan_xet = nhan_xet
        bai.save()
    context = {
        "bai": bai,
        "sv": bai.sinh_vien,
        "nv": bai.nhiem_vu,
        'current_page': 'sinhvien'
    }
    return render(request, "TruongBoMon/chi_tiet_bai_nop.html", context)

def update_sinh_vien_info(request, ma_sv):
    sv = SinhVien.objects.get(ma_sv=ma_sv)
    ten_de_tai = request.POST.get('ten_de_tai', '').strip()
    noi_tt = request.POST.get('noi_tt', '').strip()
    if ten_de_tai:
        sv.ten_de_tai = ten_de_tai
    if noi_tt:
        sv.noi_thuc_tap = noi_tt
    sv.save()
    return redirect("TruongBoMon:sinhvien_huongdan")

def hoi_dong_list(request):
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    is_gvpt = get_is_gvpt(request)
    tab = request.GET.get('tab', 'my')
    ky_id = request.GET.get('ky')
    ky_list = KyThucTap.objects.all().order_by('-id')
    if is_gvpt:
        if tab == 'all':
            hoidongs = HoiDong.objects.select_related('ky').all()
        else:
            hoidongs = HoiDong.objects.filter(hoidong_giangvien__giang_vien=gv).select_related('ky').distinct()
    else:
        hoidongs = HoiDong.objects.filter(hoidong_giangvien__giang_vien=gv).select_related('ky').distinct()
    if ky_id:
        hoidongs = hoidongs.filter(ky_id=ky_id)
    hoidongs = hoidongs.order_by('-ngay_bao_ve')
    current_ky = KyThucTap.objects.filter(id=ky_id).first() if ky_id else (ky_list.first() if ky_list.exists() else None)
    context = {
        "hoidongs": hoidongs,
        "current_page": "hoi_dong_bv",
        "is_gvpt": is_gvpt,
        "ky_list": ky_list,
        "current_ky": current_ky,
        "tab": tab,
    }
    return render(request, "TruongBoMon/hoi_dong_list.html", context)

def hoi_dong_detail(request, id):
    hoidong = get_object_or_404(HoiDong, id=id)
    is_gvpt = get_is_gvpt(request)
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    if not is_gvpt and gv:
        if not HoiDong_GiangVien.objects.filter(hoi_dong=hoidong, giang_vien=gv).exists():
            return redirect("TruongBoMon:hoi_dong_list")
    
    # Ở đây chúng ta tin tưởng vào database đã được fix sạch sẽ ở step trước
    now = timezone.now()
    is_in_time = False
    
    # Lấy giờ phút giây hiện tại để so sánh
    current_time = now.time()
    if hoidong.thoi_gian_bat_dau and hoidong.thoi_gian_ket_thuc:
        # Kiểm tra đúng ngày và trong khoảng giờ
        is_in_time = (hoidong.ngay_bao_ve == now.date()) and \
                     (hoidong.thoi_gian_bat_dau <= current_time <= hoidong.thoi_gian_ket_thuc)

    giangviens = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong).select_related('giang_vien')
    sv_list = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong).select_related('sinh_vien')
    data_sv = []
    for item in sv_list:
        sv = item.sinh_vien
        bd = BangDiem.objects.filter(sinh_vien=sv, ky=hoidong.ky).first()
        diem_value = bd.diem_bao_cao if bd else None
        data_sv.append({
            "sv": sv,
            "diem": diem_value,
        })
    context = {
        "hoidong": hoidong,
        "giangviens": giangviens,
        "sinhviens": data_sv,
        "is_gvpt": is_gvpt,
        "current_page": "hoi_dong_bv",
        "is_in_time": is_in_time,
        "now": now,
    }
    return render(request, "TruongBoMon/hoi_dong_detail.html", context)

@require_POST
def cham_diem_hoi_dong(request, id, ma_sv):
    hoidong = get_object_or_404(HoiDong, id=id)
    sv = get_object_or_404(SinhVien, ma_sv=ma_sv)
    now = timezone.now()
    current_time = now.time()
    
    if not (hoidong.thoi_gian_bat_dau and hoidong.thoi_gian_ket_thuc):
        messages.error(request, "Hội đồng chưa thiết lập thời gian bảo vệ.")
        return redirect("TruongBoMon:hoi_dong_detail", id=id)
    if not (hoidong.thoi_gian_bat_dau <= current_time <= hoidong.thoi_gian_ket_thuc) or \
       hoidong.ngay_bao_ve != now.date():
        messages.error(request, "Chỉ được chấm điểm trong thời gian bảo vệ của hội đồng.")
        return redirect("TruongBoMon:hoi_dong_detail", id=id)
    diem_str = request.POST.get("diem")
    if diem_str:
        bd, _ = BangDiem.objects.update_or_create(
            sinh_vien=sv,
            ky=hoidong.ky,
            defaults={'diem_bao_cao': float(diem_str)}
        )
        if hasattr(bd, 'calculate_total'):
            bd.calculate_total()
    return redirect("TruongBoMon:hoi_dong_detail", id=id)


from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

@login_required
def update_password(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, "Mật khẩu hiện tại không đúng.", extra_tags='pwd_error')
            return redirect('TruongBoMon:truongboomon_home')
        
        if new_password != confirm_password:
            messages.error(request, "Xác nhận mật khẩu không khớp.", extra_tags='pwd_error')
            return redirect('TruongBoMon:truongboomon_home')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Thay đổi mật khẩu thành công!", extra_tags='pwd_success')
        
    return redirect('TruongBoMon:truongboomon_home')
