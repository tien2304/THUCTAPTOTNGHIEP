from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from Home.models import NguoiDung, VaiTro

def groups_required(*group_names):
   """Kiểm tra người dùng có thuộc ít nhất một trong các nhóm (vai trò) chỉ định hay không."""
   def in_groups(u):
       if u.is_authenticated:
           # Kiểm tra Superuser hoặc Vai trò trong bảng NguoiDung
           if u.is_superuser:
               return True
           
           # Thử lấy vai trò từ profile NguoiDung
           try:
               if hasattr(u, 'nguoidung') and u.nguoidung.role.ten_vai_tro in group_names:
                   return True
           except:
               pass
               
           # Vẫn kiểm tra Groups mặc định để tương thích ngược
           if u.groups.filter(name__in=group_names).exists():
               return True
       return False
   return user_passes_test(in_groups, login_url='login')

def sync_user_account(username, full_name, role_name, password=None):
    """
    Đảm bảo có User và NguoiDung tương ứng với username (ma_sv hoặc ma_gv).
    - Mật khẩu mặc định: 123456789 (nếu tạo mới và không cung cấp mật khẩu).
    """
    # 1. Lấy hoặc tạo VaiTro
    role_obj, _ = VaiTro.objects.get_or_create(ten_vai_tro=role_name)
    
    # 2. Tạo hoặc cập nhật User
    user, created = User.objects.get_or_create(username=username)
    
    # Xử lý mật khẩu
    if created:
        if not password:
            password = "123456789"
        user.set_password(password)
    elif password:
        # Nếu user đã tồn tại và có cung cấp password mới -> Cập nhật
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
            'password': password if password else "123456789" # Lưu lại để tham khảo (tùy thiết kế cũ)
        }
    )
    return user
