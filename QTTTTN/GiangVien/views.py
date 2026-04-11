from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from Home.models import (GiangVien, PhanCongGVPT,SinhVien,
                         PhanCongGVHD, MauKhaoSat, CauHoi, LuaChon, BaiNop, NhiemVu, BangDiem, KyThucTap,
                         KyThucTap, ChiTietTraLoi, PhieuTraLoi, TieuChiDanhGia, HoiDong, HoiDong_SinhVien,HoiDong_GiangVien, ChamDiemHoiDong)
from django.contrib import messages
from django.views.decorators.http import require_POST


def home_view(request):
    """Khi giảng viên đăng nhập → tự động chuyển thẳng sang trang Sinh viên của tôi"""

    # Vẫn giữ phần kiểm tra is_gvpt (để sidebar hoạt động)
    ma_gv = request.user.username
    giang_vien = GiangVien.objects.filter(ma_gv=ma_gv).first()

    is_gvpt = False
    if giang_vien:
        is_gvpt = PhanCongGVPT.objects.filter(giang_vien=giang_vien).exists()

    # 🔥 Redirect thẳng sang view sinhvien_huongdan (view này có đầy đủ dữ liệu)
    return redirect('GiangVien:sinhvien_huongdan')

def sinhvien_huongdan(request):

    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()

    ky_id = request.GET.get("ky")
    query = request.GET.get("q")   # 🔥 THÊM DÒNG NÀY

    danh_sach = PhanCongGVHD.objects.filter(
        giang_vien=gv,
        trang_thai=2
    ).select_related('sinh_vien', 'ky')

    # 🔥 FILTER KỲ
    if ky_id:
        danh_sach = danh_sach.filter(ky_id=ky_id)

    # 🔥 SEARCH
    if query:
        danh_sach = danh_sach.filter(
            Q(sinh_vien__ma_sv__icontains=query) |
            Q(sinh_vien__ho_ten__icontains=query) |
            Q(sinh_vien__lop__icontains=query)
        )

    ky_list = KyThucTap.objects.all().order_by('-id')

    current_ky = None
    if ky_id:
        current_ky = KyThucTap.objects.filter(id=ky_id).first()

    for item in danh_sach:
        sv = item.sinh_vien

        if sv.noi_thuc_tap:
            item.noi_thuc_tap = sv.noi_thuc_tap
            continue

        phieu = PhieuTraLoi.objects.filter(
            sinh_vien=sv
        ).order_by("-id").first()

        noi_tt = ""

        if phieu:
            for ans in phieu.answers.all():
                tag = (ans.cau_hoi.system_tag or "").strip()
                if tag == "don_vi_tt":
                    noi_tt = ans.gia_tri
                    sv.noi_thuc_tap = noi_tt
                    sv.save()
                    break

        item.noi_thuc_tap = noi_tt or ""

    context = {
        'danh_sach': danh_sach,
        'ky_list': ky_list,
        'current_ky': current_ky,   # 🔥 thêm
        'query': query,  # 🔥 QUAN TRỌNG
        'current_page': 'sinhvien',
        'is_gvpt': get_is_gvpt(request)
    }

    return render(request, 'GiangVien/sinhvien_huongdan.html', context)

def chi_tiet_sinh_vien(request, ma_sv):

    sv = get_object_or_404(SinhVien, ma_sv=ma_sv)

    # 🔥 lấy kỳ hiện tại
    ky = sv.ky_hien_tai

    # 🔥 lấy tất cả nhiệm vụ (milestone)
    nhiem_vus = NhiemVu.objects.filter(ky=ky).order_by("han_nop")

    milestones = []

    for nv in nhiem_vus:

        bai_nop = BaiNop.objects.filter(
            sinh_vien=sv,
            nhiem_vu=nv
        ).first()

        if bai_nop:
            status = "ĐÃ NỘP"
            file = bai_nop.ten_file
            file_url = bai_nop.file_path.url
            ngay = bai_nop.thoi_gian_nop
            bai_id = bai_nop.id  # ✅ có thì mới lấy
        else:
            status = "CHƯA NỘP"
            file = "--"
            file_url = "#"
            ngay = "--"
            bai_id = None  # ✅ tránh lỗi

        milestones.append({
            "id": bai_id,
            "ten": nv.ten_nhiem_vu,
            "ngay": ngay,
            "file": file,
            "file_url": file_url,
            "status": status,
            "is_submitted": True if bai_nop else False  # 🔥 thêm dòng này
        })

    # 🔥 lấy điểm nếu đã có
    bang_diem = BangDiem.objects.filter(
        sinh_vien=sv,
        ky=ky
    ).order_by('-id').first()

    context = {
        "sv": sv,
        "milestones": milestones,
        "bang_diem": bang_diem,
        "is_gvpt": get_is_gvpt(request)
    }

    return render(
        request,
        "GiangVien/chi_tiet_sinh_vien.html",
        context
    )


