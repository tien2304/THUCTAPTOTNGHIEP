from django.shortcuts import render
from Home.models import (GiangVien, PhanCongGVPT,SinhVien,
                         PhanCongGVHD, MauKhaoSat, CauHoi, LuaChon,
                         KyThucTap, ChiTietTraLoi, PhieuTraLoi, TieuChiDanhGia, HoiDong, HoiDong_SinhVien,HoiDong_GiangVien)

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

    danh_sach = PhanCongGVHD.objects.select_related(
        'sinh_vien', 'giang_vien', 'ky'
    )

    context = {
        'danh_sach': danh_sach,
        'current_page': 'home'
    }

    return render(request, 'GiangVien/sinhvien_huongdan.html', context)

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

    ky_moi_nhat = KyThucTap.objects.order_by("-id").first()

    if request.method == "POST":

        raw = request.POST.get("form_data")
        data = json.loads(raw)

        form = MauKhaoSat.objects.create(
            ky=ky_moi_nhat,
            ten_form=data["ten_form"],
            ngay_bat_dau=ky_moi_nhat.ngay_bat_dau,
            ngay_ket_thuc=ky_moi_nhat.ngay_ket_thuc
        )

        for i, q in enumerate(data["questions"]):

            cauhoi = CauHoi.objects.create(
                mau_khao_sat=form,
                noi_dung=q["title"],
                loai_cau_hoi=q["type"],
                thu_tu=i,
                system_tag=q.get("system_tag", "")
            )

            # Lưu options (radio, checkbox, dropdown)
            for op in q.get("options", []):
                LuaChon.objects.create(
                    cau_hoi=cauhoi,
                    noi_dung_option=op["text"]
                )

            # Lưu tiêu chí (LIKERT)
            for tc in q.get("criteria", []):
                TieuChiDanhGia.objects.create(
                    cau_hoi=cauhoi,
                    noi_dung=tc["text"]
                )

        return redirect("GiangVien:form_list")

    return render(request,"GiangVien/tao_form.html",{
        "ky_moi_nhat": ky_moi_nhat,"is_gvpt": get_is_gvpt(request)
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

    form = MauKhaoSat.objects.get(public_id=public_id)

    if request.method == "POST":
        data = json.loads(request.POST.get("form_data"))

        form.ten_form = data["ten_form"]
        form.save()

        form.cau_hoi.all().delete()

        for i, q in enumerate(data["questions"]):

            cauhoi = CauHoi.objects.create(
                mau_khao_sat=form,
                noi_dung=q["title"],
                loai_cau_hoi=q["type"],
                thu_tu=i,
                system_tag=q.get("system_tag","")
            )

            for op in q.get("options", []):
                LuaChon.objects.create(
                    cau_hoi=cauhoi,
                    noi_dung_option=op["text"]
                )

            for tc in q.get("criteria", []):
                TieuChiDanhGia.objects.create(
                    cau_hoi=cauhoi,
                    noi_dung=tc["text"]
                )

        return redirect("GiangVien:edit_form", public_id=public_id)

    # ===== LOAD QUESTIONS =====
    questions = []

    gvhd_counter = Counter()

    for q in form.cau_hoi.all():

        answers = q.chitiettraloi_set.all()
        values = [a.gia_tri for a in answers]

        stats = Counter(values)

        if q.system_tag in ["GVHD_1","GVHD_2"]:
            for v in values:
                gvhd_counter[v] += 1

        questions.append({
            "title": q.noi_dung,
            "type": q.loai_cau_hoi,
            "system_tag": q.system_tag,
            "options": [{"text": o.noi_dung_option} for o in q.options.all()],
            "criteria": [{"text": c.noi_dung} for c in q.tieuchi.all()],
            "stats": dict(stats)
        })

    return render(request, "GiangVien/tao_form.html", {
        "form": form,
        "questions_json": json.dumps(questions),
        "ky_moi_nhat": form.ky,
        "stats_json": json.dumps(questions),  # 🔥 thêm
        "gvhd_stats": dict(gvhd_counter),
        "is_edit": True, "is_gvpt": get_is_gvpt(request)
    })
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

        phieu = PhieuTraLoi.objects.create(
                sinh_vien=SinhVien.objects.first(),
            mau_khao_sat=form
        )

        for key in request.POST:
            if key.startswith("question_"):
                values = request.POST.getlist(key)

                for v in values:
                    ChiTietTraLoi.objects.create(
                        phieu_tra_loi=phieu,
                        cau_hoi_id=key.replace("question_", ""),
                        gia_tri=v
                    )

        return render(request, "Forms/success.html")

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

    form = MauKhaoSat.objects.get(id=form_id)
    sv_data = build_profiles(form)

    gvs = list(GiangVien.objects.all())
    gv_count = defaultdict(int)

    for pc in PhanCongGVHD.objects.all():
        gv_count[pc.giang_vien] += 1

    def score(sv, gv):

        s = 0

        if sv.get("GVHD_1") == gv.ho_ten:
            s += 3
        elif sv.get("GVHD_2") == gv.ho_ten:
            s += 2

        if sv.get("HUONG_1", "").lower() in gv.chuyen_mon.lower():
            s += 2
        elif sv.get("HUONG_2", "").lower() in gv.chuyen_mon.lower():
            s += 1

        if sv.get("GROUP") == "Có":
            s += 1

        return s

    for sv, profile in sv_data.items():

        best = None
        best_score = -1

        for gv in gvs:

            if gv_count[gv] >= 10:
                continue

            sc = score(profile, gv)

            if sc > best_score:
                best_score = sc
                best = gv

        if not best:
            best = min(gvs, key=lambda g: gv_count[g])

        PhanCongGVHD.objects.update_or_create(
            sinh_vien=sv,
            defaults={
                "giang_vien": best,
                "ky": form.ky,
                "trang_thai": 2
            }
        )

        gv_count[best] += 1

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

    if not get_is_gvpt(request):
        return redirect("GiangVien:giangvien_home")

    hoidongs = HoiDong.objects.all()

    return render(request, "GiangVien/hoi_dong_list.html", {
        "hoidongs": hoidongs,
        "current_page": "hoi_dong",
        "is_gvpt": get_is_gvpt(request)
    })

def tao_hoi_dong(request):

    if not get_is_gvpt(request):
        return redirect("GiangVien:giangvien_home")

    if request.method == "POST":
        thoi_gian = request.POST.get("thoi_gian")
        hd = HoiDong.objects.create(
            ten_hoi_dong=request.POST.get("ten"),
            ngay_bao_ve=request.POST.get("ngay"),
            dia_diem=request.POST.get("dia_diem"),
            thoi_gian=thoi_gian,
            ky=KyThucTap.objects.last()
        )

        gv_ids = request.POST.getlist("giang_vien")

        for gv_id in gv_ids:
            HoiDong_GiangVien.objects.create(
                hoi_dong=hd,
                giang_vien_id=gv_id
            )

        return redirect("GiangVien:hoi_dong_detail", id=hd.id)

    return render(request, "GiangVien/tao_hoi_dong.html", {
        "giangviens": GiangVien.objects.all(),
        "is_gvpt": get_is_gvpt(request)
    })

def them_sinh_vien(request, id):

    hoidong = HoiDong.objects.get(id=id)

    if request.method == "POST":

        for sv_id in request.POST.getlist("sinh_vien"):

            sv = SinhVien.objects.get(pk=sv_id)

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
    hoidong = HoiDong.objects.get(id=id)

    giangviens = HoiDong_GiangVien.objects.filter(hoi_dong=hoidong)
    sinhviens = HoiDong_SinhVien.objects.filter(hoi_dong=hoidong)

    return render(request, "GiangVien/hoi_dong_detail.html", {
        "hoidong": hoidong,
        "giangviens": giangviens,
        "sinhviens": sinhviens,
        "is_gvpt": get_is_gvpt(request)

    })