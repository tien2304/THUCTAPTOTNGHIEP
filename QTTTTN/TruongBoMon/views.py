from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from Home.models import (GiangVien, KyThucTap, PhanCongGVPT, PhanCongGVHD, HoiDong, 
                         HoiDong_GiangVien, HoiDong_SinhVien, BangDiem, SinhVien, TyLeDiem,
                         BaiNop, NhiemVu, PhieuTraLoi, ChiTietTraLoi, ChamDiemHoiDong)


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
                phan_congs = PhanCongGVPT.objects.filter(ky=ky)
                if phan_congs.exists():
                    pc = phan_congs.first()
                    messages.warning(request, f"{ky.ten_ky} đã được phân công cho {pc.giang_vien.ho_ten}. Mỗi kỳ chỉ được phép có 1 Giảng viên phụ trách!")
                else:
                    PhanCongGVPT.objects.create(giang_vien=gv, ky=ky)
                    messages.success(request, f"Đã phân công {gv.ho_ten} phụ trách {ky.ten_ky}!")
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
    # Luôn lấy học kỳ mới nhất (fix cứng)
    selected_ky = ky_list.first()
    selected_ky_id = selected_ky.id if selected_ky else None
        
    ds_sinh_vien = []
    if selected_ky:
        # Lấy toàn bộ sinh viên trong kỳ này
        sinh_vien_qs = SinhVien.objects.filter(ky_hien_tai=selected_ky).order_by('ma_sv')
        
        # Lấy toàn bộ phân công của kỳ này
        phan_cong_qs = PhanCongGVHD.objects.filter(ky=selected_ky).select_related('giang_vien', 'sinh_vien')
        phan_cong_dict = {pc.sinh_vien_id: pc for pc in phan_cong_qs}
        
        # Lấy khảo sát để lấy điểm tích lũy và lĩnh vực (hướng tiếp cận)
        # Tối ưu: Lấy toàn bộ ChiTietTraLoi liên quan
        answers_qs = ChiTietTraLoi.objects.filter(
            phieu_tra_loi__mau_khao_sat__ky=selected_ky,
            cau_hoi__system_tag__in=['diem_tich_luy', 'huong_tiep_can', 'gvhd_ttnn']
        ).select_related('phieu_tra_loi', 'cau_hoi')
        
        survey_data = {} # {ma_sv: {tag: "val1, val2"}}
        for ans in answers_qs:
            ma_sv = ans.phieu_tra_loi.sinh_vien_id
            tag = ans.cau_hoi.system_tag
            val = ans.gia_tri.strip() if ans.gia_tri else ""
            if not val: continue

            if ma_sv not in survey_data:
                survey_data[ma_sv] = {}
            
            # Lưu raw cho huong_tiep_can để xử lý linh_vuc sau
            if tag in survey_data[ma_sv]:
                survey_data[ma_sv][tag] += f"\n{val}"
            else:
                survey_data[ma_sv][tag] = val

        for sv in sinh_vien_qs:
            pc = phan_cong_dict.get(sv.ma_sv)
            sv_survey = survey_data.get(sv.ma_sv, {})
            
            gvhd_obj = pc.giang_vien if pc else None
            
            # Xử lý Lĩnh vực y hệt bên GiangVien/views.py
            raw_huong_tc = sv_survey.get('huong_tiep_can', '')
            linh_vuc_display = ""
            if raw_huong_tc:
                import re
                lines = raw_huong_tc.split('\n')
                seen_lv = set()
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    display_val = line
                    if '(' in line and ')' in line:
                        match = re.search(r'\((.*?)\)', line)
                        if match: display_val = match.group(1)
                    elif ',' in line:
                        display_val = line.split(',')[-1].strip()
                    
                    if display_val not in seen_lv:
                        seen_lv.add(display_val)
                        if linh_vuc_display:
                            linh_vuc_display += f"\n{display_val}"
                        else:
                            linh_vuc_display = display_val
            
            # Lấy thông tin nhóm
            group_val = sv_survey.get('group', '')
            if not group_val or group_val.strip().lower() == 'không':
                group_val = sv_survey.get('hinh_thuc_nhom', '')
            
            if group_val and group_val.strip().lower() == 'không':
                group_val = ''

            ds_sinh_vien.append({
                'ma_sv': sv.ma_sv,
                'ho_ten': sv.ho_ten,
                'lop': sv.lop,
                'diem_tich_luy': sv_survey.get('diem_tich_luy', '—'),
                'linh_vuc': linh_vuc_display or '—',
                'gvhd_ttnn': sv_survey.get('gvhd_ttnn', '—'),
                'gvhd': gvhd_obj,
                'trang_thai': pc.trang_thai if pc else 0,
                'pc_id': pc.id if pc else None,
                'group': group_val,
                'hinh_thuc': 'Nhóm' if group_val else 'Cá nhân',
            })

    # Đếm số lượng đã duyệt/tổng cộng để hiển thị thống kê
    tong_cong = len(ds_sinh_vien)
    da_duyet = sum(1 for item in ds_sinh_vien if item['trang_thai'] == 2)
    cho_duyet = sum(1 for item in ds_sinh_vien if item['trang_thai'] == 1)

    # Lấy danh sách giảng viên CÓ PHÂN CÔNG trong kỳ này (để hiển thị trong dropdown lọc)
    gv_ids_co_phan_cong = phan_cong_qs.values_list('giang_vien_id', flat=True).distinct()
    ds_giang_vien_filter = GiangVien.objects.filter(ma_gv__in=gv_ids_co_phan_cong).order_by('ho_ten')
    
    # Thống kê số lượng phân công mỗi giảng viên (giữ nguyên cho stats panel)
    assignment_stats = {}
    for pc in phan_cong_qs:
        gv_id = pc.giang_vien_id
        assignment_stats[gv_id] = assignment_stats.get(gv_id, 0) + 1

    ds_thong_ke_gv = []
    # Dùng toàn bộ ds_giang_vien (hoặc chỉ những người có phân công) cho stats panel
    for gv in GiangVien.objects.filter(ma_gv__in=gv_ids_co_phan_cong):
        count = assignment_stats.get(gv.ma_gv, 0)
        # Viết tắt học vị
        hv = gv.hoc_vi
        if hv == 'Thạc sĩ': hv = 'ThS.'
        elif hv == 'Tiến sĩ': hv = 'TS.'
        elif hv == 'Tiến sĩ Khoa học': hv = 'TSKH.'
        elif hv == 'Phó Giáo sư': hv = 'PGS.TS.'
        elif hv == 'Giáo sư': hv = 'GS.TS.'
        
        ds_thong_ke_gv.append({
            'ho_ten': gv.ho_ten,
            'hoc_vi_tat': hv,
            'count': count
        })
    ds_thong_ke_gv.sort(key=lambda x: x['count'], reverse=True)

    # Lấy danh sách Lĩnh vực duy nhất để lọc
    unique_linh_vuc = set()
    for item in ds_sinh_vien:
        lv = item.get('linh_vuc', '')
        if lv and lv != '—':
            for line in lv.split('\n'):
                if line.strip():
                    unique_linh_vuc.add(line.strip())

    context = {
        'current_page': 'duyet_gvhd',
        'ky_list': ky_list,
        'selected_ky': selected_ky,
        'selected_ky_id': selected_ky_id,
        'selected_ky_ten': selected_ky.ten_ky if selected_ky else "Chưa có học kỳ",
        'ds_sinh_vien': ds_sinh_vien,
        'ds_giang_vien': ds_giang_vien_filter,
        'ds_thong_ke_gv': ds_thong_ke_gv,
        'unique_linh_vuc': sorted(list(unique_linh_vuc)),
        'stats': {
            'tong_cong': tong_cong,
            'da_duyet': da_duyet,
            'cho_duyet': cho_duyet,
        }
    }
    return render(request, 'TruongBoMon/duyet_gvhd.html', context)

