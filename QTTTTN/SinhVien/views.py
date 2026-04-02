from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from Home.models import (NhiemVu, SinhVien, BaiNop, NguoiDung,
                         MauKhaoSat, TaiLieu, PhanCongGVHD,
                         PhieuTraLoi, ChiTietTraLoi, BangDiem,
                         HoiDong, HoiDong_SinhVien)


@login_required
def home(request):
    try:
        nguoi_dung = NguoiDung.objects.get(user=request.user)
        sinh_vien = SinhVien.objects.select_related('ky_hien_tai').get(ma_sv=nguoi_dung.username)
        ky_hien_tai = sinh_vien.ky_hien_tai
    except (NguoiDung.DoesNotExist, SinhVien.DoesNotExist):
        return render(request, 'SinhVien/dashboard.html', {'error': 'Không tìm thấy hồ sơ sinh viên'})

    giang_vien = None
    if ky_hien_tai:
        phan_cong = PhanCongGVHD.objects.filter(sinh_vien=sinh_vien, ky=ky_hien_tai).first()
        if phan_cong:
            giang_vien = phan_cong.giang_vien

    danh_sach_nhiem_vu = []
    if ky_hien_tai:
        now = timezone.now()
        # 1. Lấy Nhiệm vụ
        tasks = NhiemVu.objects.filter(ky=ky_hien_tai, han_nop__gte=now).order_by('han_nop')
        for t in tasks:
            delta = t.han_nop - now
            days = delta.days
            if days > 2:
                loai = "warning"
                con_lai = f"CÒN {days} NGÀY"
            elif days >= 1 and days <= 2:
                loai = "danger"
                con_lai = f"CÒN {days} NGÀY"
            else:
                loai = "danger"
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                if minutes > 0:
                    con_lai = f"CÒN {hours} GIỜ {minutes} PHÚT"
                else:
                    con_lai = f"CÒN {hours} GIỜ"

            danh_sach_nhiem_vu.append({
                'id': t.id,
                'ten': t.ten_nhiem_vu,
                'han_chot': t.han_nop.strftime('%d/%m/%Y'),
                'con_lai': con_lai,
                'loai': loai,
                'url': reverse('SinhVien:nhiem_vu_page'),
                'is_form': False,
                'sort_time': t.han_nop
            })

        # 2. Lấy Khảo sát
        forms = MauKhaoSat.objects.filter(ky=ky_hien_tai)
        now_date = timezone.now().date()
        for f in forms:
            if (f.ngay_bat_dau and f.ngay_bat_dau > now_date) or (f.ngay_ket_thuc and f.ngay_ket_thuc < now_date):
                continue
            if PhieuTraLoi.objects.filter(mau_khao_sat=f, sinh_vien=sinh_vien).exists():
                continue

            con_lai_str = "--"
            loai = "normal"
            if f.ngay_ket_thuc:
                delta = timezone.make_aware(timezone.datetime.combine(f.ngay_ket_thuc, timezone.datetime.max.time())) - now
                days = delta.days
                if days > 2:
                    loai = "warning"
                    con_lai_str = f"CÒN {days} NGÀY"
                elif days >= 1 and days <= 2:
                    loai = "danger"
                    con_lai_str = f"CÒN {days} NGÀY"
                elif days == 0:
                    loai = "danger"
                    hours = delta.seconds // 3600
                    minutes = (delta.seconds % 3600) // 60
                    if minutes > 0:
                        con_lai_str = f"CÒN {hours} GIỜ {minutes} PHÚT"
                    else:
                        con_lai_str = f"CÒN {hours} GIỜ"
                else:
                    con_lai_str = "Hết hạn"
                    loai = "danger"

            danh_sach_nhiem_vu.append({
                'id': f.id,
                'public_id': f.public_id,
                'ten': f.ten_form,
                'han_chot': f.ngay_ket_thuc.strftime('%d/%m/%Y') if f.ngay_ket_thuc else '--/--/----',
                'con_lai': con_lai_str,
                'loai': loai,
                'url': reverse('SinhVien:dien_form', args=[f.public_id]),
                'is_form': True,
                'sort_time': timezone.make_aware(timezone.datetime.combine(f.ngay_ket_thuc, timezone.datetime.max.time())) if f.ngay_ket_thuc else now
            })

    # ----------------------------------------------------
    # Lấy thông tin thực tập (Dựa trên form khảo sát)
    # ----------------------------------------------------
    thong_tin_thuc_tap = {
        'ten_cong_ty': None,
        'dia_chi': None
    }

    if ky_hien_tai:
        # Lấy câu trả lời mới nhất
        answers = ChiTietTraLoi.objects.filter(
            phieu_tra_loi__sinh_vien=sinh_vien,
            phieu_tra_loi__mau_khao_sat__ky=ky_hien_tai
        ).select_related('cau_hoi').order_by('-phieu_tra_loi__thoi_gian_nop')

        for ans in answers:
            tag = ans.cau_hoi.system_tag
            if not tag: continue

            # Khớp chính xác với các value trong thẻ <option> của trang tạo form
            if tag == 'don_vi_tt' and not thong_tin_thuc_tap['ten_cong_ty']:
                thong_tin_thuc_tap['ten_cong_ty'] = ans.gia_tri

            elif tag == 'dia_diem_dv' and not thong_tin_thuc_tap['dia_chi']:
                thong_tin_thuc_tap['dia_chi'] = ans.gia_tri

            # Nếu đã tìm thấy cả 2 thì dừng
            if thong_tin_thuc_tap['ten_cong_ty'] and thong_tin_thuc_tap['dia_chi']:
                break

    # Lấy thông tin hội đồng bảo vệ của sinh viên
    hoi_dong = None
    if ky_hien_tai:
        hd_sv = HoiDong_SinhVien.objects.filter(
            sinh_vien=sinh_vien,
            hoi_dong__ky=ky_hien_tai
        ).select_related('hoi_dong').first()
        if hd_sv:
            hoi_dong = hd_sv.hoi_dong

    context = {
        'current_page': 'home',
        'sinh_vien': sinh_vien,
        'ky_hien_tai': ky_hien_tai,
        'giang_vien': giang_vien,
        'danh_sach_nhiem_vu': danh_sach_nhiem_vu,
        'tai_lieu': TaiLieu.objects.filter(ky=ky_hien_tai).order_by('-ngay_cap_nhat')[:5],
        'thong_tin_thuc_tap': thong_tin_thuc_tap,
        'hoi_dong': hoi_dong,
    }
    return render(request, 'SinhVien/dashboard.html', context)