@require_POST
def save_diem(request, ma_sv):

    sv = SinhVien.objects.get(ma_sv=ma_sv)
    ky = sv.ky_hien_tai or KyThucTap.objects.order_by('-id').first()

    diem = request.POST.get("diem")

    if diem:
        diem = float(diem)

    bd, _ = BangDiem.objects.get_or_create(
        sinh_vien=sv,
        ky=ky
    )

    bd.diem_qua_trinh = diem
    bd.save()

    return redirect("GiangVien:chi_tiet_sv", ma_sv=ma_sv)
def chi_tiet_bai_nop(request, id):

    bai = get_object_or_404(BaiNop, id=id)
    # Nếu giảng viên gửi nhận xét (POST)
    if request.method == "POST":
        nhan_xet = request.POST.get('nhan_xet', '').strip()
        bai.nhan_xet = nhan_xet
        bai.save()
        # Có thể thêm thông báo nếu bạn dùng messages
    context = {
        "bai": bai,
        "sv": bai.sinh_vien,
        "nv": bai.nhiem_vu,
        "is_gvpt": get_is_gvpt(request)
    }

    return render(
        request,
        "GiangVien/chi_tiet_bai_nop.html",
        context
    )



@require_POST
def update_sinh_vien_info(request, ma_sv):
    sv = SinhVien.objects.get(ma_sv=ma_sv)

    ten_de_tai = request.POST.get('ten_de_tai', '').strip()
    noi_tt = request.POST.get('noi_tt', '').strip()

    if ten_de_tai:
        sv.ten_de_tai = ten_de_tai
    if noi_tt:
        sv.noi_thuc_tap = noi_tt

    sv.save()
    return redirect("GiangVien:sinhvien_huongdan")

def get_is_gvpt(request):
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    if gv:
        return PhanCongGVPT.objects.filter(giang_vien=gv).exists()
    return False
def form_list(request):

    forms = MauKhaoSat.objects.all().order_by("-ngay_tao")

    return render(request, "GiangVien/form_list.html", {
        "forms": forms,
        "current_page": "form_list",
        "is_gvpt": get_is_gvpt(request)    })
def tao_form(request):
    # Lấy tất cả các kỳ thực tập từ database
    # Phải dùng đúng tên biến 'danh_sach_ky' như trong file HTML của ông
    danh_sach_ky = KyThucTap.objects.all().order_by("-id")
    ky_moi_nhat = danh_sach_ky.first()
    
    # Danh sách giảng viên để tự động điền vào tạo form đánh giá (loại Giáo vụ và thêm học vị)
    gvs = GiangVien.objects.exclude(chuc_vu='Giáo vụ').order_by('ho_ten')
    danh_sach_gv = []
    prefix_map = {'Thạc sĩ': 'ThS.', 'Tiến sĩ': 'TS.', 'Phó Giáo sư': 'PGS.TS.', 'Giáo sư': 'GS.TS.'}
    for gv in gvs:
        prefix = prefix_map.get(gv.hoc_vi, '')
        hovaten = f"{prefix} {gv.ho_ten}".strip() if prefix else gv.ho_ten
        if gv.chuyen_mon:
            hovaten += f" ({gv.chuyen_mon})"
        danh_sach_gv.append({'ma_gv': gv.ma_gv, 'ho_ten': hovaten})

    if request.method == "POST":
        raw = request.POST.get("form_data")
        data = json.loads(raw)

        id_ky_chon = data.get("ky_thuc_tap")
        ky_duoc_chon = KyThucTap.objects.get(id=id_ky_chon)

        form = MauKhaoSat.objects.create(
            ky=ky_duoc_chon,
            ten_form=data["ten_form"],
            ngay_bat_dau=data.get("start_date") or ky_duoc_chon.ngay_bat_dau,
            ngay_ket_thuc=data.get("end_date") or ky_duoc_chon.ngay_ket_thuc
        )

        for i, q in enumerate(data["questions"]):
            cauhoi = CauHoi.objects.create(
                mau_khao_sat=form,
                noi_dung=q["title"],
                loai_cau_hoi=q["type"],
                thu_tu=i,
                system_tag=q.get("system_tag", "")
            )

            for op in q.get("options", []):
                LuaChon.objects.create(
                    cau_hoi=cauhoi,
                    noi_dung_option=op["text"]
                )

            # Dùng 'rows' để khớp với JS render của ông
            for tc in q.get("rows", []):
                TieuChiDanhGia.objects.create(
                    cau_hoi=cauhoi,
                    noi_dung=tc["text"]
                )

        return redirect("GiangVien:form_list")

    # ĐÂY LÀ CHỖ QUAN TRỌNG:
    # Phải truyền 'danh_sach_ky' vào dictionary này
    return render(request, "GiangVien/tao_form.html", {
        "danh_sach_ky": danh_sach_ky,
        "ky_moi_nhat": ky_moi_nhat,
        "is_gvpt": get_is_gvpt(request),
        "danh_sach_gv_json": json.dumps(danh_sach_gv)
    })

