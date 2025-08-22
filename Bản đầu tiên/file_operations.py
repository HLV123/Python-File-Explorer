# file_operations.py

import os
import shutil
from datetime import datetime
from send2trash import send2trash # Sử dụng send2trash để an toàn hơn

class FileOperations:
    """
    Lớp chứa các phương thức tĩnh để thực hiện các thao tác trên hệ thống tệp.
    """
    @staticmethod
    def get_directory_contents(path):
        """Lấy danh sách các tệp và thư mục trong một đường dẫn."""
        try:
            items = []
            for item_name in os.listdir(path):
                full_path = os.path.join(path, item_name)
                try:
                    is_dir = os.path.isdir(full_path)
                    size = os.path.getsize(full_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
                    items.append({
                        "name": item_name,
                        "path": full_path,
                        "is_dir": is_dir,
                        "size": size,
                        "modified": mod_time
                    })
                except OSError:
                    # Bỏ qua các tệp không thể truy cập (ví dụ: system files)
                    continue
            return items
        except OSError as e:
            print(f"Lỗi khi truy cập {path}: {e}")
            return None

    @staticmethod
    def send_to_trash(path):
        """Gửi tệp hoặc thư mục vào thùng rác một cách an toàn."""
        try:
            send2trash(path)
            return True, f"Đã chuyển '{os.path.basename(path)}' vào thùng rác."
        except Exception as e:
            return False, f"Lỗi khi xóa: {e}"

    @staticmethod
    def create_folder(path, folder_name):
        """Tạo một thư mục mới."""
        full_path = os.path.join(path, folder_name)
        try:
            os.makedirs(full_path, exist_ok=True)
            return True, f"Đã tạo thư mục '{folder_name}'."
        except OSError as e:
            return False, f"Lỗi khi tạo thư mục: {e}"

    @staticmethod
    def rename_item(old_path, new_name):
        """Đổi tên một tệp hoặc thư mục."""
        if not new_name:
            return False, "Tên mới không được để trống."
            
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        if os.path.exists(new_path):
            return False, f"Tên '{new_name}' đã tồn tại."
        
        try:
            shutil.move(old_path, new_path)
            return True, "Đổi tên thành công."
        except OSError as e:
            return False, f"Lỗi khi đổi tên: {e}"