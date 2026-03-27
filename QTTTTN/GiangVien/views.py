from django.shortcuts import render
from Home.models import (GiangVien, PhanCongGVPT,SinhVien,
                         PhanCongGVHD, MauKhaoSat, CauHoi, LuaChon, BaiNop, NhiemVu, BangDiem, KyThucTap,
                         KyThucTap, ChiTietTraLoi, PhieuTraLoi, TieuChiDanhGia, HoiDong, HoiDong_SinhVien,HoiDong_GiangVien)
from django.shortcuts import get_object_or_404

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

def sinhvien_huongdan(request):

    ma_gv = request.user.username  # username = ma_gv
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()

    danh_sach = PhanCongGVHD.objects.filter(
        giang_vien=gv
    ).select_related('sinh_vien', 'ky')

    for item in danh_sach:
        sv = item.sinh_vien

        # 🔥 ƯU TIÊN 1: DB chính
        if sv.noi_thuc_tap:
            item.noi_thuc_tap = sv.noi_thuc_tap
            continue

        # 🔥 ƯU TIÊN 2: lấy từ form
        phieu = PhieuTraLoi.objects.filter(
            sinh_vien=sv
        ).order_by("-id").first()

        noi_tt = ""

        if phieu:
            for ans in phieu.answers.all():
                tag = (ans.cau_hoi.system_tag or "").strip()

                if tag == "don_vi_tt":
                    noi_tt = ans.gia_tri

                    # 🔥 SAVE LUÔN vào DB chính (rất hay)
                    sv.noi_thuc_tap = noi_tt
                    sv.save()
                    break

        item.noi_thuc_tap = noi_tt or ""

    context = {
        'danh_sach': danh_sach,
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
from django.views.decorators.http import require_POST

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

from django.views.decorators.http import require_POST

@require_POST
def update_noi_thuc_tap(request, ma_sv):
    sv = SinhVien.objects.get(ma_sv=ma_sv)
    noi_tt = request.POST.get("noi_tt")

    if noi_tt:
        sv.noi_thuc_tap = noi_tt
        sv.save()

    return redirect("GiangVien:sinhvien_huongdan")
import json
from django.shortcuts import render,redirect
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
        "is_gvpt": get_is_gvpt(request)
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

        # 2. Xóa câu hỏi cũ để ghi đè (hoặc cập nhật tùy logic của ông)
        form.cau_hoi.all().delete()

        # 3. Lưu danh sách câu hỏi mới
        for i, q in enumerate(data["questions"]):
            cauhoi = CauHoi.objects.create(
                mau_khao_sat=form,
                noi_dung=q["title"],
                loai_cau_hoi=q["type"],
                thu_tu=i,
                system_tag=q.get("system_tag", "")
            )

            # Lưu Options (Cho Radio, Checkbox, Select)
            for op in q.get("options", []):
                if op.get("text"):  # Chỉ lưu nếu có nội dung
                    LuaChon.objects.create(
                        cau_hoi=cauhoi,
                        noi_dung_option=op["text"]
                    )

            # SỬA TẠI ĐÂY: Đổi 'criteria' thành 'rows' để khớp với JS
            for tc in q.get("rows", []):
                if tc.get("text"):
                    TieuChiDanhGia.objects.create(
                        cau_hoi=cauhoi,
                        noi_dung=tc["text"]
                    )

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

    return render(request, "GiangVien/tao_form.html", {
        "form": form,
        "questions_json": json.dumps(questions_data),  # Truyền xuống để JS render()
        "ky_moi_nhat": form.ky,
        "danh_sach_ky": danh_sach_ky,
        "gvhd_stats": dict(gvhd_counter),
        "is_edit": True,
        "is_gvpt": get_is_gvpt(request)
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
def save_assign(request):

    if request.method == "POST":

        sv_ids = request.POST.getlist("sv")
        gv_name = request.POST.get("gv")

        gv = GiangVien.objects.get(ho_ten=gv_name)
        ky = KyThucTap.objects.last()

        for sv_id in sv_ids:
            sv = SinhVien.objects.get(ma_sv=sv_id)

            PhanCongGVHD.objects.update_or_create(
                sinh_vien=sv,
                defaults={
                    "giang_vien": gv,
                    "ky": ky,
                    "trang_thai": 2
                }
            )

    return redirect("GiangVien:phan_cong")

def confirm_assign(request):

    if request.method == "POST":

        sv_ids = request.POST.getlist("sv")

        gvs = GiangVien.objects.all()

        return render(request, "GiangVien/select_gv.html", {
            "sv_ids": sv_ids,
            "gvs": gvs
        })
from collections import defaultdict
from django.http import JsonResponse

# ========================
# LẤY FORM NGUYỆN VỌNG
# ========================
def get_form_nguyen_vong():

    ky = KyThucTap.objects.order_by("-id").first()

    form = MauKhaoSat.objects.filter(
        ky=ky,
        cau_hoi__system_tag__in=["GVHD_1", "GVHD_2"]
    ).distinct().order_by("-ngay_tao").first()

    return ky, form


# ========================
# DASHBOARD
# ========================
def phan_cong_dashboard(request):

    ky, form = get_form_nguyen_vong()

    if not form:
        return render(request, "GiangVien/phan_cong.html", {
            "data": [],
            "gv_stats": [],
            "is_gvpt": get_is_gvpt(request)
        })

    sinhviens = SinhVien.objects.filter(ky_hien_tai=ky)

    data = []

    for sv in sinhviens:

        phieu = PhieuTraLoi.objects.filter(
            sinh_vien=sv,
            mau_khao_sat=form
        ).first()

        nv1 = ""
        nv2 = ""
        de_tai = ""
        group = ""

        if phieu:
            for a in phieu.answers.all():
                tag = (a.cau_hoi.system_tag or "").strip().upper()
                val = (a.gia_tri or "").strip()

                if tag == "GVHD_1":
                    nv1 = val
                elif tag == "GVHD_2":
                    nv2 = val
                elif tag == "DE_TAI":
                    de_tai = val
                elif tag == "GROUP":
                    group = val

        pc = PhanCongGVHD.objects.filter(sinh_vien=sv, ky=ky).first()

        status = ""
        if pc:
            if pc.giang_vien.ho_ten == nv1:
                status = "NV1"
            elif pc.giang_vien.ho_ten == nv2:
                status = "NV2"

        data.append({
            "id": sv.ma_sv,
            "ten": sv.ho_ten,
            "lop": sv.lop,
            "de_tai": de_tai or "--",
            "nv1": nv1,
            "nv2": nv2,
            "group": group or "Không",
            "gvhd": pc.giang_vien.ho_ten if pc else "",
            "status": status
        })

    # SORT NV1 lên trước
    data.sort(key=lambda x: (0 if x["nv1"] else 1))

    # ===== GV STATS =====
    gv_stats = []

    for gv in GiangVien.objects.all():
        count = gv_wish_count.get(gv.ho_ten.strip().lower(), 0)

        gv_stats.append({
            "ten": gv.ho_ten,
            "count": count,
            "overload": count > 10
        })

    return render(request, "GiangVien/phan_cong.html", {
        "data": data,
        "gv_stats": gv_stats,
        "is_gvpt": get_is_gvpt(request)
    })
gv_wish_count = defaultdict(int)

# ========================
# AUTO ASSIGN (UI)
# ========================
# RUN AUTO
# ========================
def run_auto_assign_ui(request):
    ky, form = get_form_nguyen_vong()
    auto_assign(form.id)
    return redirect("GiangVien:phan_cong")


# ========================
# UPDATE MANUAL
# ========================
def update_phan_cong(request):

    if request.method == "POST":

        sv_id = request.POST.get("sv")
        gv_name = request.POST.get("gv")

        sv = SinhVien.objects.get(ma_sv=sv_id)
        gv = GiangVien.objects.get(ho_ten=gv_name)

        ky = KyThucTap.objects.order_by("-id").first()

        PhanCongGVHD.objects.update_or_create(
            sinh_vien=sv,
            defaults={
                "giang_vien": gv,
                "ky": ky,
                "trang_thai": 2
            }
        )

        return JsonResponse({"status": "ok"})
def select_sinh_vien(request):

    ky, form = get_form_nguyen_vong()

    sinhviens = SinhVien.objects.filter(ky_hien_tai=ky)

    data = []

    for sv in sinhviens:

        phieu = PhieuTraLoi.objects.filter(
            sinh_vien=sv,
            mau_khao_sat=form
        ).first()

        nv = ""

        if phieu:
            for a in phieu.answers.select_related("cau_hoi"):
                if a.cau_hoi.system_tag == "GVHD_1":
                    nv = a.gia_tri

        data.append({
            "id": sv.ma_sv,
            "ten": sv.ho_ten,
            "lop": sv.lop,
            "nv": nv
        })

    return render(request, "GiangVien/select_sv.html", {
        "data": data
    })

# BUILD PROFILE
# ========================
def build_profiles(form):

    answers = ChiTietTraLoi.objects.select_related(
        "phieu_tra_loi__sinh_vien",
        "cau_hoi"
    ).filter(
        phieu_tra_loi__mau_khao_sat=form
    )

    data = defaultdict(dict)

    for ans in answers:
        sv = ans.phieu_tra_loi.sinh_vien
        tag = ans.cau_hoi.system_tag

        if tag:
            data[sv][tag] = ans.gia_tri

    return data


# ========================
# AUTO ASSIGN
# ========================
def auto_assign(form_id):

    ky = KyThucTap.objects.order_by("-id").first()
    form = MauKhaoSat.objects.get(id=form_id)

    sinhviens = SinhVien.objects.filter(ky_hien_tai=ky)

    # ===== LOAD hiện tại =====
    gv_load = defaultdict(int)

    for pc in PhanCongGVHD.objects.filter(ky=ky):
        key = pc.giang_vien.ho_ten.strip().lower()
        gv_load[key] += 1

    # ===== LOAD NGUYỆN VỌNG =====
    sv_data = []

    for sv in sinhviens:

        phieu = PhieuTraLoi.objects.filter(
            sinh_vien=sv,
            mau_khao_sat=form
        ).first()

        nv1 = ""
        nv2 = ""
        de_tai = ""
        group = ""

        if phieu:
            for a in phieu.answers.all():
                tag = (a.cau_hoi.system_tag or "").strip().upper()
                val = (a.gia_tri or "").strip()

                if tag == "GVHD_1":
                    nv1 = val
                elif tag == "GVHD_2":
                    nv2 = val
                elif tag == "DE_TAI":
                    de_tai = val
                elif tag == "GROUP":
                    group = val

        sv_data.append({
            "sv": sv,
            "nv1": nv1,
            "nv2": nv2
        })

    # ===== AUTO ASSIGN =====
    for item in sv_data:

        sv = item["sv"]
        assigned = None

        # 🔥 NV1
        if item["nv1"]:
            key = item["nv1"].lower()
            if gv_load[key] < 10:
                assigned = item["nv1"]
                gv_load[key] += 1

        # 🔥 NV2
        if not assigned and item["nv2"]:
            key = item["nv2"].lower()
            if gv_load[key] < 10:
                assigned = item["nv2"]
                gv_load[key] += 1

        # SAVE
        if assigned:
            gv = GiangVien.objects.get(ho_ten=assigned)

            PhanCongGVHD.objects.update_or_create(
                sinh_vien=sv,
                defaults={
                    "giang_vien": gv,
                    "ky": ky,
                    "trang_thai": 2
                }
            )

from django.http import HttpResponse
import json
from collections import defaultdict
# ========================
# RUN AUTO ASSIGN
# ========================
def run_auto_assign(request, form_id):

    auto_assign(form_id)

    return HttpResponse("Đã phân công xong")

def hoi_dong_list(request):

    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()

    is_gvpt = get_is_gvpt(request)

    # 👑 GV PHỤ TRÁCH → thấy tất cả
    if is_gvpt:
        hoidongs = HoiDong.objects.all()

    # 👨‍🏫 GV thường → chỉ thấy hội đồng mình thuộc
    else:
        hoidongs = HoiDong.objects.filter(
            hoidong_giangvien__giang_vien=gv
        ).distinct()

    return render(request, "GiangVien/hoi_dong_list.html", {
        "hoidongs": hoidongs,
        "current_page": "hoi_dong",
        "is_gvpt": is_gvpt
    })

def tao_hoi_dong(request):

    if not get_is_gvpt(request):
        return redirect("GiangVien:hoi_dong_list")
    ky = KyThucTap.objects.last()

    sinhviens = SinhVien.objects.filter(ky_hien_tai=ky)

    if request.method == "POST":

        gv_ids = request.POST.getlist("giang_vien")
        sv_ids = request.POST.get("sinh_vien_ids").split(",")

        hd = HoiDong.objects.create(
            ten_hoi_dong=request.POST.get("ten"),
            ngay_bao_ve=request.POST.get("ngay"),
            dia_diem=request.POST.get("dia_diem"),
            thoi_gian=request.POST.get("thoi_gian"),
            ky=KyThucTap.objects.last()
        )

        # GV
        for gv_id in gv_ids:
            HoiDong_GiangVien.objects.create(
                hoi_dong=hd,
                giang_vien_id=gv_id
            )

        # SV
        for sv_id in sv_ids:
            if not sv_id:
                continue

            sv = SinhVien.objects.get(ma_sv=sv_id)

            gvhd = PhanCongGVHD.objects.filter(sinh_vien=sv).first()

            # ❌ CHẶN GVHD
            if gvhd and gvhd.giang_vien.ma_gv in gv_ids:
                continue

            HoiDong_SinhVien.objects.create(
                hoi_dong=hd,
                sinh_vien=sv
            )

        return redirect("GiangVien:hoi_dong_detail", id=hd.id)

    return render(request, "GiangVien/tao_hoi_dong.html", {
        "giangviens": GiangVien.objects.all(),
        "sinhviens": sinhviens,  # 👈 THÊM DÒNG NÀY
        "is_gvpt": True,
        "current_page": "hoi_dong"
    })
def load_sinh_vien(request):
    ky = KyThucTap.objects.last()

    sv_da_co = HoiDong_SinhVien.objects.filter(
        hoi_dong__ky=ky
    ).values_list("sinh_vien_id", flat=True)

    sinhviens = SinhVien.objects.filter(
        ky_hien_tai=ky
    ).exclude(
        ma_sv__in=sv_da_co
    )

    data = []

    for sv in sinhviens:
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

            gvhd = PhanCongGVHD.objects.filter(sinh_vien=sv).first()

            if gvhd:
                if HoiDong_GiangVien.objects.filter(
                    hoi_dong=hoidong,
                    giang_vien=gvhd.giang_vien
                ).exists():
                    continue  # ❌ bỏ nếu trùng GVHD

            HoiDong_SinhVien.objects.create(
                hoi_dong=hoidong,
                sinh_vien=sv
            )

        return redirect("GiangVien:hoi_dong_detail", id=id)

    return render(request, "GiangVien/them_sinh_vien.html", {
        "sinhviens": SinhVien.objects.all(),
        "hoidong": hoidong,        "is_gvpt": get_is_gvpt(request)

    })


def hoi_dong_detail(request, id):
    hoidong = get_object_or_404(HoiDong, id=id)
    is_gvpt = get_is_gvpt(request)
    ma_gv = request.user.username
    gv = GiangVien.objects.filter(ma_gv=ma_gv).first()

    if not is_gvpt and gv:
        if not HoiDong_GiangVien.objects.filter(hoi_dong=hoidong, giang_vien=gv).exists():
            return redirect("GiangVien:hoi_dong_list")

    giangviens = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong).select_related('giang_vien')

    # Lấy danh sách sinh viên + điểm
    sv_list = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong).select_related('sinh_vien')

    data_sv = []
    for item in sv_list:
        sv = item.sinh_vien

        # SỬA TẠI ĐÂY: Truy vấn bằng ma_sv cụ thể để tránh lỗi mapping đối tượng
        bd = BangDiem.objects.filter(
            sinh_vien_id=sv.ma_sv,
            ky_id=hoidong.ky_id
        ).first()

        diem_value = None
        if bd:
            # Đảm bảo lấy đúng trường diem_bao_cao (điểm hội đồng)
            diem_value = bd.diem_bao_cao

        data_sv.append({
            "sv": sv,
            "diem": diem_value,
        })

    return render(request, "GiangVien/hoi_dong_detail.html", {
        "hoidong": hoidong,
        "giangviens": giangviens,
        "sinhviens": data_sv,  # Key này phải khớp với {% for item in sinhviens %}
        "is_gvpt": is_gvpt,
        "current_page": "hoi_dong"
    })

@require_POST
def cham_diem_hoi_dong(request, id, ma_sv):
    sv = get_object_or_404(SinhVien, ma_sv=ma_sv)
    hoidong = get_object_or_404(HoiDong, id=id)
    diem_str = request.POST.get("diem")

    if diem_str:
        # Sử dụng update_or_create để đảm bảo không tạo bản ghi rác
        bd, created = BangDiem.objects.update_or_create(
            sinh_vien=sv,
            ky=hoidong.ky,
            defaults={'diem_bao_cao': float(diem_str)}
        )
        # Gọi hàm tính tổng kết nếu có
        bd.calculate_total()

    return redirect("GiangVien:hoi_dong_detail", id=id)