def form_detail(request, public_id):

    form = MauKhaoSat.objects.get(public_id=public_id)

    questions = form.cau_hoi.all().prefetch_related("options")

    return render(request, "GiangVien/form_detail.html", {
        "form": form,
        "questions": questions, "is_gvpt": get_is_gvpt(request)
    })
from collections import Counter


def edit_form(request, public_id):
    form = get_object_or_404(MauKhaoSat, public_id=public_id)
    danh_sach_ky = KyThucTap.objects.all().order_by("-id")
    
    # Danh sách giảng viên
    gvs = GiangVien.objects.exclude(chuc_vu='Giáo vụ').order_by('ho_ten')
    danh_sach_gv = []
    prefix_map = {'Thạc sĩ': 'ThS.', 'Tiến sĩ': 'TS.', 'Phó Giáo sư': 'PGS.TS.', 'Giáo sư': 'GS.TS.'}
    for gv in gvs:
        prefix = prefix_map.get(gv.hoc_vi, '')
        hovaten = f"{prefix} {gv.ho_ten}".strip() if prefix else gv.ho_ten
        if gv.chuyen_mon:
            hovaten += f" ({gv.chuyen_mon})"
        danh_sach_gv.append({'ma_gv': gv.ma_gv, 'ho_ten': hovaten})

    if request.method == "POST":
        data = json.loads(request.POST.get("form_data"))

        # 1. Cập nhật thông tin cơ bản của Form
        form.ten_form = data.get("ten_form", "")
        if data.get("start_date"):
            form.ngay_bat_dau = data["start_date"]
        if data.get("end_date"):
            form.ngay_ket_thuc = data["end_date"]

        # Cập nhật kỳ thực tập nếu có thay đổi
        if data.get("ky_thuc_tap"):
            form.ky_id = data["ky_thuc_tap"]

        form.save()

        form.save()

        # So sánh câu hỏi cũ và mới để quyết định có reset bài nộp hay không
        old_questions = list(form.cau_hoi.all().order_by('thu_tu'))
        new_questions_data = data.get("questions", [])

        is_changed = False
        if len(old_questions) != len(new_questions_data):
            is_changed = True
        else:
            for i, q in enumerate(new_questions_data):
                old_q = old_questions[i]
                if (old_q.noi_dung != q["title"] or 
                    old_q.loai_cau_hoi != q["type"] or 
                    (old_q.system_tag or "") != (q.get("system_tag", ""))):
                    is_changed = True
                    break
                
                # Kiểm tra options
                old_opts = list(old_q.options.all().order_by('id'))
                new_opts = q.get("options", [])
                if len(old_opts) != len([o for o in new_opts if o.get("text")]):
                    is_changed = True
                    break
                
                # Kiểm tra rows (Tiêu chí)
                old_rows = list(old_q.tieuchi.all().order_by('id'))
                new_rows = q.get("rows", [])
                if len(old_rows) != len([r for r in new_rows if r.get("text")]):
                    is_changed = True
                    break

        if is_changed:
            # Nếu có thay đổi câu hỏi, xoá bài nộp cũ để SV điền lại
            PhieuTraLoi.objects.filter(mau_khao_sat=form).delete()
            
            # Xoá câu hỏi cũ và tạo mới
            form.cau_hoi.all().delete()
            for i, q in enumerate(new_questions_data):
                cauhoi = CauHoi.objects.create(
                    mau_khao_sat=form,
                    noi_dung=q["title"],
                    loai_cau_hoi=q["type"],
                    thu_tu=i,
                    system_tag=q.get("system_tag", "")
                )
                for op in q.get("options", []):
                    if op.get("text"):
                        LuaChon.objects.create(cau_hoi=cauhoi, noi_dung_option=op["text"])
                for tc in q.get("rows", []):
                    if tc.get("text"):
                        TieuChiDanhGia.objects.create(cau_hoi=cauhoi, noi_dung=tc["text"])
            
            messages.warning(request, "Đã cập nhật câu hỏi và reset danh sách bài nộp để sinh viên điền lại.")
        else:
            messages.success(request, "Đã cập nhật thông tin form thành công.")

        return redirect("GiangVien:edit_form", public_id=public_id)

    # ===== LOAD QUESTIONS (GET METHOD) =====
    questions_data = []
    gvhd_counter = Counter()

    # Load câu hỏi sắp xếp theo thứ tự
    for q in form.cau_hoi.all().order_by('thu_tu'):

        # Thống kê (Giữ nguyên logic của ông)
        answers = q.chitiettraloi_set.all()
        values = [a.gia_tri for a in answers]
        stats = Counter(values)

        if q.system_tag in ["GVHD_1", "GVHD_2"]:
            for v in values:
                gvhd_counter[v] += 1

        # Đóng gói object để đẩy xuống JS
        questions_data.append({
            "id": q.id,  # Để JS biết đây là câu cũ
            "title": q.noi_dung,
            "type": q.loai_cau_hoi,
            "system_tag": q.system_tag,
            "options": [{"text": o.noi_dung_option} for o in q.options.all()],
            # SỬA TẠI ĐÂY: Đổi key 'criteria' thành 'rows'
            "rows": [{"text": c.noi_dung} for c in q.tieuchi.all()],
            "stats": dict(stats)
        })

    # ===== LOAD RESPONSES =====
    responses_list = []
    phieu_list = PhieuTraLoi.objects.filter(mau_khao_sat=form).select_related('sinh_vien').order_by('-thoi_gian_nop')
    for phieu in phieu_list:
        ans_dict = {}
        for c in phieu.answers.all():
            if c.cau_hoi_id not in ans_dict:
                ans_dict[c.cau_hoi_id] = []
            ans_dict[c.cau_hoi_id].append(c.gia_tri)
            
        ans_list = []
        for q in questions_data:
            ans = ans_dict.get(q["id"], ["-"])
            ans_list.append(", ".join(ans) if isinstance(ans, list) else ans)

        responses_list.append({
            "ma_sv": phieu.sinh_vien.ma_sv,
            "ho_ten": phieu.sinh_vien.ho_ten,
            "thoi_gian": timezone.localtime(phieu.thoi_gian_nop).strftime('%d/%m/%Y %H:%M') if phieu.thoi_gian_nop else "-",
            "answers": ans_list
        })

    return render(request, "GiangVien/tao_form.html", {
        "form": form,
        "questions_json": json.dumps(questions_data),  # Truyền xuống để JS render()
        "ky_moi_nhat": form.ky,
        "danh_sach_ky": danh_sach_ky,
        "gvhd_stats": dict(gvhd_counter),
        "is_edit": True,
        "is_gvpt": get_is_gvpt(request),
        "danh_sach_gv_json": json.dumps(danh_sach_gv),
        "questions_list": questions_data,
        "responses_list": responses_list
    })
