from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from Home.models import GiangVien, KyThucTap, PhanCongGVPT, PhanCongGVHD


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
