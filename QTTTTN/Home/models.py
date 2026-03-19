from django.db import models
from django.contrib.auth.models import User
# --- NHÓM 1: NGƯỜI DÙNG & VAI TRÒ ---
class VaiTro(models.Model):
    role_id = models.AutoField(primary_key=True)
    ten_vai_tro = models.CharField(max_length=50) # SinhVien, GiangVien, GiaoVu, TruongBoMon
    def __str__(self):
        return f"{self.role_id} - {self.ten_vai_tro}"
class NguoiDung(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='nguoidung_profile')
    username = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True) # Lưu bản rõ để đối chiếu hoặc gán mặc định 1-9
    role = models.ForeignKey(VaiTro, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
# --- NHÓM 2: QUẢN LÝ KỲ THỰC TẬP & CÁC THỰC THỂ CHÍNH ---
class GiangVien(models.Model):
    HOC_VI_CHOICES = [
        ('Thạc sĩ', 'Thạc sĩ'),
        ('Tiến sĩ', 'Tiến sĩ'),
        ('Phó Giáo sư', 'Phó Giáo sư'),
        ('Giáo sư', 'Giáo sư'),
    ]
    CHUC_VU_CHOICES = [
        ('Giảng viên', 'Giảng viên'),
        ('Trưởng bộ môn', 'Trưởng bộ môn'),
        ('Giáo vụ', 'Giáo vụ'),
    ]
    CHUYEN_MON_CHOICES = [
        ('Phân tích thiết kế hệ thống (BA)', 'Phân tích thiết kế hệ thống (BA)'),
        ('Xây dựng hệ thống (DEV)', 'Xây dựng hệ thống (DEV)'),
        ('Artificial Intelligence (AI)', 'Artificial Intelligence (AI)'),
        ('Kiểm thử phần mềm', 'Kiểm thử phần mềm'),
        ('Phân tích dữ liệu (BI)', 'Phân tích dữ liệu (BI)'),
        ('An toàn bảo mật thông tin', 'An toàn bảo mật thông tin'),
        ('Triển khai ERP', 'Triển khai ERP'),
    ]
    ma_gv = models.CharField(max_length=20, primary_key=True)
    ho_ten = models.CharField(max_length=255)
    chuc_vu = models.CharField(max_length=100, choices=CHUC_VU_CHOICES, default='Giảng viên')
    hoc_vi = models.CharField(max_length=100, choices=HOC_VI_CHOICES, default='Thạc sĩ')
    chuyen_mon = models.CharField(max_length=500) # Lưu chuỗi các chuyên môn ghép lại
    so_dien_thoai = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.ho_ten
class KyThucTap(models.Model):
    ten_ky = models.CharField(max_length=255)
    ngay_bat_dau = models.DateField()
    ngay_ket_thuc = models.DateField()
    gv_phu_trach = models.ForeignKey(GiangVien, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.ten_ky
class SinhVien(models.Model):
    ma_sv = models.CharField(max_length=20, primary_key=True)
    ho_ten = models.CharField(max_length=255)
    lop = models.CharField(max_length=50)
    ky_hien_tai = models.ForeignKey(KyThucTap, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return f"{self.ma_sv} - {self.ho_ten}"
class SinhVien_KyThucTap(models.Model):
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    ky_thuc_tap = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
# --- NHÓM 3: KHẢO SÁT ĐỘNG (SURVEY MODULE) ---
import uuid
class MauKhaoSat(models.Model):
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    ten_form = models.CharField(max_length=255)
    ngay_tao = models.DateTimeField(auto_now_add=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    ngay_bat_dau = models.DateField(null=True, blank=True)
    ngay_ket_thuc = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.ten_form
class CauHoi(models.Model):

    LOAI_CHOICES = [
        ('TEXT', 'Câu hỏi ngắn'),
        ('RADIO', 'Trắc nghiệm'),
        ('LIKERT', 'Đánh giá 1-5'),
        ('SELECT', 'Menu thả xuống'),
        ('CHECKBOX', 'Hộp kiểm'),
    ]

    SYSTEM_TAG_CHOICES = [
        ('', 'Bình thường'),
        ('GVHD_1', 'Nguyện vọng GVHD 1'),
        ('GVHD_2', 'Nguyện vọng GVHD 2'),
        # HƯỚNG
        ('HUONG_1', 'Hướng đề tài 1'),
        ('HUONG_2', 'Hướng đề tài 2'),

        # NHÓM
        ('GROUP', 'Làm nhóm'),
        ('GROUP_MEMBER', 'Thành viên nhóm'),

    ]

    mau_khao_sat = models.ForeignKey(MauKhaoSat,related_name='cau_hoi', on_delete=models.CASCADE)
    noi_dung = models.TextField()
    loai_cau_hoi = models.CharField(max_length=20,choices=LOAI_CHOICES)
    # 🔥 QUAN TRỌNG NHẤT
    system_tag = models.CharField(max_length=50,choices=SYSTEM_TAG_CHOICES,default="",blank=True)
    thu_tu = models.IntegerField(default=0)
class TieuChiDanhGia(models.Model):

    cau_hoi = models.ForeignKey(CauHoi,related_name="tieuchi",on_delete=models.CASCADE)
    noi_dung = models.CharField(max_length=255)

class LuaChon(models.Model):

    cau_hoi = models.ForeignKey(CauHoi,related_name="options",on_delete=models.CASCADE)
    noi_dung_option = models.CharField(max_length=255)
class PhieuTraLoi(models.Model):
    mau_khao_sat = models.ForeignKey(MauKhaoSat, on_delete=models.CASCADE)
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    thoi_gian_nop = models.DateTimeField(auto_now_add=True)
class ChiTietTraLoi(models.Model):
    phieu_tra_loi = models.ForeignKey(PhieuTraLoi, related_name='answers', on_delete=models.CASCADE)
    cau_hoi = models.ForeignKey(CauHoi, on_delete=models.CASCADE)
    gia_tri = models.TextField()  # Lưu câu trả lời của SV hoặc điểm DN
# --- NHÓM 4: PHÂN CÔNG & CHẤM ĐIỂM ---
class PhanCongGVHD(models.Model):
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    giang_vien = models.ForeignKey(GiangVien, on_delete=models.CASCADE)
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    ngay_phan_cong = models.DateTimeField(auto_now_add=True)
    trang_thai = models.IntegerField(default=1)  # 1: Chờ, 2: Đã phân công
class PhanCongGVPT(models.Model):
    giang_vien = models.ForeignKey(GiangVien, on_delete=models.CASCADE)
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    ngay_phan_cong = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('giang_vien', 'ky')
class TyLeDiem(models.Model):
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    diem_gvhd = models.FloatField(default=0.4)
    diem_hoidong = models.FloatField(default=0.4)
    diem_doanhnghiep = models.FloatField(default=0.2)
class BangDiem(models.Model):
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    diem_qua_trinh = models.FloatField(null=True, blank=True)       # GVHD nhập
    diem_doanh_nghiep = models.FloatField(null=True, blank=True)    # Lấy từ system_tag='diem_dn'
    diem_bao_cao = models.FloatField(null=True, blank=True)         # Hội đồng nhập
    diem_tong_ket = models.FloatField(null=True, blank=True)

    def calculate_total(self):
        tyle = TyLeDiem.objects.filter(ky=self.ky).first()
        if tyle and self.diem_qua_trinh and self.diem_doanh_nghiep and self.diem_bao_cao:
            self.diem_tong_ket = (
                (self.diem_qua_trinh * tyle.diem_gvhd) +
                (self.diem_doanh_nghiep * tyle.diem_doanhnghiep) +
                (self.diem_bao_cao * tyle.diem_hoidong)
            )
            self.save()
# --- NHÓM 5: CHUYÊN MÔN (NHIỆM VỤ, HỘI ĐỒNG, TÀI LIỆU) ---
class NhiemVu(models.Model):
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    ten_nhiem_vu = models.CharField(max_length=255)
    han_nop = models.DateTimeField()
    mo_ta = models.TextField()
class BaiNop(models.Model):
    nhiem_vu = models.ForeignKey(NhiemVu, on_delete=models.CASCADE)
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
    file_path = models.FileField(upload_to='assignments/')
    ten_file = models.CharField(max_length=255)
    thoi_gian_nop = models.DateTimeField(auto_now_add=True)
    trang_thai = models.CharField(max_length=50)
class HoiDong(models.Model):
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    ten_hoi_dong = models.CharField(max_length=255)
    thoi_gian = models.DateTimeField()
    dia_diem = models.CharField(max_length=255)
    ngay_bao_ve = models.DateField()
class HoiDong_GiangVien(models.Model):
    hoi_dong = models.ForeignKey(HoiDong, on_delete=models.CASCADE)
    giang_vien = models.ForeignKey(GiangVien, on_delete=models.CASCADE)
class HoiDong_SinhVien(models.Model):
    hoi_dong = models.ForeignKey(HoiDong, on_delete=models.CASCADE)
    sinh_vien = models.ForeignKey(SinhVien, on_delete=models.CASCADE)
class TaiLieu(models.Model):
    ky = models.ForeignKey(KyThucTap, on_delete=models.CASCADE)
    mo_ta = models.TextField()
    ten_tai_lieu = models.CharField(max_length=255)
    duong_dan_file = models.FileField(upload_to='documents/')
    ngay_cap_nhat = models.DateTimeField(auto_now=True)
    gv_dang = models.ForeignKey(GiangVien, on_delete=models.CASCADE)