def xoa_form(request, public_id):
    # Chỉ cho phép xóa nếu là phương thức POST (để bảo mật)
    if request.method == "POST":
        form = get_object_or_404(MauKhaoSat, public_id=public_id)
        form.delete()
    return redirect("GiangVien:form_list")
def public_form(request, public_id):

    form = MauKhaoSat.objects.get(public_id=public_id)

    questions = form.cau_hoi.all().prefetch_related("options")

    return render(request, "Forms/public_form.html", {
        "form": form,
        "questions": questions
    })

def submit_form(request,public_id):

    if request.method=="POST":

        form = MauKhaoSat.objects.get(public_id=public_id)

        sv = SinhVien.objects.get(ma_sv=request.user.username)

        phieu = PhieuTraLoi.objects.create(
            sinh_vien=sv,
            mau_khao_sat=form
        )

        for key in request.POST:
            if key.startswith("question_"):
                values = request.POST.getlist(key)

                cau_hoi_id = key.replace("question_", "")
                cau_hoi = CauHoi.objects.get(id=cau_hoi_id)

                for v in values:
                    ChiTietTraLoi.objects.create(
                        phieu_tra_loi=phieu,
                        cau_hoi=cau_hoi,
                        gia_tri=v
                    )

                    # 🔥 AUTO LƯU NƠI THỰC TẬP
                    if (cau_hoi.system_tag or "").strip() == "don_vi_tt":
                        sv.noi_thuc_tap = v
                        sv.save()

        return render(request, "Forms/success.html")
#
# ========================
# LẤY FORM NGUYỆN VỌNG
# ========================
def get_form_nguyen_vong(ky_id=None):
    if ky_id:
        ky = KyThucTap.objects.filter(id=ky_id).first()
    else:
        ky = KyThucTap.objects.order_by("-id").first()

    form = None
    if ky:
        form = MauKhaoSat.objects.filter(
            ky=ky,
            cau_hoi__system_tag__in=["GVHD_1", "GVHD_2", "ten_gvhd", "gvhd_1", "gvhd_2"]
        ).distinct().order_by("-ngay_tao").first()
        
        if not form:
            form = MauKhaoSat.objects.filter(ky=ky).order_by("-ngay_tao").first()

    return ky, form