@csrf_exempt
def update_gvhd_ajax(request):
    """Cập nhật Giảng viên hướng dẫn cho sinh viên qua AJAX."""
    if request.method == 'POST':
        ma_sv = request.POST.get('ma_sv')
        ma_gv = request.POST.get('ma_gv')
        ky_id = request.POST.get('ky_id')
        
        try:
            ky = KyThucTap.objects.get(id=ky_id)
            sinh_vien = SinhVien.objects.get(ma_sv=ma_sv)
            
            # Xử lý trường hợp ma_gv rỗng (bỏ phân công)
            if not ma_gv:
                PhanCongGVHD.objects.filter(sinh_vien=sinh_vien, ky=ky).delete()
            else:
                giang_vien = GiangVien.objects.get(ma_gv=ma_gv)
                # Cập nhật hoặc tạo mới phân công
                phan_cong, created = PhanCongGVHD.objects.update_or_create(
                    sinh_vien=sinh_vien,
                    ky=ky,
                    defaults={'giang_vien': giang_vien, 'trang_thai': 1} # Mặc định chờ duyệt khi sửa
                )
            
            return JsonResponse({'status': 'success', 'message': 'Cập nhật phân công thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def action_duyet_gvhd(request):
    if request.method == 'POST':
        ky_id = request.POST.get('ky_id')
        ma_gv = request.POST.get('ma_gv')
        action = request.POST.get('action')
        
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
            ds_phan_cong.update(trang_thai=2)
            messages.success(request, 'Đã phê duyệt phân công thành công!')
        elif action == 'reject':
            ds_phan_cong.update(trang_thai=3)
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
        
    # Lấy danh sách GV và SV toàn cầu cho việc chọn thêm sau này (để modal load nhanh)
    available_gv = GiangVien.objects.all().order_by('ho_ten')
    available_sv = SinhVien.objects.filter(ky_hien_tai=selected_ky).order_by('ma_sv') if selected_ky else []

    ds_hoidong = []
    if selected_ky:
        hoidong_qs = HoiDong.objects.filter(ky=selected_ky).order_by('ngay_bao_ve', 'thoi_gian_bat_dau')
        
        for hd in hoidong_qs:
            gv_list = HoiDong_GiangVien.objects.filter(hoi_dong=hd).select_related('giang_vien')
            sv_list = HoiDong_SinhVien.objects.filter(hoi_dong=hd).select_related('sinh_vien')
            
            # Chỉ hiển thị giờ nếu Giáo vụ đã nhập đầy đủ (Giờ và Địa điểm)
            is_ready = hd.thoi_gian_bat_dau and hd.thoi_gian_ket_thuc and hd.dia_diem
            
            ds_hoidong.append({
                'id': hd.id,
                'ten': hd.ten_hoi_dong,
                'thoi_gian_bat_dau': hd.thoi_gian_bat_dau,
                'thoi_gian_ket_thuc': hd.thoi_gian_ket_thuc,
                'thoi_gian': f"{hd.thoi_gian_bat_dau.strftime('%H:%M')} - {hd.thoi_gian_ket_thuc.strftime('%H:%M')}" if is_ready else "Chưa thiết lập",
                'ngay_bao_ve': hd.ngay_bao_ve,
                'dia_diem': hd.dia_diem if is_ready else "",
                'gv_count': gv_list.count(),
                'sv_count': sv_list.count(),
                'giang_vien': [g.giang_vien for g in gv_list],
                'sinh_vien': [s.sinh_vien for s in sv_list],
                'trang_thai': hd.trang_thai,
                'is_ready': is_ready
            })
            
    context = {
        'current_page': 'duyet_hoi_dong',
        'all_ky': all_ky,
        'selected_ky': selected_ky,
        'selected_ky_id': selected_ky.id if selected_ky else None,
        'ds_hoidong': ds_hoidong,
        'available_gv': available_gv,
        'available_sv': available_sv,
    }
    return render(request, 'TruongBoMon/duyet_hoidong.html', context)

def hoidong_detail_ajax(request, hd_id):
    """Lấy chi tiết hội đồng (partial HTML) để hiển thị trong panel bên phải."""
    hoidong = get_object_or_404(HoiDong, id=hd_id)
    ds_giang_vien = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong).select_related('giang_vien')
    ds_sinh_vien = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong).select_related('sinh_vien')
    
    current_gv_ids = ds_giang_vien.values_list('giang_vien_id', flat=True)
    available_gv = GiangVien.objects.exclude(ma_gv__in=current_gv_ids).order_by('ho_ten')
    
    current_sv_ids = HoiDong_SinhVien.objects.filter(hoi_dong__ky=hoidong.ky).values_list('sinh_vien_id', flat=True)
    available_sv = SinhVien.objects.filter(ky_hien_tai=hoidong.ky).exclude(ma_sv__in=current_sv_ids).order_by('ma_sv')

    context = {
        'hoidong': hoidong,
        'ds_giang_vien': ds_giang_vien,
        'ds_sinh_vien': ds_sinh_vien,
        'available_gv': available_gv,
        'available_sv': available_sv,
    }
    return render(request, 'TruongBoMon/hoidong_detail_partial.html', context)

