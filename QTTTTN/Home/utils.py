from django.contrib.auth.models import User
from Home.models import NguoiDung, VaiTro

def sync_user_account(username, full_name, role_name, password="123456789"):
    """
    Đảm bảo có User và NguoiDung tương ứng với username (ma_sv hoặc ma_gv).
    - Mật khẩu mặc định: 123456789 (nếu tạo mới).
    """
    # 1. Lấy hoặc tạo VaiTro (ID sẽ tự động nếu chưa có, nhưng tốt nhất là init db trước)
    role_obj, _ = VaiTro.objects.get_or_create(ten_vai_tro=role_name)
    
    # 2. Tạo hoặc cập nhật User
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
    
    # Luôn cập nhật họ tên theo thứ tự tiếng Việt (Họ lót -> Tên)
    parts = full_name.split(' ')
    if len(parts) > 1:
        user.first_name = " ".join(parts[:-1]) # Ví dụ: Nguyễn Văn
        user.last_name = parts[-1]            # Ví dụ: A
    else:
        user.first_name = full_name
    user.save()
    
    # 3. Tạo hoặc cập nhật NguoiDung profile
    NguoiDung.objects.update_or_create(
        user=user,
        defaults={
            'role': role_obj,
            'username': username,
            'password': password
        }
    )
    return user