# ========================
# DASHBOARD
# ========================
def phan_cong_dashboard(request):
    ky_id = request.GET.get('ky_id')
    ky, form = get_form_nguyen_vong(ky_id)
    ky_list = KyThucTap.objects.all().order_by('-id')

    # Luôn lấy danh sách sinh viên của kỳ hiện tại
    if ky:
        sinhviens = SinhVien.objects.filter(ky_hien_tai=ky)
    else:
        sinhviens = SinhVien.objects.all()

    data = []
    gv_wish_count = defaultdict(int)

    # 🔥 Build map: plain ho_ten → display name có prefix (ThS./TS./...)
    PREFIX_MAP = {'Thạc sĩ': 'ThS.', 'Tiến sĩ': 'TS.', 'Phó Giáo sư': 'PGS.TS.', 'Giáo sư': 'GS.TS.'}
    gv_display_map = {}  # {"Lê Hoàng Nam": "ThS. Lê Hoàng Nam"}
    for _gv in GiangVien.objects.exclude(chuc_vu='Giáo vụ'):
        pf = PREFIX_MAP.get(_gv.hoc_vi, '')
        gv_display_map[_gv.ho_ten] = f"{pf} {_gv.ho_ten}".strip() if pf else _gv.ho_ten

    for sv in sinhviens:
        nv1 = ""
        nv2 = ""
        de_tai = ""
        group = ""
        huong_tc = ""
        linh_vuc = ""

        if form:
            phieu = PhieuTraLoi.objects.filter(
                sinh_vien=sv,
                mau_khao_sat=form
            ).first()

            if phieu:
                for a in phieu.answers.all():
                    tag = (a.cau_hoi.system_tag or "").strip().lower()
                    val = (a.gia_tri or "").strip()

                    if tag in ["gvhd_1", "ten_gvhd"]:
                        clean_val = val.split('(')[0].strip() if '(' in val else val

                        if nv1:
                            nv1 += f"\n{clean_val}"
                        else:
                            nv1 = clean_val
                        gv_wish_count[clean_val.lower()] += 1

                    elif tag == "gvhd_2":
                        clean_val = val.split('(')[0].strip() if '(' in val else val

                        if nv2:
                            nv2 += f"\n{clean_val}"
                        else:
                            nv2 = clean_val
                        gv_wish_count[clean_val.lower()] += 1
                    
                    elif tag == "de_tai":
                        if de_tai:
                            de_tai += f", {val}"
                        else:
                            de_tai = val
                    elif tag == "huong_tiep_can":
                        if huong_tc:
                            if val not in huong_tc:
                                huong_tc += f", {val}"
                        else:
                            huong_tc = val
                        # 🔥 Lĩnh vực = những gì SV điền vào câu hướng tiếp cận
                        if linh_vuc:
                            if val not in linh_vuc:
                                linh_vuc += f"\n{val}"
                        else:
                            linh_vuc = val
                    elif tag in ["group", "hinh_thuc_nhom"]:
                        # Chỉ lưu nếu SV điền tên thực sự, bỏ qua "Không có", "Không có làm nhóm với ai"...
                        if val and not val.strip().lower().startswith("không"):
                            if group:
                                if val not in group:
                                    group += f", {val}"
                            else:
                                group = val

        pc = PhanCongGVHD.objects.filter(sinh_vien=sv, ky=ky).first() if ky else PhanCongGVHD.objects.filter(sinh_vien=sv).first()

        status = ""
        if pc:
            if pc.giang_vien.ho_ten == nv1:
                status = "NV1"
            elif pc.giang_vien.ho_ten == nv2:
                status = "NV2"

        # 🔥 Tạo danh sách GVHD đề xuất từ nv1+nv2+linh_vuc
        # value = plain ho_ten (lưu DB), display = tên có prefix (hiện UI)
        de_xuat_gvhd = []
        seen_values = set()

        def strip_prefix(name):
            for p in ['GS.TS. ', 'PGS.TS. ', 'TS. ', 'ThS. ']:
                if name.startswith(p):
                    return name[len(p):]
            return name

        # 1. Từ nguyện vọng
        for raw in [nv1, nv2]:
            for gv_name in raw.split("\n"):
                plain = strip_prefix(gv_name.strip())
                if plain and plain not in seen_values:
                    seen_values.add(plain)
                    de_xuat_gvhd.append({
                        "value": plain,
                        "display": gv_display_map.get(plain, plain)
                    })

        # 2. Từ lĩnh vực: match chuyen_mon
        if linh_vuc and linh_vuc != "--":
            import re
            def clean_text(text):
                if not text: return ""
                # Chuyển về chữ thường, xoá khoảng trắng thừa
                text = text.lower().strip()
                # Hàm đơn giản bỏ dấu tiếng Việt để so sánh khớp hơn
                import unicodedata
                return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

            # Tách từ khóa bằng các ký tự phân cách phổ biến (xuống dòng, phẩy, chấm phẩy)
            raw_keywords = re.split(r'[\n,;]', linh_vuc)
            keywords = [clean_text(kw) for kw in raw_keywords if len(kw.strip()) > 2]
            
            for gv in GiangVien.objects.exclude(chuc_vu='Giáo vụ'):
                gv_cm_clean = clean_text(gv.chuyen_mon or "")
                for kw_clean in keywords:
                    if kw_clean and (kw_clean in gv_cm_clean or gv_cm_clean in kw_clean):
                        if gv.ho_ten not in seen_values:
                            seen_values.add(gv.ho_ten)
                            de_xuat_gvhd.append({
                                "value": gv.ho_ten,
                                "display": gv_display_map.get(gv.ho_ten, gv.ho_ten)
                            })
                        break

        # 3. Đảm bảo GVHD HIỆN TẠI luôn luôn nằm trong danh sách đề xuất (nếu chưa có) để hiển thị đúng Dropdown
        if pc and pc.giang_vien:
            current_gv = pc.giang_vien.ho_ten
            if current_gv not in seen_values:
                seen_values.add(current_gv)
                de_xuat_gvhd.append({
                    "value": current_gv,
                    "display": gv_display_map.get(current_gv, current_gv)
                })

        data.append({
            "id": sv.ma_sv,
            "ten": sv.ho_ten,
            "lop": sv.lop,
            "de_tai": de_tai or "--",
            "huong_tc": huong_tc or "--",
            "linh_vuc": linh_vuc or "--",
            "nv1": nv1,
            "nv2": nv2,
            "de_xuat_gvhd": de_xuat_gvhd,
            "group": group or "Không",
            "gvhd": pc.giang_vien.ho_ten if pc else "",
            "trang_thai": pc.trang_thai if pc else 1,
            "ly_do_tu_choi": pc.ly_do_tu_choi if pc else "",
            "status": status
        })

    # Ưu tiên những người có nv1 lên trước tiên, sau đó tới người chưa có nv
    data.sort(key=lambda x: (0 if x["nv1"] else 1))

    # ===== GV STATS =====
    gv_stats = []
    gv_assigned_count = defaultdict(int)

    # Tính số lượng SV ĐÃ phân công cho mỗi GVHD trong kỳ hiện tại
    query = PhanCongGVHD.objects.filter(ky=ky) if ky else PhanCongGVHD.objects.all()
    for pc in query:
        if pc.giang_vien:
            gv_assigned_count[pc.giang_vien.ho_ten] += 1

    for gv in GiangVien.objects.all():
        count = gv_assigned_count.get(gv.ho_ten, 0)
        # Chỉ hiện GV nếu có sinh viên được phân công 
        if count > 0:
            gv_stats.append({
                "ten": gv_display_map.get(gv.ho_ten, gv.ho_ten),
                "count": count,
                "overload": count > 10
            })

    # Sắp xếp theo số lượng giảm dần
    gv_stats.sort(key=lambda x: -x["count"])

    return render(request, "GiangVien/phan_cong.html", {
        "data": data,
        "gv_stats": gv_stats,
        "is_gvpt": get_is_gvpt(request),
        "ky_list": ky_list,
        "current_ky": ky
    })

