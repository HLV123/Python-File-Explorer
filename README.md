


# Python File Explorer

Ứng dụng quản lý file hiện đại được xây dựng bằng Python và Tkinter, cung cấp giao diện trực quan để quản lý file và thư mục hiệu quả.

### Yêu cầu
- Python 3.7 hoặc cao hơn
- Trình quản lý gói pip

```bash
pip install -r requirements.txt
```
```bash
python main.py
```

## Cấu trúc dự án

```
python-file-explorer/
├── main.py                 # Điểm khởi động chính
├── app.py                  # Lớp ứng dụng chính
├── config.py              # Cấu hình ứng dụng
├── file_operations.py     # Thao tác file/thư mục
├── file_item.py          # Lớp đại diện file/thư mục
├── widgets.py            # Các widget giao diện
├── logger.py             # Hệ thống logging
├── exceptions.py         # Các exception tùy chỉnh
├── search_manager.py     # Quản lý tìm kiếm
├── recent_manager.py     # Quản lý file gần đây
├── bookmarks_manager.py  # Quản lý bookmark
├── theme_manager.py      # Quản lý theme
├── disk_analyzer.py      # Phân tích đĩa
├── drive_manager.py      # Quản lý ổ đĩa
└── requirements.txt      # Dependencies
```

```bash
# Cài đặt lại dependencies
pip install -r requirements.txt
```
### Log files
Ứng dụng tạo log file `file_explorer.log` trong thư mục hiện tại để debug.

## Tác giả

- **Lê Văn Hưng** - HE186837 - FPT University HOLA Campus

Nếu bạn thấy dự án này hữu ích, hãy cho một ⭐ trên GitHub!