def nhiem_vu(request):
    try:
        nguoi_dung = NguoiDung.objects.get(user=request.user)
        sinh_vien = SinhVien.objects.get(ma_sv=nguoi_dung.username)
    except (NguoiDung.DoesNotExist, SinhVien.DoesNotExist):
        return render(request, "SinhVien/nhiemvu_nopbai.html", {
            "page_obj": [],
            "current_page": "nhiem_vu"
        })

    tasks = NhiemVu.objects.filter(
        ky=sinh_vien.ky_hien_tai
    ).order_by('-han_nop')

    status_filter = request.GET.get('status', 'all')
    task_list = []

    # Gắn trạng thái bài nộp vào nhiệm vụ
    for task in tasks:
        # Lấy bản ghi bài nộp thực sự từ DB
        bainop = BaiNop.objects.filter(nhiem_vu=task, sinh_vien=sinh_vien).first()

        if bainop:
            task.trang_thai = "done"
            # Đính thẳng object bainop vào task để Template lấy dữ liệu
            task.thong_tin_nop = bainop
        else:
            if timezone.now() > task.han_nop:
                task.trang_thai = "late"
            else:
                task.trang_thai = "pending"

        if status_filter == 'done' and task.trang_thai != 'done':
            continue
        if status_filter == 'pending' and task.trang_thai != 'pending':
            continue
        if status_filter == 'late' and task.trang_thai != 'late':
            continue
            
        task_list.append(task)

    # Phân trang
    paginator = Paginator(task_list, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "current_page": "nhiem_vu"
    }

    # --- QUAN TRỌNG: ĐÃ THÊM LỆNH RETURN Ở ĐÂY ---
    return render(request, "SinhVien/nhiemvu_nopbai.html", context)