# ========================
# AUTO ASSIGN (UI)
# ========================
# RUN AUTO



# ========================
# UPDATE MANUAL
# ========================
def update_phan_cong(request):

    if request.method == "POST":

        sv_id = request.POST.get("sv")
        gv_name = request.POST.get("gv")
        ky_id = request.POST.get("ky_id")

        try:
            sv = SinhVien.objects.get(ma_sv=sv_id)
            
            if not gv_name:
                # Xoá phân công nếu chọn "-- Chưa phân --"
                # Nhưng KHÔNG cho xoá nếu đã được Duyệt (trang_thai=2)
                if PhanCongGVHD.objects.filter(sinh_vien=sv, trang_thai=2).exists():
                    return JsonResponse({"status": "error", "message": "Phân công này đã được Trưởng bộ môn DUYỆT nên không được xoá!"})
                
                PhanCongGVHD.objects.filter(sinh_vien=sv).delete()
                return JsonResponse({"status": "deleted"})

            gv = GiangVien.objects.filter(ho_ten=gv_name).first()
            if not gv:
                return JsonResponse({"status": "error", "message": f"Giảng viên {gv_name} không tồn tại trong hệ thống."})
            
            # Kiểm tra xem phân công hiện tại đã được duyệt chưa (trang_thai=2)
            # Nếu đã duyệt rồi (trang_thai=2) thì không cho phép ghi đè (sửa)
            if PhanCongGVHD.objects.filter(sinh_vien=sv, trang_thai=2).exists():
                return JsonResponse({"status": "error", "message": "Phân công này đã được Trưởng bộ môn DUYỆT nên không được sửa đổi!"})
            
            if ky_id and str(ky_id).isdigit():
                ky = KyThucTap.objects.get(id=ky_id)
            else:
                ky = KyThucTap.objects.order_by("-id").first()

            # Sử dụng cả sinh_vien và ky để lọc chính xác bản ghi cần cập nhật
            PhanCongGVHD.objects.update_or_create(
                sinh_vien=sv,
                ky=ky,
                defaults={
                    "giang_vien": gv,
                    "trang_thai": 1  # Chờ duyệt
                }
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

import json
from collections import defaultdict

def hoi_dong_list(request):
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()
    is_gvpt = get_is_gvpt(request)

    tab = request.GET.get('tab', 'my')
    ky_id = request.GET.get('ky')   # Lấy kỳ từ filter

    # Lấy danh sách tất cả kỳ để hiển thị trong dropdown
    ky_list = KyThucTap.objects.all().order_by('-id')

    # Xác định queryset hội đồng
    if is_gvpt:
        if tab == 'all':
            # GVPT xem tất cả hội đồng (Bao gồm cả chờ duyệt để họ theo dõi)
            hoidongs = HoiDong.objects.select_related('ky').all()
        else:
            # GVPT xem hội đồng của mình ĐÃ ĐƯỢC DUYỆT
            hoidongs = HoiDong.objects.filter(
                hoidong_giangvien__giang_vien=gv,
                trang_thai=2
            ).select_related('ky').distinct()
    else:
        # GV thường chỉ xem hội đồng mình tham gia ĐÃ ĐƯỢC DUYỆT
        hoidongs = HoiDong.objects.filter(
            hoidong_giangvien__giang_vien=gv,
            trang_thai=2
        ).select_related('ky').distinct()

    # Áp dụng lọc theo Kỳ thực tập (nếu có)
    if ky_id:
        hoidongs = hoidongs.filter(ky_id=ky_id)

    # Sắp xếp theo ngày mới nhất
    hoidongs = hoidongs.order_by('-ngay_bao_ve')

    # Xác định kỳ hiện tại để highlight trong dropdown
    current_ky = None
    if ky_id:
        current_ky = KyThucTap.objects.filter(id=ky_id).first()
    elif ky_list.exists():
        current_ky = ky_list.first()

    context = {
        "hoidongs": hoidongs,
        "current_page": "hoi_dong",
        "is_gvpt": is_gvpt,
        "ky_list": ky_list,          # Truyền danh sách kỳ vào template
        "current_ky": current_ky,    # Kỳ đang được chọn
        "tab": tab,                  # Để template biết tab nào đang active
    }

    return render(request, "GiangVien/hoi_dong_list.html", context)

from datetime import datetime

def tao_hoi_dong(request):
    if not get_is_gvpt(request):
        return redirect("GiangVien:hoi_dong_list")

    if request.method == "POST":
        gv_ids = request.POST.getlist("giang_vien")
        sv_ids_str = request.POST.get("sinh_vien_ids", "")
        sv_ids = [x.strip() for x in sv_ids_str.split(",") if x.strip()]

        ngay = request.POST.get("ngay")          # yyyy-mm-dd
        gio_bd = request.POST.get("thoi_gian_bat_dau") # HH:MM
        gio_kt = request.POST.get("thoi_gian_ket_thuc")

        try:
            # 🔥 GHÉP NGÀY + GIỜ
            thoi_gian_bat_dau = datetime.strptime(f"{ngay} {gio_bd}", "%Y-%m-%d %H:%M")
            thoi_gian_ket_thuc = datetime.strptime(f"{ngay} {gio_kt}", "%Y-%m-%d %H:%M")

            hd = HoiDong.objects.create(
                ten_hoi_dong=request.POST.get("ten"),
                ngay_bao_ve=ngay,
                thoi_gian_bat_dau=thoi_gian_bat_dau,   # ✅ ĐÚNG
                thoi_gian_ket_thuc=thoi_gian_ket_thuc, # ✅ ĐÚNG
                dia_diem=request.POST.get("dia_diem"),
                ky=KyThucTap.objects.last()
            )

        except Exception as e:
            print("Lỗi:", e)
            return redirect("GiangVien:tao_hoi_dong")

        # Thêm giảng viên
        for gv_id in gv_ids:
            HoiDong_GiangVien.objects.create(hoi_dong=hd, giang_vien_id=gv_id)

        # Thêm sinh viên
        for sv_id in sv_ids:
            sv = SinhVien.objects.get(ma_sv=sv_id)
            gvhd = PhanCongGVHD.objects.filter(sinh_vien=sv).first()

            if gvhd and HoiDong_GiangVien.objects.filter(
                hoi_dong=hd,
                giang_vien=gvhd.giang_vien
            ).exists():
                continue

            HoiDong_SinhVien.objects.create(
                hoi_dong=hd,
                sinh_vien=sv
            )

        return redirect("GiangVien:hoi_dong_detail", id=hd.id)

    return render(request, "GiangVien/tao_hoi_dong.html", {
        "giangviens": GiangVien.objects.all(),
        "is_gvpt": True,
        "current_page": "hoi_dong"
    })
from django.http import JsonResponse
from django.db.models import Q

def load_sinh_vien(request):
    ky = KyThucTap.objects.last()
    if not ky:
        return JsonResponse([], safe=False)

    # Lấy danh sách ma_gv đã chọn từ query param
    gvs_param = request.GET.get('gvs', '')
    selected_gv_ids = [x.strip() for x in gvs_param.split(',') if x.strip()]

    # Lấy danh sách sinh viên chưa có trong bất kỳ hội đồng nào của kỳ này
    sv_da_co = HoiDong_SinhVien.objects.filter(
        hoi_dong__ky=ky
    ).values_list("sinh_vien__ma_sv", flat=True)

    queryset = SinhVien.objects.filter(ky_hien_tai=ky).exclude(ma_sv__in=sv_da_co)

    # Nếu có giảng viên được chọn → loại bỏ sinh viên có GVHD thuộc danh sách đó
    if selected_gv_ids:
        queryset = queryset.exclude(
            phanconggvhd__giang_vien__ma_gv__in=selected_gv_ids
        )

    data = []
    for sv in queryset:
        gvhd = PhanCongGVHD.objects.filter(sinh_vien=sv).first()
        data.append({
            "id": sv.ma_sv,
            "ten": sv.ho_ten,
            "lop": sv.lop,
            "gvhd": gvhd.giang_vien.ma_gv if gvhd else ""
        })

    return JsonResponse(data, safe=False)
def them_sinh_vien(request, id):

    hoidong = HoiDong.objects.get(id=id)

    if request.method == "POST":

        for sv_id in request.POST.getlist("sinh_vien"):

            sv = SinhVien.objects.get(ma_sv=sv_id)

            # 🔥 CHẶN TRÙNG HỘI ĐỒNG
            da_co = HoiDong_SinhVien.objects.filter(
                sinh_vien=sv,
                hoi_dong__ky=hoidong.ky
            ).exists()

            if da_co:
                continue

            gvhd = PhanCongGVHD.objects.filter(sinh_vien=sv).first()

            if gvhd:
                if HoiDong_GiangVien.objects.filter(
                        hoi_dong=hoidong,
                        giang_vien=gvhd.giang_vien
                ).exists():
                    continue

            HoiDong_SinhVien.objects.create(
                hoi_dong=hoidong,
                sinh_vien=sv
            )

        return redirect("GiangVien:hoi_dong_detail", id=id)

    return render(request, "GiangVien/them_sinh_vien.html", {
        "sinhviens": SinhVien.objects.all(),
        "hoidong": hoidong,        "is_gvpt": get_is_gvpt(request)

    })


from django.utils import timezone

def hoi_dong_detail(request, id):
    hoidong = get_object_or_404(HoiDong, id=id)
    is_gvpt = get_is_gvpt(request)
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()

    if not is_gvpt and gv:
        if not HoiDong_GiangVien.objects.filter(hoi_dong=hoidong, giang_vien=gv).exists():
            return redirect("GiangVien:hoi_dong_list")

    # Kiểm tra thời gian chấm điểm
    now = timezone.now()
    is_in_time = False
    if hoidong.thoi_gian_bat_dau and hoidong.thoi_gian_ket_thuc:
        is_in_time = (hoidong.thoi_gian_bat_dau <= now <= hoidong.thoi_gian_ket_thuc) and \
                     (hoidong.ngay_bao_ve == now.date())

    giangviens = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong).select_related('giang_vien')

    sv_list = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong).select_related('sinh_vien')

    data_sv = []
    for item in sv_list:
        sv = item.sinh_vien

        # Lấy điểm báo cáo (diem_bao_cao)
        bd = BangDiem.objects.filter(
            sinh_vien=sv,
            ky=hoidong.ky
        ).first()

        diem_value = bd.diem_bao_cao if bd else None

        data_sv.append({
            "sv": sv,
            "diem": diem_value,     # <-- Đảm bảo là số hoặc None
        })

    context = {
        "hoidong": hoidong,
        "giangviens": giangviens,
        "sinhviens": data_sv,
        "is_gvpt": is_gvpt,
        "current_page": "hoi_dong",
        "is_in_time": is_in_time,
        "now": now,
    }

    return render(request, "GiangVien/hoi_dong_detail.html", context)

