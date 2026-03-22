from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from Home.models import (NhiemVu, SinhVien, BaiNop, NguoiDung,
                         MauKhaoSat, TaiLieu, PhanCongGVHD, PhieuTraLoi, ChiTietTraLoi)


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
            loai = "danger" if days < 1 else ("warning" if days <= 3 else "normal")
            con_lai = f"{days} NGÀY" if days > 0 else f"{int(delta.seconds / 3600)} GIỜ"
            danh_sach_nhiem_vu.append({
                'id': t.id,
                'ten': t.ten_nhiem_vu,
                'han_chot': t.han_nop.strftime('%d/%m/%Y'),
                'con_lai': con_lai,
                'loai': loai,
                'url': reverse('SinhVien:nhiem_vu_page'),
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
                days = (f.ngay_ket_thuc - now_date).days
                con_lai_str = f"{days} NGÀY" if days > 0 else "Hết hạn"
                loai = "danger" if days <= 1 else ("warning" if days <= 3 else "normal")

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

    context = {
        'current_page': 'home',
        'sinh_vien': sinh_vien,
        'ky_hien_tai': ky_hien_tai,
        'giang_vien': giang_vien,
        'danh_sach_nhiem_vu': danh_sach_nhiem_vu,
        'tai_lieu': TaiLieu.objects.filter(ky=ky_hien_tai).order_by('-ngay_cap_nhat')[:5]
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

    # Gắn trạng thái bài nộp vào nhiệm vụ
    for task in tasks:
        bainop = BaiNop.objects.filter(
            nhiem_vu=task,
            sinh_vien=sinh_vien
        ).first()

        if bainop:
            task.trang_thai = "done"
        else:
            if timezone.now() > task.han_nop:
                task.trang_thai = "late"
            else:
                task.trang_thai = "pending"

    # Phân trang
    paginator = Paginator(tasks, 4)
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
        sinh_vien = SinhVien.objects.get(ma_sv=nguoi_dung.username)
        # Kiểm tra xem có thuộc tính cong_ty không
        cong_ty = sinh_vien.cong_ty if hasattr(sinh_vien, 'cong_ty') else None
    except (NguoiDung.DoesNotExist, SinhVien.DoesNotExist):
        sinh_vien = None
        cong_ty = None

    context = {
        'current_page': 'xem_diem',
        'sinh_vien': sinh_vien,
        'cong_ty': cong_ty
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
            # Tạo phiếu trả lời chính
            phieu = PhieuTraLoi.objects.create(mau_khao_sat=mau_ks, sinh_vien=sinh_vien)

            # Quét các câu hỏi để lấy dữ liệu từ POST
            for q in mau_ks.cau_hoi.all():
                field_name = f"question_{q.id}"
                
                ans_str = None # Biến này giữ nguyên text sinh viên nộp để dùng cho việc cập nhật Model

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
                # Tận dụng system_tag từ câu hỏi và ans_str (câu trả lời) để cập nhật thẳng vào CSDL.
                if ans_str and q.system_tag:
                    
                    # Ví dụ 1: Nếu tag là 'don_vi' -> Chèn tên thực tập vào SinhVien
                    if q.system_tag == "don_vi":
                        pass
                        # Mở comment dòng dưới nếu SinhVien đã có trường cong_ty
                        # sinh_vien.cong_ty = ans_str
                        
                    # Ví dụ 2: Nếu tag là 'sdt' -> Cập nhật số điện thoại
                    elif q.system_tag == "sdt":
                        pass
                        # sinh_vien.so_dien_thoai = ans_str
                        
                    # Ví dụ 3: Nếu tag là GVHD -> Tạo/Sửa dòng trong PhanCongGVHD
                    elif q.system_tag == "chon_gvhd":
                        pass
                        """
                        gv = GiangVien.objects.filter(ho_ten=ans_str).first()
                        if gv:
                            PhanCongGVHD.objects.update_or_create(
                                sinh_vien=sinh_vien,
                                ky=mau_ks.ky,
                                defaults={'giang_vien': gv}
                            )
                        """

            # Lệnh save tổng này chỉ nên mở khi SinhVien thực sự có cập nhật
            # sinh_vien.save()

            # Gắn tin nhắn thành công để kích hoạt Popup ở Template
            messages.success(request, "success")
            return redirect('SinhVien:dien_form', public_id=public_id)

    return redirect('SinhVien:sinhvien_home')