def xem_diem(request):
    try:
        nguoi_dung = NguoiDung.objects.get(user=request.user)
        sinh_vien = SinhVien.objects.select_related('ky_hien_tai').get(ma_sv=nguoi_dung.username)
        ky_hien_tai = sinh_vien.ky_hien_tai

        # Lấy điểm từ BangDiem
        bang_diem = BangDiem.objects.filter(sinh_vien=sinh_vien, ky=ky_hien_tai).first()
        diem_tk = bang_diem.diem_tong_ket if (bang_diem and bang_diem.diem_tong_ket is not None) else "Chưa có"

    except (NguoiDung.DoesNotExist, SinhVien.DoesNotExist):
        return render(request, 'SinhVien/xem_diem.html', {'error': 'Không tìm thấy hồ sơ'})

    # --- LOGIC LẤY THÔNG TIN TỪ FORM KHẢO SÁT ---
    thong_tin_thuc_tap = {
        'ten_cong_ty': None,
        'dia_chi': None,
        'de_tai': None  # <--- Thêm mới cái này
    }

    if ky_hien_tai:
        # Lấy tất cả câu trả lời của SV này trong kỳ này
        answers = ChiTietTraLoi.objects.filter(
            phieu_tra_loi__sinh_vien=sinh_vien,
            phieu_tra_loi__mau_khao_sat__ky=ky_hien_tai
        ).select_related('cau_hoi').order_by('-phieu_tra_loi__thoi_gian_nop')

        for ans in answers:
            tag = ans.cau_hoi.system_tag
            if not tag: continue

            if tag == 'don_vi_tt' and not thong_tin_thuc_tap['ten_cong_ty']:
                thong_tin_thuc_tap['ten_cong_ty'] = ans.gia_tri
            elif tag == 'dia_diem_dv' and not thong_tin_thuc_tap['dia_chi']:
                thong_tin_thuc_tap['dia_chi'] = ans.gia_tri
            elif tag == 'de_tai_tt' and not thong_tin_thuc_tap['de_tai']:  # <--- Quét tag de_tai_tt
                thong_tin_thuc_tap['de_tai'] = ans.gia_tri

            # Nếu tìm đủ rồi thì dừng vòng lặp cho nhẹ máy
            if all(thong_tin_thuc_tap.values()):
                break

    context = {
        'current_page': 'xem_diem',
        'sinh_vien': sinh_vien,
        'diem_tk': diem_tk,
        'thong_tin_thuc_tap': thong_tin_thuc_tap
    }
    return render(request, 'SinhVien/xem_diem.html', context)




@login_required
def dien_form(request, public_id):
    mau_ks = get_object_or_404(MauKhaoSat, public_id=public_id)
    nguoi_dung = NguoiDung.objects.get(user=request.user)
    sinh_vien = SinhVien.objects.get(ma_sv=nguoi_dung.username)
    questions = mau_ks.cau_hoi.all().order_by('thu_tu')
    return render(request, 'GiangVien/public_form.html', {
        'form': mau_ks,
        'questions': questions,
        'sinh_vien': sinh_vien
    })


@login_required
def submit_form(request, public_id):
    if request.method == "POST":
        mau_ks = get_object_or_404(MauKhaoSat, public_id=public_id)
        nguoi_dung = NguoiDung.objects.get(user=request.user)
        sinh_vien = SinhVien.objects.get(ma_sv=nguoi_dung.username)

        with transaction.atomic():
            # 1. Tạo phiếu trả lời chính
            phieu = PhieuTraLoi.objects.create(mau_khao_sat=mau_ks, sinh_vien=sinh_vien)

            # 2. Quét các câu hỏi để lấy dữ liệu từ POST
            for q in mau_ks.cau_hoi.all():
                field_name = f"question_{q.id}"
                ans_str = None

                if q.loai_cau_hoi == "LIKERT":
                    for t in q.tieuchi.all():
                        val = request.POST.get(f"{field_name}_{t.id}")
                        if val:
                            ChiTietTraLoi.objects.create(phieu_tra_loi=phieu, cau_hoi=q, gia_tri=f"{t.noi_dung}: {val}")
                elif q.loai_cau_hoi == "CHECKBOX":
                    vals = request.POST.getlist(f"{field_name}[]")
                    if vals:
                        ans_str = ", ".join(vals)
                        ChiTietTraLoi.objects.create(phieu_tra_loi=phieu, cau_hoi=q, gia_tri=ans_str)
                else:
                    val = request.POST.get(field_name)
                    if val:
                        ans_str = val
                        ChiTietTraLoi.objects.create(phieu_tra_loi=phieu, cau_hoi=q, gia_tri=val)

                # ==========================================
                # HOOK: CẬP NHẬT THÔNG TIN TỰ ĐỘNG
                # ==========================================
                if ans_str and q.system_tag:

                    # Cập nhật điểm doanh nghiệp vào BangDiem
                    if q.system_tag == "diem_doanh_nghiep":
                        try:
                            # Ép kiểu về float (thay dấu phẩy bằng dấu chấm nếu cần)
                            score = float(ans_str.replace(',', '.'))

                            # Tìm hoặc tạo bản ghi điểm cho SV này trong kỳ này
                            bang_diem, created = BangDiem.objects.update_or_create(
                                sinh_vien=sinh_vien,
                                ky=mau_ks.ky,
                                defaults={'diem_doanh_nghiep': score}
                            )
                            # Tự động tính lại tổng kết nếu đã đủ các đầu điểm khác
                            bang_diem.calculate_total()
                        except ValueError:
                            pass  # Bỏ qua nếu SV nhập không phải là số

                    # Cập nhật nơi thực tập vào hồ sơ SinhVien
                    elif q.system_tag == "don_vi_tt":
                        sinh_vien.noi_thuc_tap = ans_str
                        sinh_vien.save()

            messages.success(request, "success")
            return redirect('SinhVien:dien_form', public_id=public_id)

    return redirect('SinhVien:sinhvien_home')