@require_POST
def cham_diem_hoi_dong(request, id, ma_sv):
    hoidong = get_object_or_404(HoiDong, id=id)
    sv = get_object_or_404(SinhVien, ma_sv=ma_sv)

    ma_gv = request.user.username
    gv = get_object_or_404(GiangVien, ma_gv=ma_gv)

    now = timezone.now()

    # CHECK TIME
    if not (hoidong.thoi_gian_bat_dau and hoidong.thoi_gian_ket_thuc):
        return redirect("GiangVien:hoi_dong_detail", id=id)

    if not (hoidong.thoi_gian_bat_dau <= now <= hoidong.thoi_gian_ket_thuc) or \
       hoidong.ngay_bao_ve != now.date():
        return redirect("GiangVien:hoi_dong_detail", id=id)

    diem_str = request.POST.get("diem")

    if diem_str:
        diem = float(diem_str)

        # ✅ Lưu điểm từng giảng viên
        ChamDiemHoiDong.objects.update_or_create(
            hoi_dong=hoidong,
            sinh_vien=sv,
            giang_vien=gv,
            defaults={'diem': diem}
        )

        # ✅ TÍNH TRUNG BÌNH
        danh_sach_diem = ChamDiemHoiDong.objects.filter(
            hoi_dong=hoidong,
            sinh_vien=sv
        )

        avg = sum(d.diem for d in danh_sach_diem) / danh_sach_diem.count()

        # ✅ LƯU VÀO BangDiem
        bd, _ = BangDiem.objects.get_or_create(
            sinh_vien=sv,
            ky=hoidong.ky
        )

        bd.diem_bao_cao = round(avg, 2)
        bd.save()

    return redirect("GiangVien:hoi_dong_detail", id=id)


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
            return redirect('GiangVien:giangvien_home')
        
        if new_password != confirm_password:
            messages.error(request, "Xác nhận mật khẩu không khớp.", extra_tags='pwd_error')
            return redirect('GiangVien:giangvien_home')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Thay đổi mật khẩu thành công!", extra_tags='pwd_success')
        
    return redirect('GiangVien:giangvien_home')