def chi_tiet_hoidong_view(request, hd_id):
    """Trang chi tiết Hội đồng – Trưởng Bộ Môn."""
    hoidong = HoiDong.objects.filter(id=hd_id).select_related('ky').first()
    
    if not hoidong:
        messages.error(request, "Không tìm thấy hội đồng này.")
        return redirect('TruongBoMon:duyet_hoidong')
        
    ds_giang_vien = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong).select_related('giang_vien')
    ds_sinh_vien_raw = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong).select_related('sinh_vien')
    
    # Lấy thông tin GVHD cho từng sinh viên
    ds_sinh_vien = []
    gvhd_ids_in_council = []
    for item in ds_sinh_vien_raw:
        sv = item.sinh_vien
        # Tìm GVHD trong kỳ này
        pc = PhanCongGVHD.objects.filter(sinh_vien=sv, ky=hoidong.ky, trang_thai=2).select_related('giang_vien').first()
        ds_sinh_vien.append({
            'sinh_vien': sv,
            'gvhd': pc.giang_vien if pc else None
        })
        if pc and pc.giang_vien:
            gvhd_ids_in_council.append(pc.giang_vien.ma_gv)
    
    # 1. Xử lý danh sách giảng viên để chọn thêm
    current_gv_ids = list(ds_giang_vien.values_list('giang_vien_id', flat=True))
    # Loại bỏ giảng viên là GVHD của sinh viên trong hội đồng này
    exclude_gv_ids = set(current_gv_ids + gvhd_ids_in_council)
    available_gv = GiangVien.objects.exclude(ma_gv__in=exclude_gv_ids).order_by('ho_ten')
    
    # 2. Xử lý danh sách sinh viên để chọn thêm
    current_sv_ids = HoiDong_SinhVien.objects.filter(hoi_dong__ky=hoidong.ky).values_list('sinh_vien_id', flat=True)
    
    # Tìm các sinh viên có GVHD nằm trong hội đồng này
    sv_ids_with_gvhd_in_council = PhanCongGVHD.objects.filter(
        ky=hoidong.ky,
        trang_thai=2,
        giang_vien_id__in=current_gv_ids
    ).values_list('sinh_vien_id', flat=True)
    
    # Danh sách sinh viên bị loại trừ: đã có hội đồng HOẶC có GVHD trong hội đồng này
    exclude_sv_ids = set(list(current_sv_ids) + list(sv_ids_with_gvhd_in_council))
    available_sv = SinhVien.objects.filter(ky_hien_tai=hoidong.ky).exclude(ma_sv__in=exclude_sv_ids).order_by('ma_sv')
    
    context = {
        'current_page': 'duyet_hoi_dong',
        'hoidong': hoidong,
        'ds_giang_vien': ds_giang_vien,
        'ds_sinh_vien': ds_sinh_vien,
        'available_gv': available_gv,
        'available_sv': available_sv,
    }
    return render(request, 'TruongBoMon/chi_tiet_hoidong.html', context)