def tong_hop_nxet(request):
    """View dành cho sinh viên tra cứu nhận xét đơn vị thực tập."""

    # Định nghĩa các tag cần lấy (Phải khớp với tag ông đã đặt ở app GiangVien)
    target_tags = ['don_vi_tt', 'email_don_vi', 'sdt_don_vi', 'nhan_xet_dv', 'loi_nhan_dv']

    # Lấy tất cả câu trả lời có gắn các tag này
    chi_tiet_answers = ChiTietTraLoi.objects.filter(
        cau_hoi__system_tag__in=target_tags
    ).select_related('phieu_tra_loi', 'cau_hoi')

    # Gom nhóm dữ liệu theo từng phiếu trả lời (mỗi phiếu là 1 đơn vị/1 SV)
    data_map = {}
    for ans in chi_tiet_answers:
        phieu_id = ans.phieu_tra_loi.id
        if phieu_id not in data_map:
            data_map[phieu_id] = {
                'don_vi': 'Chưa rõ',
                'email': '-',
                'sdt': '-',
                'nhan_xet': '',
                'loi_nhan': ''
            }

        tag = ans.cau_hoi.system_tag
        if tag == 'don_vi_tt':
            data_map[phieu_id]['don_vi'] = ans.gia_tri
        elif tag == 'email_don_vi':
            data_map[phieu_id]['email'] = ans.gia_tri
        elif tag == 'sdt_don_vi':
            data_map[phieu_id]['sdt'] = ans.gia_tri
        elif tag == 'nhan_xet_dv':
            data_map[phieu_id]['nhan_xet'] = ans.gia_tri
        elif tag == 'loi_nhan_dv':
            data_map[phieu_id]['loi_nhan'] = ans.gia_tri

    results_list = list(data_map.values())
    
    # ------------------
    # Xử lý TÌM KIẾM
    # ------------------
    search_query = request.GET.get('q', '').strip().lower()
    if search_query:
        # Lọc danh sách theo tên công ty hoặc nội dung nhận xét
        results_list = [
            item for item in results_list
            if search_query in item['don_vi'].lower() or search_query in item['nhan_xet'].lower()
        ]

    paginator = Paginator(results_list, 10) # Hiển thị 10 đơn vị 1 trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'results': page_obj,
        'page_obj': page_obj,
        'current_page': 'tra_cuu_don_vi',  # Để active menu nếu cần
        'search_query': search_query
    }
    return render(request, "SinhVien/tong_hop_nxet.html", context)


@login_required
def nop_bai_action(request):
    if request.method == "POST" and request.FILES.get('file_nop'):
        task_id = request.POST.get('task_id')
        file_obj = request.FILES['file_nop']

        nguoi_dung = NguoiDung.objects.get(user=request.user)
        sinh_vien = SinhVien.objects.get(ma_sv=nguoi_dung.username)
        nhiem_vu_obj = get_object_or_404(NhiemVu, id=task_id)

        # Lưu vào Database qua Model BaiNop
        # Django sẽ tự động lưu file vật lý vào thư mục /media/assignments/
        bai_nop, created = BaiNop.objects.update_or_create(
            nhiem_vu=nhiem_vu_obj,
            sinh_vien=sinh_vien,
            defaults={
                'file_path': file_obj,
                'ten_file': file_obj.name,
                'thoi_gian_nop': timezone.now(),
                'trang_thai': 'Đã nộp'
            }
        )
        messages.success(request, "Nộp bài thành công!")
    return redirect('SinhVien:nhiem_vu_page')