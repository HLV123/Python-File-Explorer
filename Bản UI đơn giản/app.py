import tkinter as tk
from tkinter import ttk
import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, List

try:
    from config import Config
    from file_operations import FileOperations
    from file_item import FileItem
    from widgets import (PathEntry, FileTreeView, ActionButtons, StatusBar, 
                        InputDialog, InfoDialog)
    from exceptions import *
    from logger import Logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required files are in the same directory")
    sys.exit(1)


class FileExplorerApp:
    def __init__(self, root):
        self.root = root
        self.current_path = Config.DEFAULT_START_PATH
        self.file_ops = FileOperations()
        self.show_hidden = False
        self.selected_items = []
        self.clipboard_items = []
        self.clipboard_action = None
        self._is_closing = False
        
        self._setup_window()
        self._create_widgets()
        self._setup_menu()
        self._setup_shortcuts()
        self._setup_error_handling()
        self.navigate_to(self.current_path)
        
        Logger.log_info(f"File Explorer started at: {self.current_path}")
    
    def _setup_window(self):
        self.root.title(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.root.geometry(f"{Config.DEFAULT_WINDOW_WIDTH}x{Config.DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(Config.MIN_WINDOW_WIDTH, Config.MIN_WINDOW_HEIGHT)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _setup_error_handling(self):
        def handle_exception(exc_type, exc_value, exc_traceback):
            if not self._is_closing:
                error_msg = f"Unhandled exception: {exc_type.__name__}: {exc_value}"
                Logger.log_error(error_msg)
                try:
                    InputDialog.show_error("Lỗi hệ thống", 
                                         f"Đã xảy ra lỗi không mong muốn:\n{exc_value}")
                except:
                    pass
        
        sys.excepthook = handle_exception
    
    def _create_widgets(self):
        try:
            self.path_entry = PathEntry(self.root, self._on_path_change)
            self.path_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            
            self.tree_view = FileTreeView(self.root, self._on_item_select, self._on_item_activate)
            self.tree_view.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
            
            # Updated actions dictionary - changed 'move' to use _move_items
            actions = {
                'create_folder': self._create_folder,
                'rename': self._rename_item,
                'delete': self._delete_items,
                'copy': self._copy_items,
                'move': self._move_items,  # Changed from _cut_items to _move_items
                'info': self._show_item_info,
                'toggle_hidden': self._toggle_hidden_files
            }
            
            self.action_buttons = ActionButtons(self.root, actions)
            self.action_buttons.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
            
            self.status_bar = StatusBar(self.root)
            self.status_bar.grid(row=3, column=0, sticky="ew")
            
        except Exception as e:
            Logger.log_error(f"Error creating widgets: {e}")
            raise
    
    def _setup_menu(self):
        try:
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)
            
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="Tạo thư mục mới", command=self._create_folder, accelerator="Ctrl+N")
            file_menu.add_command(label="Cửa sổ mới", command=self._open_new_window, accelerator="Ctrl+Shift+N")
            file_menu.add_separator()
            file_menu.add_command(label="Sao chép", command=self._copy_items, accelerator="Ctrl+C")
            file_menu.add_command(label="Cắt", command=self._cut_items, accelerator="Ctrl+X")
            file_menu.add_command(label="Dán", command=self._paste_items, accelerator="Ctrl+V")
            file_menu.add_separator()
            file_menu.add_command(label="Di chuyển", command=self._move_items, accelerator="Ctrl+M")
            file_menu.add_separator()
            file_menu.add_command(label="Xóa", command=self._delete_items, accelerator="Delete")
            file_menu.add_command(label="Đổi tên", command=self._rename_item, accelerator="F2")
            file_menu.add_separator()
            file_menu.add_command(label="Thoát", command=self._quit_app, accelerator="Ctrl+Q")
            
            view_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="View", menu=view_menu)
            view_menu.add_checkbutton(label="Hiển thị file ẩn", command=self._toggle_hidden_files)
            view_menu.add_command(label="Làm mới", command=self._refresh, accelerator="F5")
            
            # Removed help_menu - no longer showing Help menu
            
        except Exception as e:
            Logger.log_error(f"Error creating menu: {e}")
    
    def _open_new_window(self):
        try:
            new_window = tk.Toplevel(self.root)
            new_app = FileExplorerApp(new_window)
            Logger.log_info("Opened new window")
        except Exception as e:
            Logger.log_error(f"Error opening new window: {e}")
            self._show_error("Lỗi", f"Không thể mở cửa sổ mới: {str(e)}")
    
    def _setup_shortcuts(self):
        try:
            shortcuts = {
                "<Control-n>": lambda e: self._create_folder(),
                "<Control-c>": lambda e: self._copy_items(),
                "<Control-x>": lambda e: self._cut_items(),
                "<Control-v>": lambda e: self._paste_items(),
                "<Control-m>": lambda e: self._move_items(),
                "<Control-f>": lambda e: self._show_search_dialog(),  # Added search shortcut
                "<Control-Shift-n>": lambda e: self._open_new_window(),  # Added new window shortcut
                "<Delete>": lambda e: self._delete_items(),
                "<F2>": lambda e: self._rename_item(),
                "<F5>": lambda e: self._refresh(),
                "<Control-q>": lambda e: self._quit_app(),
                "<Alt-Left>": lambda e: self._go_back(),
                "<Alt-Right>": lambda e: self._go_forward()
            }
            
            for key, command in shortcuts.items():
                self.root.bind(key, command)
                
        except Exception as e:
            Logger.log_error(f"Error setting up shortcuts: {e}")
    
    def _show_search_dialog(self):
        try:
            from search_manager import SearchManager
            query = InputDialog.get_text("Tìm kiếm", "Nhập tên file cần tìm:")
            if query:
                self._perform_search(query)
        except Exception as e:
            Logger.log_error(f"Error showing search dialog: {e}")
            
    def _perform_search(self, query: str):
        try:
            from search_manager import SearchManager
            search_manager = SearchManager()
            
            results = []
            def on_result(file_item):
                results.append(file_item)
                
            def on_complete(count):
                self.tree_view.clear()
                for item in results:
                    icon = item.get_icon()
                    self.tree_view.add_item(item, icon)
                self.status_bar.set_status(f"Tìm thấy {count} kết quả cho '{query}'")
                
            search_manager.search_files(
                self.current_path, query, on_result, on_complete, 
                case_sensitive=False, search_content=False
            )
            
        except Exception as e:
            Logger.log_error(f"Error performing search: {e}")
            self._show_error("Lỗi", f"Không thể tìm kiếm: {str(e)}")
    
    def _on_path_change(self, path: str):
        try:
            if path == "UP":
                self._go_up()
            elif path == "DRIVES":
                self._show_drives_menu()
            elif path == "SEARCH":
                self._show_search_info()
            else:
                if os.path.exists(path):
                    self.navigate_to(path)
                else:
                    self._show_error("Lỗi đường dẫn", f"Đường dẫn không tồn tại: {path}")
                    self.path_entry.set_path(self.current_path)
        except Exception as e:
            Logger.log_error(f"Error in path change: {e}")
            self._show_error("Lỗi điều hướng", str(e))
            self.path_entry.set_path(self.current_path)
    
    def _show_drives_menu(self):
        try:
            drives_menu = tk.Menu(self.root, tearoff=0)
            
            if platform.system() == "Windows":
                for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                    drive_path = f"{letter}:\\"
                    if os.path.exists(drive_path):
                        drives_menu.add_command(
                            label=f"{letter}:\\", 
                            command=lambda path=drive_path: self.navigate_to(path)
                        )
            else:
                common_paths = [
                    ("/", "Root (/)"),
                    (str(Path.home()), "Home"),
                    ("/mnt", "Mounts"),
                    ("/media", "Media")
                ]
                
                for path, label in common_paths:
                    if os.path.exists(path):
                        drives_menu.add_command(
                            label=label,
                            command=lambda p=path: self.navigate_to(p)
                        )
            
            try:
                x = self.root.winfo_pointerx()
                y = self.root.winfo_pointery()
                drives_menu.tk_popup(x, y)
            except:
                drives_menu.tk_popup(self.root.winfo_x() + 50, self.root.winfo_y() + 50)
            finally:
                drives_menu.grab_release()
                
        except Exception as e:
            Logger.log_error(f"Error showing drives menu: {e}")
            self._show_error("Lỗi", f"Không thể hiển thị menu ổ đĩa: {str(e)}")
    
    def _show_search_info(self):
        try:
            guide_text = f"""
{Config.APP_NAME} - Trình quản lý tệp đơn giản
Phiên bản: {Config.APP_VERSION}
Phát triển bởi: HE186837 Lê Văn Hưng

=== HƯỚNG DẪN SỬ DỤNG ===

📁 ĐIỀU HƯỚNG:
• Nhấn đúp vào thư mục để mở
• Sử dụng nút "⬆ Lên" để lên thư mục cha
• Nút "💾 Drives" để chọn ổ đĩa
• Dropdown "📁 Recent Files" để truy cập nhanh thư mục gần đây
• Gõ đường dẫn trực tiếp vào thanh địa chỉ và nhấn Enter

📋 QUẢN LÝ TỆP:
• Tạo thư mục mới: Ctrl+N hoặc nút "📁 Tạo thư mục"
• Đổi tên: F2 hoặc nút "✏️ Đổi tên"
• Xóa: Delete hoặc nút "🗑️ Xóa"
• Sao chép: Ctrl+C hoặc nút "📋 Sao chép"
• Cắt: Ctrl+X
• Dán: Ctrl+V
• Di chuyển: Ctrl+M hoặc nút "📦 Di chuyển"

🔍 TÌM KIẾM:
• Ctrl+F để mở hộp thoại tìm kiếm
• Tìm theo tên file trong thư mục hiện tại và các thư mục con

📄 XEM FILE:
• Nhấn đúp file text để xem trước nội dung
• File không phải text sẽ hỏi xác nhận trước khi mở ứng dụng ngoài
• Enter cũng có thể dùng để mở file/thư mục

🪟 NHIỀU CỬA SỔ:
• Menu File > Cửa sổ mới (Ctrl+Shift+N) để mở cửa sổ file manager mới
• Dễ dàng so sánh và di chuyển file giữa các thư mục khác nhau

ℹ️ XEM THÔNG TIN:
• Nút "ℹ️ Thông tin" để xem chi tiết tệp/thư mục
• Nút "👁️ Ẩn/Hiện" để bật/tắt hiển thị tệp ẩn
• Cột "Kích thước" hiển thị dung lượng file và thống kê thư mục

🎯 CHỌN TỆP:
• Click để chọn một tệp
• Ctrl+Click để chọn nhiều tệp
• Shift+Click để chọn dãy tệp
• Nút "✅ Select All" để chọn tất cả
• Ctrl+A để chọn tất cả

🔄 LÀM MỚI:
• F5 để làm mới thư mục hiện tại
• Menu View > Làm mới

⚡ PHÍM TẮT KHÁC:
• Ctrl+Q: Thoát ứng dụng
• Ctrl+F: Tìm kiếm file
• Ctrl+Shift+N: Cửa sổ mới
• Alt+Left/Right: Điều hướng trước/sau (dự phòng)

💡 MẸO:
• Sử dụng Recent Files dropdown để truy cập nhanh
• File text có thể xem trước trước khi mở ứng dụng ngoài
• Thư mục hiển thị tổng dung lượng và số file bên trong
• Sử dụng phím tắt để làm việc hiệu quả
• Kiểm tra thanh trạng thái để biết thông tin chi tiết
• Tệp/thư mục bị xóa sẽ được chuyển vào thùng rác

🔒 BẢO MẬT:
• Ứng dụng ghi log hoạt động vào file 'file_explorer.log'
• Không có quyền truy cập sẽ hiển thị thông báo lỗi
• Dữ liệu được xử lý an toàn với encoding UTF-8
• Lịch sử Recent Files được lưu cục bộ

Cảm ơn bạn đã sử dụng Python File Explorer!
            """
            
            InputDialog.show_info("Hướng dẫn sử dụng", guide_text.strip())
        except Exception as e:
            Logger.log_error(f"Error showing guide: {e}")
    
    def _on_item_select(self, item_path: str):
        try:
            self.selected_items = self.tree_view.get_selected_items()
            
            if len(self.selected_items) == 1:
                item_info = self.file_ops.get_item_info(item_path)
                if item_info:
                    status_msg = f"Đã chọn: {item_info['name']}"
                    if not item_info['is_dir']:
                        status_msg += f" ({item_info['size']})"
                    self.status_bar.set_status(status_msg)
            elif len(self.selected_items) > 1:
                self.status_bar.set_status(f"Đã chọn {len(self.selected_items)} mục")
                
        except Exception as e:
            Logger.log_error(f"Error selecting item: {e}")
    
    def _on_item_activate(self, item_path: str):
        try:
            path_obj = Path(item_path)
            if path_obj.is_dir():
                self.navigate_to(item_path)
            else:
                self._handle_file_activation(item_path)
        except Exception as e:
            Logger.log_error(f"Error activating item: {e}")
            self._show_error("Lỗi", f"Không thể mở: {str(e)}")
    
    def _handle_file_activation(self, file_path: str):
        try:
            path_obj = Path(file_path)
            file_ext = path_obj.suffix.lower()
            
            # Check if it's a text file
            if Config.is_text_file(file_ext):
                if InputDialog.confirm("Xem trước file text", 
                                     f"File '{path_obj.name}' là file text.\nBạn muốn xem trước nội dung hay mở bằng ứng dụng ngoài?"):
                    self._show_text_preview(file_path)
                else:
                    self._open_file(file_path)
            else:
                # Non-text file - ask confirmation to open with external app
                if InputDialog.confirm("Mở file", 
                                     f"File '{path_obj.name}' chỉ có thể xem trước nếu là file text.\nTiếp tục mở bằng ứng dụng ngoài?"):
                    self._open_file(file_path)
        except Exception as e:
            Logger.log_error(f"Error handling file activation: {e}")
            self._show_error("Lỗi", f"Không thể xử lý file: {str(e)}")
    
    def _show_text_preview(self, file_path: str):
        try:
            # Create preview window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Xem trước - {Path(file_path).name}")
            preview_window.geometry("800x600")
            preview_window.transient(self.root)
            
            # Create text widget with scrollbar
            main_frame = ttk.Frame(preview_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Consolas", 10))
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Read and display file content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(50000)  # Limit to 50KB
                    text_widget.insert(tk.END, content)
                    if len(content) >= 50000:
                        text_widget.insert(tk.END, "\n\n... (File quá lớn, chỉ hiển thị 50KB đầu)")
            except Exception as e:
                text_widget.insert(tk.END, f"Không thể đọc file: {str(e)}")
            
            text_widget.config(state=tk.DISABLED)  # Make read-only
            
            # Add close button
            button_frame = ttk.Frame(preview_window)
            button_frame.pack(pady=5)
            ttk.Button(button_frame, text="Đóng", command=preview_window.destroy).pack()
            
            preview_window.focus_set()
            
        except Exception as e:
            Logger.log_error(f"Error showing text preview: {e}")
            self._show_error("Lỗi", f"Không thể xem trước: {str(e)}")
    
    def navigate_to(self, path: str):
        try:
            if not FileOperations.validate_path(path):
                raise InvalidPathError(f"Invalid path: {path}")
            
            items = self.file_ops.get_directory_contents(path, self.show_hidden)
            
            self.current_path = path
            self.path_entry.set_path(path)
            
            # Add to recent files
            try:
                from recent_manager import RecentManager
                recent_manager = RecentManager()
                recent_manager.add_recent_item(path, 'opened')
                # Update recent dropdown
                self.path_entry._populate_recent_files()
            except Exception as e:
                Logger.log_debug(f"Could not update recent files: {e}")
            
            self.tree_view.clear()
            
            for item in items:
                icon = item.get_icon()
                self.tree_view.add_item(item, icon)
            
            self.status_bar.set_item_count(len(items))
            self.status_bar.set_status(f"Đã tải {len(items)} mục từ {Path(path).name}")
            
            Logger.log_debug(f"Navigated to: {path} ({len(items)} items)")
            
        except PermissionDeniedError as e:
            self._show_error("Lỗi quyền truy cập", str(e))
            self.status_bar.set_status("Không có quyền truy cập", True)
        except (PathAccessError, InvalidPathError) as e:
            self._show_error("Lỗi đường dẫn", str(e))
            self.status_bar.set_status("Đường dẫn không hợp lệ", True)
        except Exception as e:
            Logger.log_error(f"Navigation error: {e}")
            self._show_error("Lỗi", f"Không thể truy cập thư mục: {str(e)}")
            self.status_bar.set_status("Lỗi tải thư mục", True)("Lỗi đường dẫn", str(e))
            self.status_bar.set_status("Đường dẫn không hợp lệ", True)
        except Exception as e:
            Logger.log_error(f"Navigation error: {e}")
            self._show_error("Lỗi", f"Không thể truy cập thư mục: {str(e)}")
            self.status_bar.set_status("Lỗi tải thư mục", True)("Lỗi đường dẫn", str(e))
            self.status_bar.set_status("Đường dẫn không hợp lệ", True)
        except Exception as e:
            Logger.log_error(f"Navigation error: {e}")
            self._show_error("Lỗi", f"Không thể truy cập thư mục: {str(e)}")
            self.status_bar.set_status("Lỗi tải thư mục", True)
    
    def _go_up(self):
        try:
            parent_path = str(Path(self.current_path).parent)
            if parent_path != self.current_path:
                self.navigate_to(parent_path)
        except Exception as e:
            Logger.log_error(f"Error going up: {e}")
    
    def _go_back(self):
        pass
    
    def _go_forward(self):
        pass
    
    def _refresh(self):
        try:
            self.navigate_to(self.current_path)
        except Exception as e:
            Logger.log_error(f"Error refreshing: {e}")
    
    def _create_folder(self):
        try:
            folder_name = InputDialog.get_text("Tạo thư mục", "Nhập tên thư mục mới:")
            if folder_name:
                safe_name = FileOperations.get_safe_filename(folder_name)
                if safe_name != folder_name:
                    if not InputDialog.confirm("Xác nhận", 
                                             f"Tên thư mục đã được điều chỉnh thành: '{safe_name}'\nTiếp tục?"):
                        return
                
                success, message = self.file_ops.create_folder(self.current_path, safe_name)
                if success:
                    self._refresh()
                    self.status_bar.set_status(message)
                else:
                    self._show_error("Lỗi", message)
                    self.status_bar.set_status(message, True)
        except Exception as e:
            Logger.log_error(f"Error creating folder: {e}")
            self._show_error("Lỗi", f"Không thể tạo thư mục: {str(e)}")
    
    def _rename_item(self):
        try:
            if not self.selected_items:
                InputDialog.show_warning("Cảnh báo", "Vui lòng chọn một mục để đổi tên.")
                return
            
            if len(self.selected_items) > 1:
                InputDialog.show_warning("Cảnh báo", "Chỉ có thể đổi tên một mục tại một thời điểm.")
                return
            
            item_path = self.selected_items[0]
            old_name = Path(item_path).name
            new_name = InputDialog.get_text("Đổi tên", f"Nhập tên mới cho '{old_name}':", old_name)
            
            if new_name and new_name != old_name:
                safe_name = FileOperations.get_safe_filename(new_name)
                if safe_name != new_name:
                    if not InputDialog.confirm("Xác nhận", 
                                             f"Tên đã được điều chỉnh thành: '{safe_name}'\nTiếp tục?"):
                        return
                
                success, message = self.file_ops.rename_item(item_path, safe_name)
                if success:
                    self._refresh()
                    self.status_bar.set_status(message)
                else:
                    self._show_error("Lỗi", message)
                    self.status_bar.set_status(message, True)
        except Exception as e:
            Logger.log_error(f"Error renaming item: {e}")
            self._show_error("Lỗi", f"Không thể đổi tên: {str(e)}")
    
    def _delete_items(self):
        try:
            if not self.selected_items:
                InputDialog.show_warning("Cảnh báo", "Vui lòng chọn mục để xóa.")
                return
            
            if len(self.selected_items) == 1:
                item_name = Path(self.selected_items[0]).name
                message = f"Bạn có chắc muốn chuyển '{item_name}' vào thùng rác?"
            else:
                message = f"Bạn có chắc muốn chuyển {len(self.selected_items)} mục vào thùng rác?"
            
            if InputDialog.confirm("Xác nhận xóa", message):
                success_count = 0
                errors = []
                
                for item_path in self.selected_items:
                    success, msg = self.file_ops.send_to_trash(item_path)
                    if success:
                        success_count += 1
                    else:
                        errors.append(f"{Path(item_path).name}: {msg}")
                
                self._refresh()
                
                if success_count == len(self.selected_items):
                    self.status_bar.set_status(f"Đã xóa {success_count} mục")
                else:
                    self.status_bar.set_status(f"Đã xóa {success_count}/{len(self.selected_items)} mục", True)
                    if errors:
                        error_details = "\n".join(errors[:5])
                        if len(errors) > 5:
                            error_details += f"\n... và {len(errors)-5} lỗi khác"
                        self._show_error("Một số mục không thể xóa", error_details)
                        
        except Exception as e:
            Logger.log_error(f"Error deleting items: {e}")
            self._show_error("Lỗi", f"Không thể xóa: {str(e)}")
    
    def _copy_items(self):
        try:
            if not self.selected_items:
                InputDialog.show_warning("Cảnh báo", "Vui lòng chọn mục để sao chép.")
                return
            
            self.clipboard_items = self.selected_items.copy()
            self.clipboard_action = "copy"
            
            if len(self.clipboard_items) == 1:
                item_name = Path(self.clipboard_items[0]).name
                self.status_bar.set_status(f"Đã sao chép '{item_name}' vào clipboard")
            else:
                self.status_bar.set_status(f"Đã sao chép {len(self.clipboard_items)} mục vào clipboard")
                
        except Exception as e:
            Logger.log_error(f"Error copying items: {e}")
            self._show_error("Lỗi", f"Không thể sao chép: {str(e)}")
    
    def _cut_items(self):
        """Cut selected items to clipboard for paste operation"""
        try:
            if not self.selected_items:
                InputDialog.show_warning("Cảnh báo", "Vui lòng chọn mục để cắt.")
                return
            
            self.clipboard_items = self.selected_items.copy()
            self.clipboard_action = "cut"
            
            if len(self.clipboard_items) == 1:
                item_name = Path(self.clipboard_items[0]).name
                self.status_bar.set_status(f"Đã cắt '{item_name}' vào clipboard")
            else:
                self.status_bar.set_status(f"Đã cắt {len(self.clipboard_items)} mục vào clipboard")
                
        except Exception as e:
            Logger.log_error(f"Error cutting items: {e}")
            self._show_error("Lỗi", f"Không thể cắt: {str(e)}")
    
    def _move_items(self):
        """Move selected items to a destination path with dialog input"""
        try:
            if not self.selected_items:
                InputDialog.show_warning("Cảnh báo", "Vui lòng chọn mục để di chuyển.")
                return
            
            # Show dialog to input destination path
            if len(self.selected_items) == 1:
                item_name = Path(self.selected_items[0]).name
                message = f"Nhập đường dẫn đích để di chuyển '{item_name}':"
            else:
                message = f"Nhập đường dẫn đích để di chuyển {len(self.selected_items)} mục:"
            
            destination = InputDialog.get_text("Di chuyển", message, self.current_path)
            
            if not destination:
                return
            
            # Validate destination path
            if not os.path.exists(destination):
                self._show_error("Lỗi", f"Đường dẫn đích không tồn tại: {destination}")
                return
            
            if not os.path.isdir(destination):
                self._show_error("Lỗi", "Đường dẫn đích phải là thư mục")
                return
            
            # Check if trying to move to same directory
            if os.path.abspath(destination) == os.path.abspath(self.current_path):
                InputDialog.show_warning("Cảnh báo", "Không thể di chuyển mục trong cùng thư mục.")
                return
            
            success_count = 0
            errors = []
            
            for source_path in self.selected_items:
                source_name = Path(source_path).name
                destination_path = Path(destination) / source_name
                
                # Handle name conflicts by adding suffix
                counter = 1
                original_dest = destination_path
                while destination_path.exists():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    destination_path = original_dest.parent / f"{stem}_moved_{counter}{suffix}"
                    counter += 1
                
                # Check if trying to move a folder into itself or its subfolder
                if Path(source_path).is_dir():
                    try:
                        # Check if destination is inside source
                        Path(destination).relative_to(source_path)
                        errors.append(f"{source_name}: Không thể di chuyển thư mục vào chính nó")
                        continue
                    except ValueError:
                        # This is expected - destination is not inside source
                        pass
                
                success, message = self.file_ops.move_item(source_path, str(destination_path))
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{source_name}: {message}")
            
            self._refresh()
            
            if success_count == len(self.selected_items):
                dest_name = Path(destination).name if Path(destination).name else destination
                self.status_bar.set_status(f"Đã di chuyển {success_count} mục đến '{dest_name}'")
            else:
                self.status_bar.set_status(f"Đã di chuyển {success_count}/{len(self.selected_items)} mục", True)
                if errors:
                    error_details = "\n".join(errors[:3])
                    if len(errors) > 3:
                        error_details += f"\n... và {len(errors)-3} lỗi khác"
                    self._show_error("Một số mục không thể di chuyển", error_details)
                    
        except Exception as e:
            Logger.log_error(f"Error moving items: {e}")
            self._show_error("Lỗi", f"Không thể di chuyển: {str(e)}")
    
    def _paste_items(self):
        try:
            if not self.clipboard_items or not self.clipboard_action:
                InputDialog.show_warning("Cảnh báo", "Clipboard trống.")
                return
            
            success_count = 0
            errors = []
            
            for source_path in self.clipboard_items:
                source_name = Path(source_path).name
                destination_path = Path(self.current_path) / source_name
                
                counter = 1
                original_dest = destination_path
                while destination_path.exists():
                    stem = original_dest.stem
                    suffix = original_dest.suffix
                    destination_path = original_dest.parent / f"{stem}_copy_{counter}{suffix}"
                    counter += 1
                
                if self.clipboard_action == "copy":
                    success, message = self.file_ops.copy_item(source_path, str(destination_path))
                else:
                    success, message = self.file_ops.move_item(source_path, str(destination_path))
                
                if success:
                    success_count += 1
                else:
                    errors.append(f"{source_name}: {message}")
            
            if self.clipboard_action == "cut" and success_count > 0:
                self.clipboard_items = []
                self.clipboard_action = None
            
            self._refresh()
            
            if success_count == len(self.clipboard_items):
                action = "sao chép" if self.clipboard_action == "copy" else "di chuyển"
                self.status_bar.set_status(f"Đã {action} {success_count} mục")
            else:
                self.status_bar.set_status(f"Thành công {success_count}/{len(self.clipboard_items)} mục", True)
                if errors:
                    error_details = "\n".join(errors[:3])
                    if len(errors) > 3:
                        error_details += f"\n... và {len(errors)-3} lỗi khác"
                    self._show_error("Một số mục không thể dán", error_details)
                    
        except Exception as e:
            Logger.log_error(f"Error pasting items: {e}")
            self._show_error("Lỗi", f"Không thể dán: {str(e)}")
    
    def _show_item_info(self):
        try:
            if not self.selected_items:
                InputDialog.show_warning("Cảnh báo", "Vui lòng chọn một mục để xem thông tin.")
                return
            
            if len(self.selected_items) > 1:
                InputDialog.show_warning("Cảnh báo", "Chỉ có thể xem thông tin một mục tại một thời điểm.")
                return
            
            item_info = self.file_ops.get_item_info(self.selected_items[0])
            if item_info:
                InfoDialog.show_item_info(self.root, item_info)
            else:
                self._show_error("Lỗi", "Không thể lấy thông tin mục.")
                
        except Exception as e:
            Logger.log_error(f"Error showing item info: {e}")
            self._show_error("Lỗi", f"Không thể hiển thị thông tin: {str(e)}")
    
    def _toggle_hidden_files(self):
        try:
            self.show_hidden = not self.show_hidden
            self._refresh()
            status = "hiển thị" if self.show_hidden else "ẩn"
            self.status_bar.set_status(f"Tệp ẩn: {status}")
        except Exception as e:
            Logger.log_error(f"Error toggling hidden files: {e}")
    
    def _open_file(self, file_path: str):
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
            
            self.status_bar.set_status(f"Đã mở: {Path(file_path).name}")
            
        except Exception as e:
            Logger.log_error(f"Error opening file {file_path}: {e}")
            self._show_error("Lỗi", f"Không thể mở tệp: {str(e)}")
    
    def _show_error(self, title: str, message: str):
        try:
            Logger.log_error(f"{title}: {message}")
            InputDialog.show_error(title, message)
        except Exception:
            print(f"Critical error - {title}: {message}")
    
    def _on_window_close(self):
        try:
            self._is_closing = True
            Logger.log_info("File Explorer shutting down")
            self.root.destroy()
        except Exception as e:
            Logger.log_error(f"Error during shutdown: {e}")
            self.root.quit()
    
    def _quit_app(self):
        try:
            self._on_window_close()
        except Exception as e:
            Logger.log_error(f"Error quitting app: {e}")
            sys.exit(1)