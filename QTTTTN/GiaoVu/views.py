import openpyxl
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from Home.models import KyThucTap, SinhVien, GiangVien
from Home.utils import sync_user_account


def home_view(request):
    """Trang chủ dành cho Giáo Vụ."""
    return render(request, 'GiaoVu/home.html', {'current_page': 'home'})


def ky_thuc_tap_view(request):
    """Trang Quản lý Kỳ thực tập – GET: hiển thị, POST: thêm mới."""
    if request.method == 'POST':
        ten_ky   = request.POST.get('ten', '').strip()
        bat_dau  = request.POST.get('bat_dau', '')
        ket_thuc = request.POST.get('ket_thuc', '')
        if ten_ky and bat_dau and ket_thuc:
            KyThucTap.objects.create(
                ten_ky=ten_ky, ngay_bat_dau=bat_dau,
                ngay_ket_thuc=ket_thuc, gv_phu_trach=None,
            )
            messages.success(request, f'Đã thêm kỳ thực tập "{ten_ky}" thành công!')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
        return redirect('GiaoVu:giaovu_kythuctap')

    all_ky = KyThucTap.objects.all().order_by('-id')
    paginator = Paginator(all_ky, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    context = {'current_page': 'kythuctap', 'page_obj': page_obj}
    return render(request, 'GiaoVu/ky_thuc_tap.html', context)


def ql_sinh_vien_view(request):
    """Trang Quản lý sinh viên – Giáo Vụ."""
    if request.method == 'POST':
        ma_sv  = request.POST.get('ma_sv', '').strip()
        ho_ten = request.POST.get('ho_ten', '').strip()
        lop    = request.POST.get('lop', '').strip()
        ky_id  = request.POST.get('ky_hien_tai', '')
        if ma_sv and ho_ten and lop:
            # Tự động sửa lỗi .0 nếu nhập/paste từ Excel
            if ma_sv.endswith('.0'):
                ma_sv = ma_sv[:-2]
                
            ky = KyThucTap.objects.filter(id=ky_id).first() if ky_id else None
            sv = SinhVien.objects.create(ma_sv=ma_sv, ho_ten=ho_ten, lop=lop, ky_hien_tai=ky)
            sync_user_account(ma_sv, ho_ten, 'SinhVien')
            messages.success(request, f'Đã thêm sinh viên "{ho_ten}" và tạo tài khoản đăng nhập thành công!')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
        return redirect('GiaoVu:giaovu_qlsinhvien')

    selected_ky  = request.GET.get('ky', '')
    search_query = request.GET.get('q', '').strip()

    # Nếu chưa chọn kỳ, tự động chọn kỳ mới nhất
    if not selected_ky and 'ky' not in request.GET:
        newest = KyThucTap.objects.order_by('-id').first()
        if newest:
            selected_ky = str(newest.id)

    sv_list = SinhVien.objects.select_related('ky_hien_tai').all().order_by('ma_sv')
    if selected_ky:
        sv_list = sv_list.filter(ky_hien_tai__id=selected_ky)
    if search_query:
        sv_list = sv_list.filter(Q(ma_sv__icontains=search_query) | Q(ho_ten__icontains=search_query))
    # Đếm trang
    paginator = Paginator(sv_list, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    context = {
        'current_page' : 'qlsinhvien',
        'danh_sach_ky' : KyThucTap.objects.all().order_by('-id'),
        'page_obj'     : page_obj,
        'selected_ky'  : selected_ky,
        'selected_ky_int': int(selected_ky) if selected_ky.isdigit() else None,
        'search_query' : search_query,
    }
    return render(request, 'GiaoVu/sinh_vien.html', context)


def ql_giang_vien_view(request):
    """Trang Quản lý giảng viên – Giáo Vụ."""
    if request.method == 'POST':
        ma_gv       = request.POST.get('ma_gv', '').strip()
        ho_ten      = request.POST.get('ho_ten', '').strip()
        hoc_vi      = request.POST.get('hoc_vi', '').strip()
        chuc_vu     = request.POST.get('chuc_vu', '').strip()
        # Lấy danh sách chuyên môn từ checkboxes
        chuyen_mon_list = request.POST.getlist('chuyen_mon')
        chuyen_mon      = ", ".join(chuyen_mon_list) # Nối thành chuỗi để lưu
        sdt         = request.POST.get('so_dien_thoai', '').strip()

        if ma_gv and ho_ten and chuyen_mon:
            GiangVien.objects.create(
                ma_gv=ma_gv, ho_ten=ho_ten, hoc_vi=hoc_vi,
                chuc_vu=chuc_vu, chuyen_mon=chuyen_mon, so_dien_thoai=sdt,
            )
            # Map chuc_vu sang VaiTro
            role_map = {'Giảng viên': 'GiangVien', 'Giáo vụ': 'GiaoVu', 'Trưởng bộ môn': 'TruongBoMon'}
            role_name = role_map.get(chuc_vu, 'GiangVien')
            sync_user_account(ma_gv, ho_ten, role_name)
            
            messages.success(request, f'Đã thêm giảng viên "{ho_ten}" và tạo tài khoản đăng nhập thành công!')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc.')
        return redirect('GiaoVu:giaovu_qlgiangvien')

    search_query = request.GET.get('q', '').strip()
    gv_list = GiangVien.objects.all().order_by('ho_ten')
    if search_query:
        gv_list = gv_list.filter(
            Q(ho_ten__icontains=search_query) | Q(chuyen_mon__icontains=search_query)
        )

    paginator = Paginator(gv_list, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    # Lấy các danh mục từ Model để hiển thị lên Form
    hoc_vi_choices = [c[0] for c in GiangVien.HOC_VI_CHOICES]
    chuc_vu_choices = [c[0] for c in GiangVien.CHUC_VU_CHOICES]
    chuyen_mon_choices = [c[0] for c in GiangVien.CHUYEN_MON_CHOICES]

    context = {
        'current_page' : 'qlgiangvien',
        'page_obj'     : page_obj,
        'search_query' : search_query,
        'hoc_vi_choices': hoc_vi_choices,
        'chuc_vu_choices': chuc_vu_choices,
        'chuyen_mon_choices': chuyen_mon_choices,
    }
    return render(request, 'GiaoVu/giang_vien.html', context)


def import_giang_vien_view(request):
    """View xử lý import giảng viên từ file Excel."""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        try:
            workbook = openpyxl.load_workbook(excel_file, data_only=True)
            sheet = workbook.active
            success_count = 0

            # Giả định thứ tự cột: A: MaGV, B: HoTen, C: HocVi, D: ChucVu, E: ChuyenMon, F: SDT
            for row in sheet.iter_rows(min_row=2, values_only=True):
                ma_gv_raw = row[0]
                if not ma_gv_raw: continue

                # Làm sạch MaGV
                ma_gv = str(ma_gv_raw).strip()
                if ma_gv.endswith('.0'): ma_gv = ma_gv[:-2]

                ho_ten      = str(row[1]).strip() if row[1] else "Chưa rõ"
                hoc_vi      = str(row[2]).strip() if row[2] else "Thạc sĩ"
                chuc_vu     = str(row[3]).strip() if row[3] else "Giảng viên"
                chuyen_mon  = str(row[4]).strip() if row[4] else ""
                
                # Làm sạch SDT
                sdt = str(row[5]).strip() if row[5] else ""
                if sdt.endswith('.0'): sdt = sdt[:-2]
                if sdt and not sdt.startswith('0') and sdt.isdigit():
                    sdt = '0' + sdt

                GiangVien.objects.update_or_create(
                    ma_gv=ma_gv,
                    defaults={
                        'ho_ten': ho_ten,
                        'hoc_vi': hoc_vi,
                        'chuc_vu': chuc_vu,
                        'chuyen_mon': chuyen_mon,
                        'so_dien_thoai': sdt
                    }
                )
                # Map chuc_vu sang VaiTro
                role_map = {'Giảng viên': 'GiangVien', 'Giáo vụ': 'GiaoVu', 'Trưởng bộ môn': 'TruongBoMon'}
                role_name = role_map.get(chuc_vu, 'GiangVien')
                sync_user_account(ma_gv, ho_ten, role_name)
                
                success_count += 1

            messages.success(request, f'Đã import thành công {success_count} giảng viên.')
        except Exception as e:
            messages.error(request, f'Lỗi khi xử lý file: {str(e)}')

    return redirect('GiaoVu:giaovu_qlgiangvien')


def edit_giang_vien_view(request):
    """View xử lý cập nhật giảng viên (Hỗ trợ đổi MaGV)."""
    if request.method == 'POST':
        original_ma = request.POST.get('original_ma_gv', '').strip()
        new_ma      = request.POST.get('ma_gv', '').strip()
        ho_ten      = request.POST.get('ho_ten', '').strip()
        hoc_vi      = request.POST.get('hoc_vi', '').strip()
        chuc_vu     = request.POST.get('chuc_vu', '').strip()
        sdt         = request.POST.get('so_dien_thoai', '').strip()
        
        # Chuyên môn từ Multi-select checkbox
        chuyen_mon_list = request.POST.getlist('chuyen_mon')
        chuyen_mon      = ", ".join(chuyen_mon_list)

        if original_ma and new_ma and ho_ten:
            gv = GiangVien.objects.filter(ma_gv=original_ma).first()
            if gv:
                if original_ma != new_ma:
                    # Đổi mã giảng viên (PK)
                    GiangVien.objects.create(
                        ma_gv=new_ma, ho_ten=ho_ten, hoc_vi=hoc_vi,
                        chuc_vu=chuc_vu, chuyen_mon=chuyen_mon, so_dien_thoai=sdt
                    )
                    gv.delete()
                else:
                    gv.ho_ten = ho_ten
                    gv.hoc_vi = hoc_vi
                    gv.chuc_vu = chuc_vu
                    gv.chuyen_mon = chuyen_mon
                    gv.so_dien_thoai = sdt
                    gv.save()
                messages.success(request, f'Cập nhật giảng viên "{ho_ten}" thành công!')
            else:
                messages.error(request, 'Không tìm thấy giảng viên.')
        else:
            messages.error(request, 'Thiếu thông tin bắt buộc.')
    return redirect('GiaoVu:giaovu_qlgiangvien')


def delete_giang_vien_view(request, ma_gv):
    """Xóa giảng viên."""
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    if gv:
        ho_ten = gv.ho_ten
        gv.delete()
        messages.success(request, f'Đã xóa giảng viên "{ho_ten}".')
    else:
        messages.error(request, 'Không tìm thấy giảng viên.')
    return redirect('GiaoVu:giaovu_qlgiangvien')


def import_sinh_vien_view(request):
    """View xử lý import sinh viên từ file Excel."""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        # 1. Lấy kỳ thực tập mới nhất
        ky_moi_nhat = KyThucTap.objects.order_by('-id').first()
        if not ky_moi_nhat:
            messages.error(request, 'Hệ thống chưa có Kỳ thực tập nào. Vui lòng tạo kỳ thực tập trước khi import.')
            return redirect('GiaoVu:giaovu_qlsinhvien')

        try:
            # 2. Đọc file Excel
            workbook = openpyxl.load_workbook(excel_file, data_only=True)
            sheet = workbook.active

            success_count = 0
            # Giả định: Cột A: MSSV, Cột B: Họ tên, Cột C: Lớp
            # Đọc từ hàng thứ 2 (bỏ qua tiêu đề)
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row[0]: continue  # Bỏ qua dòng trống MSSV

                ma_sv = str(row[0]).strip()
                if ma_sv.endswith('.0'): ma_sv = ma_sv[:-2]

                ho_ten  = str(row[1]).strip() if row[1] else "Chưa có tên"
                lop     = str(row[2]).strip() if row[2] else "N/A"

                # 3. Lưu vào database (Update nếu trùng MSSV)
                SinhVien.objects.update_or_create(
                    ma_sv=ma_sv,
                    defaults={
                        'ho_ten': ho_ten,
                        'lop': lop,
                        'ky_hien_tai': ky_moi_nhat
                    }
                )
                sync_user_account(ma_sv, ho_ten, 'SinhVien')
                success_count += 1

            messages.success(request, f'Đã import thành công {success_count} sinh viên vào "{ky_moi_nhat.ten_ky}".')
        except Exception as e:
            messages.error(request, f'Lỗi khi xử lý file: {str(e)}')

    return redirect('GiaoVu:giaovu_qlsinhvien')


def edit_sinh_vien_view(request):
    """View xử lý cập nhật thông tin sinh viên (bao gồm cả việc đổi MSSV)."""
    if request.method == 'POST':
        original_ma = request.POST.get('original_ma_sv', '').strip()
        new_ma      = request.POST.get('ma_sv', '').strip()
        ho_ten      = request.POST.get('ho_ten', '').strip()
        lop         = request.POST.get('lop', '').strip()
        ky_id       = request.POST.get('ky_hien_tai', '')

        if original_ma and new_ma and ho_ten and lop:
            # Sửa lỗi .0 nếu có
            if new_ma.endswith('.0'): new_ma = new_ma[:-2]
            if original_ma.endswith('.0'): original_ma = original_ma[:-2]

            sinh_vien = SinhVien.objects.filter(ma_sv=original_ma).first()
            
            if sinh_vien:
                ky = KyThucTap.objects.filter(id=ky_id).first() if ky_id else None
                
                if original_ma != new_ma:
                    # Nếu đổi MSSV (Primary Key)
                    # 1. Tạo bản ghi mới dựa trên bản ghi cũ
                    SinhVien.objects.create(
                        ma_sv=new_ma,
                        ho_ten=ho_ten,
                        lop=lop,
                        ky_hien_tai=ky
                    )
                    # 2. Xóa bản ghi cũ
                    sinh_vien.delete()
                else:
                    # Nếu giữ nguyên MSSV
                    sinh_vien.ho_ten = ho_ten
                    sinh_vien.lop = lop
                    sinh_vien.ky_hien_tai = ky
                    sinh_vien.save()
                
                messages.success(request, f'Cập nhật sinh viên "{ho_ten}" thành công!')
            else:
                messages.error(request, 'Không tìm thấy sinh viên để cập nhật.')
        else:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')

    return redirect('GiaoVu:giaovu_qlsinhvien')


def delete_sinh_vien_view(request, ma_sv):
    """View xử lý xóa sinh viên."""
    sinh_vien = SinhVien.objects.filter(ma_sv=ma_sv).first()
    if sinh_vien:
        ho_ten = sinh_vien.ho_ten
        sinh_vien.delete()
        messages.success(request, f'Đã xóa sinh viên "{ho_ten}" thành công!')
    else:
        messages.error(request, 'Không tìm thấy sinh viên để xóa.')
    return redirect('GiaoVu:giaovu_qlsinhvien')