@require_POST
@csrf_exempt
def add_gv_hoidong_ajax(request, hd_id):
    ma_gv = request.POST.get('ma_gv')
    hoidong = get_object_or_404(HoiDong, id=hd_id)
    gv = get_object_or_404(GiangVien, ma_gv=ma_gv)
    
    HoiDong_GiangVien.objects.get_or_create(hoi_dong=hoidong, giang_vien=gv)
    return JsonResponse({'status': 'success'})

@require_POST
@csrf_exempt
def remove_gv_hoidong_ajax(request, hd_id):
    ma_gv = request.POST.get('ma_gv')
    HoiDong_GiangVien.objects.filter(hoi_dong_id=hd_id, giang_vien_id=ma_gv).delete()
    return JsonResponse({'status': 'success'})

@require_POST
@csrf_exempt
def add_sv_hoidong_ajax(request, hd_id):
    ma_sv = request.POST.get('ma_sv')
    hoidong = get_object_or_404(HoiDong, id=hd_id)
    sv = get_object_or_404(SinhVien, ma_sv=ma_sv)
    
    HoiDong_SinhVien.objects.get_or_create(hoi_dong=hoidong, sinh_vien=sv)
    return JsonResponse({'status': 'success'})

@require_POST
@csrf_exempt
def remove_sv_hoidong_ajax(request, hd_id):
    ma_sv = request.POST.get('ma_sv')
    HoiDong_SinhVien.objects.filter(hoi_dong_id=hd_id, sinh_vien_id=ma_sv).delete()
    return JsonResponse({'status': 'success'})

@require_POST
@csrf_exempt
def approve_hoidong_ajax(request, hd_id):
    try:
        hoidong = HoiDong.objects.get(id=hd_id)
        hoidong.trang_thai = 2  # Đã chuyển sang trạng thái Đã phê duyệt
        hoidong.save()
        return JsonResponse({'status': 'success'})
    except HoiDong.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Hội đồng không tồn tại.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
@csrf_exempt
def approve_all_hoidong_ajax(request):
    try:
        # Lấy kỳ mới nhất
        selected_ky = KyThucTap.objects.all().order_by('-id').first()
        if not selected_ky:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy học kỳ.'})
            
        # Phê duyệt tất cả hội đồng thuộc kỳ này mà đang ở trạng thái Chờ duyệt (1)
        HoiDong.objects.filter(ky=selected_ky, trang_thai=1).update(trang_thai=2)
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


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

