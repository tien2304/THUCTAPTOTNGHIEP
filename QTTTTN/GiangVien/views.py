from django.shortcuts import render
from Home.models import GiangVien, PhanCongGVPT,SinhVien, PhanCongGVHD, MauKhaoSat, CauHoi, LuaChon, KyThucTap, ChiTietTraLoi, PhieuTraLoi, TieuChiDanhGia

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
            ngay_bat_dau=data.get("start_date"),
            ngay_ket_thuc=data.get("end_date")
        )

        for i, q in enumerate(data["questions"]):

            cauhoi = CauHoi.objects.create(
                mau_khao_sat=form,
                noi_dung=q["title"],
                loai_cau_hoi=q["type"],
                thu_tu=i
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

        # return redirect("public_form",public_id=form.public_id)
        return redirect("GiangVien:public_form", public_id=form.public_id)

    return render(request,"GiangVien/tao_form.html",{
        "ky_moi_nhat": ky_moi_nhat,
    })
def public_form(request, public_id):

    form = MauKhaoSat.objects.get(public_id=public_id)

    questions = form.cau_hoi.prefetch_related("options", "tieuchi")

    return render(request, "GiangVien/public_form.html", {
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

        for key,value in request.POST.items():

            for key in request.POST:

                if key.startswith("question_"):

                    values = request.POST.getlist(key)

                    for v in values:
                        ChiTietTraLoi.objects.create(
                            phieu_tra_loi=phieu,
                            cau_hoi_id=key.replace("question_", ""),
                            gia_tri=v
                        )

        return render(request,"Forms/success.html")