def cong_bo_diem_action(request, ky_id):
    ky = get_object_or_404(KyThucTap, id=ky_id)
    if ky.cong_bo_diem == 2:
        ky.cong_bo_diem = 1
    else:
        ky.cong_bo_diem = 2
    ky.save()
    
    status = "CÔNG BỐ" if ky.cong_bo_diem == 2 else "HỦY CÔNG BỐ"
    messages.success(request, f"{ky.ten_ky} đã được {status} thành công!")
    return redirect(f"{reverse('TruongBoMon:diem_view')}?ky_id={ky_id}")

def cau_hinh_diem_view(request):
    """Trang cấu hình tỷ lệ điểm – Trưởng Bộ Môn."""
    # PHẦN XÓA (GET)
    delete_id = request.GET.get('delete_id')
    if delete_id:
        TyLeDiem.objects.filter(id=delete_id).delete()
        messages.success(request, "Đã xoá cấu hình điểm thành công!")
        return redirect('TruongBoMon:cau_hinh_diem')

    if request.method == "POST":
        ky_id = request.POST.get('ky_id')
        gvhd_weight = float(request.POST.get('gvhd', 40))
        hoidong_weight = float(request.POST.get('hoidong', 40))
        dn_weight = float(request.POST.get('dn', 20))

        # Kiểm tra tổng trọng số (không được lớn hơn 100)
        total = gvhd_weight + hoidong_weight + dn_weight
        if total > 100:
            messages.error(request, f"Tổng tỷ lệ không được lớn hơn 100%.")
            return redirect('TruongBoMon:cau_hinh_diem')

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
    query = request.GET.get("q", "")
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
    bd.calculate_total()
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
    
    # Lọc chỉ những hội đồng mà giảng viên này tham gia
    hoidongs = HoiDong.objects.filter(
        hoidong_giangvien__giang_vien__ma_gv=request.user.username
    ).distinct()
    
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
    now = timezone.localtime(timezone.now())
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
    # Tìm đúng thông tin giảng viên để lấy mã GV (ví dụ: GV00001)
    gv_profile = GiangVien.objects.filter(ma_gv=request.user.username).first()
    ma_gv_chuan = gv_profile.ma_gv if gv_profile else request.user.username

    for item in sv_list:
        sv = item.sinh_vien
        
        # Truy vấn dùng mã GV đã chuẩn hóa
        cham_diem = ChamDiemHoiDong.objects.filter(
            hoi_dong_id=hoidong.id,
            sinh_vien_id=sv.ma_sv,
            giang_vien_id=ma_gv_chuan
        ).first()
        
        data_sv.append({
            "sv": sv,
            "diem": cham_diem.diem if cham_diem else None
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
    now = timezone.localtime(timezone.now())
    current_time = now.time()
    
    if not (hoidong.thoi_gian_bat_dau and hoidong.thoi_gian_ket_thuc):
        return JsonResponse({"status": "error", "message": "Hội đồng chưa thiết lập thời gian bảo vệ."})

    if not (hoidong.thoi_gian_bat_dau <= current_time <= hoidong.thoi_gian_ket_thuc) or \
       hoidong.ngay_bao_ve != now.date():
        return JsonResponse({"status": "error", "message": "Chỉ được chấm điểm trong thời gian bảo vệ của hội đồng."})

    diem_str = request.POST.get("diem")
    if diem_str:
        try:
            diem_val = float(diem_str)
            
            # 1. Lưu vào bảng điểm hội đồng (để biết ai chấm)
            ma_gv = request.user.username
            gv = GiangVien.objects.filter(ma_gv__iexact=ma_gv).first()
            
            if not gv:
                return JsonResponse({"status": "error", "message": f"Không tìm thấy thông tin giảng viên cho tài khoản: {ma_gv}"})

            ChamDiemHoiDong.objects.update_or_create(
                hoi_dong=hoidong,
                sinh_vien=sv,
                giang_vien=gv,
                defaults={'diem': diem_val}
            )

            # 2. Đồng bộ sang bảng điểm tổng
            bd, _ = BangDiem.objects.update_or_create(
                sinh_vien=sv,
                ky=hoidong.ky,
                defaults={'diem_bao_cao': diem_val}
            )
            if hasattr(bd, 'calculate_total'):
                bd.calculate_total()
            return JsonResponse({"status": "success", "message": "Đã lưu điểm thành công."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Dữ liệu không hợp lệ."})


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
