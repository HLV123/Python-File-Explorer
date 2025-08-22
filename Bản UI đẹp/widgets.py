import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from typing import Callable, Optional, Any, List, Dict
from pathlib import Path
from datetime import datetime
from config import Config


class PathEntry(ttk.Frame):
    def __init__(self, parent, on_path_change: Callable[[str], None]):
        super().__init__(parent)
        self.on_path_change = on_path_change
        self._create_widgets()
    
    def _create_widgets(self):
        # Style improvements
        style = ttk.Style()
        style.configure("PathEntry.TButton", padding=(10, 5))
        
        self.up_button = ttk.Button(self, text="⬆️ Lên", command=self._on_up_click, 
                                   style="PathEntry.TButton")
        self.up_button.pack(side=tk.LEFT, padx=(0, 8))
        
        self.drives_button = ttk.Button(self, text="💾 Drives", command=self._on_drives_click,
                                       style="PathEntry.TButton")
        self.drives_button.pack(side=tk.LEFT, padx=(0, 8))
        
        # Enhanced Recent Files dropdown with better styling
        self.recent_var = tk.StringVar()
        self.recent_dropdown = ttk.Combobox(self, textvariable=self.recent_var, 
                                           width=35, state="readonly", font=("Segoe UI", 9))
        self.recent_dropdown.pack(side=tk.LEFT, padx=(0, 8))
        self.recent_dropdown.bind("<<ComboboxSelected>>", self._on_recent_select)
        self._populate_recent_files()
        
        # Enhanced path entry with better font
        self.path_entry = ttk.Entry(self, font=("Segoe UI", 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.path_entry.bind("<Return>", self._on_enter)
        
        # Professional guide button
        self.search_button = ttk.Button(self, text="📖 Hướng dẫn", command=self._on_search,
                                       style="PathEntry.TButton")
        self.search_button.pack(side=tk.LEFT)
    
    def _populate_recent_files(self):
        try:
            from recent_manager import RecentManager
            recent_manager = RecentManager()
            recent_items = recent_manager.get_recent_items(10)
            
            recent_paths = ["📁 Recent Files..."]
            for item in recent_items:
                icon = "📁" if item['is_dir'] else "📄"
                display_name = f"{icon} {item['name']}"
                if len(display_name) > 40:
                    display_name = display_name[:37] + "..."
                recent_paths.append(display_name)
                
            self.recent_dropdown['values'] = recent_paths
            if recent_paths:
                self.recent_dropdown.set(recent_paths[0])
                
        except Exception as e:
            self.recent_dropdown['values'] = ["📁 Recent Files..."]
            self.recent_dropdown.set("📁 Recent Files...")
    
    def _on_recent_select(self, event):
        try:
            selected = self.recent_dropdown.get()
            if selected != "📁 Recent Files...":
                from recent_manager import RecentManager
                recent_manager = RecentManager()
                recent_items = recent_manager.get_recent_items(10)
                
                index = self.recent_dropdown.current() - 1
                if 0 <= index < len(recent_items):
                    path = recent_items[index]['path']
                    self.on_path_change(path)
                    
        except Exception as e:
            pass
    
    def _on_up_click(self):
        self.on_path_change("UP")
    
    def _on_drives_click(self):
        self.on_path_change("DRIVES")
    
    def _on_search(self):
        self.on_path_change("SEARCH")
    
    def _on_enter(self, event):
        path = self.get_path()
        if path:
            self.on_path_change(path)
    
    def set_path(self, path: str):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)
    
    def get_path(self) -> str:
        return self.path_entry.get().strip()


class FileTreeView(ttk.Frame):
    def __init__(self, parent, on_item_select: Callable[[str], None], 
                 on_item_activate: Callable[[str], None]):
        super().__init__(parent)
        self.on_item_select = on_item_select
        self.on_item_activate = on_item_activate
        self.selected_items = set()
        self._create_widgets()
    
    def _create_widgets(self):
        # Professional controls frame
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        
        # Enhanced select all button
        style = ttk.Style()
        style.configure("Select.TButton", padding=(8, 4))
        
        self.select_all_button = ttk.Button(controls_frame, text="✅ Chọn tất cả", 
                                           command=self._select_all, style="Select.TButton")
        self.select_all_button.pack(side=tk.LEFT)
        
        # Professional treeview with enhanced styling
        columns = ("size", "modified", "type")
        self.tree = ttk.Treeview(self, columns=columns, selectmode="extended", height=20)
        
        # Enhanced column headers
        self.tree.heading("#0", text="📄 Tên", anchor=tk.W)
        self.tree.heading("size", text="📏 Kích thước", anchor=tk.E)
        self.tree.heading("modified", text="📅 Ngày sửa đổi", anchor=tk.W)
        self.tree.heading("type", text="🏷️ Loại", anchor=tk.W)
        
        # Better column widths and styling
        self.tree.column("#0", width=350, minwidth=200)
        self.tree.column("size", width=120, minwidth=100, anchor=tk.E)
        self.tree.column("modified", width=180, minwidth=150)
        self.tree.column("type", width=100, minwidth=80)
        
        # Professional scrollbars
        scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Enhanced grid layout
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(0, 2))
        scrollbar_y.grid(row=1, column=1, sticky="ns")
        scrollbar_x.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Enhanced event bindings
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_return)
        self.tree.bind("<Control-a>", lambda e: self._select_all())
        
        self._configure_tags()
    
    def _select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)
        self.selected_items = set(self.tree.get_children())
    
    def get_selected_items(self) -> List[str]:
        return list(self.tree.selection())
    
    def _configure_tags(self):
        # Enhanced tag styling
        self.tree.tag_configure("folder", foreground="#0066cc", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("file", foreground="#333333", font=("Segoe UI", 9))
        self.tree.tag_configure("hidden", foreground="#888888", font=("Segoe UI", 9, "italic"))
    
    def _on_select(self, event):
        self.selected_items = set(self.tree.selection())
        selected = self.get_selected_item()
        if selected:
            self.on_item_select(selected)
    
    def _on_double_click(self, event):
        selected = self.get_selected_item()
        if selected:
            self.on_item_activate(selected)
    
    def _on_return(self, event):
        selected = self.get_selected_item()
        if selected:
            self.on_item_activate(selected)
    
    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected_items.clear()
    
    def add_item(self, file_item, icon=""):
        tags = []
        if file_item.is_dir:
            tags.append("folder")
            try:
                from file_operations import FileOperations
                total_size, file_count = FileOperations.get_folder_size(file_item.full_path)
                if total_size > 0:
                    folder_size = self._format_size(total_size)
                    size_display = f"{folder_size} ({file_count} files)"
                else:
                    size_display = "Empty"
            except:
                size_display = ""
        else:
            tags.append("file")
            size_display = file_item.size_formatted
        
        if file_item.is_hidden:
            tags.append("hidden")
        
        display_name = f"{icon} {file_item.name}" if icon else file_item.name
        
        try:
            self.tree.insert("", tk.END, 
                            text=display_name,
                            values=(size_display, 
                                   file_item.modified_formatted,
                                   file_item.category),
                            tags=tags,
                            iid=file_item.full_path)
        except tk.TclError as e:
            safe_name = self._sanitize_display_name(display_name)
            self.tree.insert("", tk.END, 
                            text=safe_name,
                            values=(size_display, 
                                   file_item.modified_formatted,
                                   file_item.category),
                            tags=tags,
                            iid=file_item.full_path)
    
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}" if size_bytes != int(size_bytes) else f"{int(size_bytes)} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _sanitize_display_name(self, name: str) -> str:
        try:
            return name.encode('utf-8', errors='replace').decode('utf-8')
        except:
            return ''.join(char if ord(char) < 127 else '?' for char in name)
    
    def get_selected_item(self) -> Optional[str]:
        selection = self.tree.selection()
        return selection[0] if selection else None
    
    def focus_item(self, item_id: str):
        if self.tree.exists(item_id):
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)
            self.tree.see(item_id)


class ActionButtons(ttk.Frame):
    def __init__(self, parent, actions: dict):
        super().__init__(parent)
        self.actions = actions
        self._create_widgets()
    
    def _create_widgets(self):
        # Professional button styling
        style = ttk.Style()
        style.configure("Action.TButton", padding=(12, 6), font=("Segoe UI", 9))
        
        buttons_config = [
            ("📁 Tạo thư mục", "create_folder", "#4CAF50"),
            ("✏️ Đổi tên", "rename", "#2196F3"),
            ("🗑️ Xóa", "delete", "#F44336"),
            ("📋 Sao chép", "copy", "#FF9800"),
            ("📦 Di chuyển", "move", "#9C27B0"),
            ("ℹ️ Thông tin", "info", "#607D8B"),
            ("👁️ Ẩn/Hiện", "toggle_hidden", "#795548")
        ]
        
        for i, (text, action, color) in enumerate(buttons_config):
            if action in self.actions:
                btn = ttk.Button(self, text=text, command=self.actions[action],
                               style="Action.TButton")
                btn.grid(row=0, column=i, padx=3, pady=2, sticky="ew")
                self.grid_columnconfigure(i, weight=1)


class StatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
    
    def _create_widgets(self):
        # Professional status bar styling
        style = ttk.Style()
        style.configure("Status.TLabel", font=("Segoe UI", 9), padding=(5, 3))
        
        self.status_label = ttk.Label(self, text="🟢 Sẵn sàng", relief=tk.SUNKEN, 
                                     anchor=tk.W, style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 5))
        
        self.item_count_label = ttk.Label(self, text="", relief=tk.SUNKEN, 
                                         anchor=tk.E, style="Status.TLabel")
        self.item_count_label.pack(side=tk.RIGHT, padx=(5, 2))
    
    def set_status(self, message: str, is_error: bool = False):
        icon = "🔴" if is_error else "🟢"
        self.status_label.config(text=f"{icon} {message}")
    
    def set_item_count(self, count: int, total: int = None):
        if total:
            text = f"📊 {count}/{total} mục"
        else:
            text = f"📊 {count} mục"
        self.item_count_label.config(text=text)
    
    def clear(self):
        self.status_label.config(text="🟢 Sẵn sàng")
        self.item_count_label.config(text="")


class GuideWindow:
    """Professional Guide/Help Window with beautiful UI"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        
    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_set()
            return
            
        self._create_window()
        
    def _create_window(self):
        # Create main window
        self.window = tk.Toplevel(self.parent)
        self.window.title("📖 Hướng dẫn sử dụng Python File Explorer")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the window
        self._center_window()
        
        # Configure styles
        self._configure_styles()
        
        # Create header
        self._create_header()
        
        # Create main content
        self._create_content()
        
        # Create footer
        self._create_footer()
        
        # Set focus
        self.window.focus_set()
        
    def _center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"1000x700+{x}+{y}")
        
    def _configure_styles(self):
        style = ttk.Style()
        
        # Header style
        style.configure("Header.TLabel", 
                       font=("Segoe UI", 16, "bold"),
                       foreground="#2c3e50",
                       background="#ecf0f1")
        
        # Subheader style
        style.configure("Subheader.TLabel", 
                       font=("Segoe UI", 12, "bold"),
                       foreground="#34495e",
                       background="#ffffff")
        
        # Content style
        style.configure("Content.TLabel", 
                       font=("Segoe UI", 10),
                       foreground="#2c3e50",
                       background="#ffffff")
        
        # Section style
        style.configure("Section.TFrame", 
                       background="#ffffff",
                       relief="solid",
                       borderwidth=1)
        
    def _create_header(self):
        # Header frame with gradient-like background
        header_frame = tk.Frame(self.window, bg="#3498db", height=80)
        header_frame.pack(fill=tk.X, pady=(0, 0))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, 
                              text="HƯỚNG DẪN SỬ DỤNG",
                              font=("Segoe UI", 18, "bold"),
                              fg="white", bg="#3498db")
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="SOFTWARE WROTE BY LÊ VĂN HƯNG HE186837 FPT Uni HOLA CAMPUS",
                                 font=("Segoe UI", 11),
                                 fg="#ecf0f1", bg="#3498db")
        subtitle_label.pack()
        
    def _create_content(self):
        # Main content frame with scrollbar
        content_frame = tk.Frame(self.window, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(content_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content sections
        self._add_content_sections(scrollable_frame)
        
        # Bind mousewheel to canvas - FIXED: Only when mouse is over the canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        
    def _add_content_sections(self, parent):
        sections = [
            {
                "title": "🚀 Bắt đầu nhanh",
                "icon": "🚀",
                "color": "#e74c3c",
                "content": [
                    "• Nhấn đúp vào thư mục để mở",
                    "• Sử dụng nút '⬆️ Lên' để lên thư mục cha", 
                    "• Nút '💾 Drives' để chọn ổ đĩa",
                    "• Dropdown 'Recent Files' để truy cập nhanh",
                    "• Gõ đường dẫn trực tiếp và nhấn Enter"
                ]
            },
            {
                "title": "📋 Quản lý tệp",
                "icon": "📋", 
                "color": "#2ecc71",
                "content": [
                    "• Tạo thư mục mới: Ctrl+N hoặc nút '📁 Tạo thư mục'",
                    "• Đổi tên: F2 hoặc nút '✏️ Đổi tên'",
                    "• Xóa: Delete hoặc nút '🗑️ Xóa'",
                    "• Sao chép: Ctrl+C hoặc nút '📋 Sao chép'",
                    "• Cắt: Ctrl+X",
                    "• Dán: Ctrl+V", 
                    "• Di chuyển: Ctrl+M hoặc nút '📦 Di chuyển'"
                ]
            },
            {
                "title": "🔍 Tìm kiếm",
                "icon": "🔍",
                "color": "#f39c12", 
                "content": [
                    "• Ctrl+F để mở hộp thoại tìm kiếm",
                    "• Tìm theo tên file trong thư mục hiện tại và các thư mục con",
                    "• Hỗ trợ tìm kiếm không phân biệt hoa thường",
                    "• Kết quả hiển thị ngay lập tức"
                ]
            },
            {
                "title": "📄 Xem file", 
                "icon": "📄",
                "color": "#9b59b6",
                "content": [
                    "• Nhấn đúp file text để xem trước nội dung",
                    "• File không phải text sẽ hỏi xác nhận trước khi mở",
                    "• Enter cũng có thể dùng để mở file/thư mục",
                    "• Xem trước an toàn với giới hạn 50KB"
                ]
            },
            {
                "title": "🪟 Nhiều cửa sổ",
                "icon": "🪟", 
                "color": "#1abc9c",
                "content": [
                    "• Menu File > Cửa sổ mới (Ctrl+Shift+N)",
                    "• Dễ dàng so sánh và di chuyển file giữa các thư mục",
                    "• Mỗi cửa sổ hoạt động độc lập"
                ]
            },
            {
                "title": "⚡ Phím tắt",
                "icon": "⚡",
                "color": "#e67e22", 
                "content": [
                    "• Ctrl+Q: Thoát ứng dụng",
                    "• Ctrl+F: Tìm kiếm file", 
                    "• Ctrl+Shift+N: Cửa sổ mới",
                    "• F5: Làm mới",
                    "• Ctrl+A: Chọn tất cả",
                    "• Alt+Left/Right: Điều hướng (dự phòng)"
                ]
            },
            {
                "title": "💡 Mẹo hay",
                "icon": "💡",
                "color": "#34495e",
                "content": [
                    "• Sử dụng Recent Files dropdown để truy cập nhanh",
                    "• Thư mục hiển thị tổng dung lượng và số file bên trong", 
                    "• Sử dụng phím tắt để làm việc hiệu quả",
                    "• Kiểm tra thanh trạng thái để biết thông tin chi tiết",
                    "• Tệp/thư mục bị xóa sẽ được chuyển vào thùng rác",
                    "• Ứng dụng ghi log hoạt động vào file 'file_explorer.log'"
                ]
            }
        ]
        
        for i, section in enumerate(sections):
            self._create_section(parent, section, i)
            
    def _create_section(self, parent, section_data, index):
        # Main container for centering
        container_frame = tk.Frame(parent, bg="white")
        container_frame.pack(fill=tk.X, pady=10)
        
        # Section frame - centered
        section_frame = tk.Frame(container_frame, bg="white", relief="solid", bd=1)
        section_frame.pack(pady=0, padx=50)  # Add horizontal padding to center content
        
        # Section header
        header_frame = tk.Frame(section_frame, bg=section_data["color"], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text=f"{section_data['icon']} {section_data['title']}",
                               font=("Segoe UI", 12, "bold"),
                               fg="white", bg=section_data["color"])
        header_label.pack(pady=8)
        
        # Section content
        content_frame = tk.Frame(section_frame, bg="white")
        content_frame.pack(fill=tk.X, padx=15, pady=10)
        
        for item in section_data["content"]:
            item_label = tk.Label(content_frame, text=item,
                                 font=("Segoe UI", 10), fg="#2c3e50", bg="white",
                                 anchor="w", justify="left")
            item_label.pack(fill=tk.X, pady=2)
            
    def _create_footer(self):
        # Footer frame
        footer_frame = tk.Frame(self.window, bg="#34495e", height=60)
        footer_frame.pack(fill=tk.X)
        footer_frame.pack_propagate(False)
        
        # Footer content
        footer_content = tk.Frame(footer_frame, bg="#34495e")
        footer_content.pack(expand=True)
        
        # Close button
        close_btn = tk.Button(footer_content, text="✅ Đóng",
                             font=("Segoe UI", 11, "bold"),
                             bg="#3498db", fg="white",
                             relief="flat", padx=30, pady=8,
                             command=self.window.destroy)
        close_btn.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Copyright info
        copyright_label = tk.Label(footer_content,
                                  text="© 2024 File Explorer | Developed by LÊ VĂN HƯNG HE186837 FPT Uni HOLA CAMPUS",
                                  font=("Segoe UI", 9),
                                  fg="#bdc3c7", bg="#34495e")
        copyright_label.pack(side=tk.RIGHT, padx=20, pady=15)


class InputDialog:
    @staticmethod
    def get_text(title: str, prompt: str, initial_value: str = "") -> Optional[str]:
        try:
            result = simpledialog.askstring(title, prompt, initialvalue=initial_value)
            return result.strip() if result and result.strip() else None
        except Exception:
            return None
    
    @staticmethod
    def confirm(title: str, message: str) -> bool:
        try:
            return messagebox.askyesno(title, message)
        except Exception:
            return False
    
    @staticmethod
    def show_info(title: str, message: str):
        try:
            messagebox.showinfo(title, message)
        except Exception:
            pass
    
    @staticmethod
    def show_warning(title: str, message: str):
        try:
            messagebox.showwarning(title, message)
        except Exception:
            pass
    
    @staticmethod
    def show_error(title: str, message: str):
        try:
            messagebox.showerror(title, message)
        except Exception:
            pass


class InfoDialog:
    @staticmethod
    def show_item_info(parent, item_info: dict):
        try:
            dialog = tk.Toplevel(parent)
            dialog.title("ℹ️ Thông tin chi tiết")
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.transient(parent)
            dialog.grab_set()
            
            # Professional styling
            dialog.configure(bg="#f8f9fa")
            
            # Header
            header_frame = tk.Frame(dialog, bg="#007bff", height=60)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            header_label = tk.Label(header_frame, 
                                   text="ℹ️ Thông tin chi tiết",
                                   font=("Segoe UI", 14, "bold"),
                                   fg="white", bg="#007bff")
            header_label.pack(pady=15)
            
            # Content frame
            main_frame = tk.Frame(dialog, bg="#f8f9fa")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            info_items = [
                ("📄 Tên:", item_info.get('name', '')),
                ("📁 Đường dẫn:", item_info.get('path', '')),
                ("🏷️ Loại:", "Thư mục" if item_info.get('is_dir') else "Tệp"),
                ("📏 Kích thước:", item_info.get('size', '')),
                ("📅 Ngày sửa đổi:", item_info.get('modified', '')),
                ("🔧 Phần mở rộng:", item_info.get('extension', 'Không có')),
                ("📂 Danh mục:", item_info.get('category', '')),
                ("👁️ Ẩn:", "Có" if item_info.get('is_hidden') else "Không")
            ]
            
            for i, (label, value) in enumerate(info_items):
                # Create row frame
                row_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
                row_frame.pack(fill=tk.X, pady=3)
                
                # Label
                label_frame = tk.Frame(row_frame, bg="#e9ecef", width=150)
                label_frame.pack(side=tk.LEFT, fill=tk.Y)
                label_frame.pack_propagate(False)
                
                ttk.Label(label_frame, text=label, 
                         font=("Segoe UI", 10, "bold"),
                         background="#e9ecef").pack(pady=8, padx=10, anchor="w")
                
                # Value
                value_frame = tk.Frame(row_frame, bg="white")
                value_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                if label == "📁 Đường dẫn:":
                    value_label = tk.Label(value_frame, text=str(value), 
                                         font=("Segoe UI", 9),
                                         bg="white", fg="#495057",
                                         wraplength=280, justify="left")
                else:
                    value_label = tk.Label(value_frame, text=str(value),
                                         font=("Segoe UI", 10), 
                                         bg="white", fg="#495057")
                
                value_label.pack(pady=8, padx=10, anchor="w")
            
            # Footer with close button
            footer_frame = tk.Frame(dialog, bg="#f8f9fa")
            footer_frame.pack(fill=tk.X, pady=10)
            
            close_btn = tk.Button(footer_frame, text="✅ Đóng",
                                 font=("Segoe UI", 11, "bold"),
                                 bg="#28a745", fg="white",
                                 relief="flat", padx=25, pady=8,
                                 command=dialog.destroy)
            close_btn.pack()
            
            # Center dialog
            dialog.update_idletasks()
            x = parent.winfo_rootx() + parent.winfo_width() // 2 - 250
            y = parent.winfo_rooty() + parent.winfo_height() // 2 - 200
            dialog.geometry(f"500x400+{x}+{y}")
            
            dialog.focus_set()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể hiển thị thông tin: {e}")


class SearchDialog:
    @staticmethod
    def show_search_dialog(parent) -> Optional[Dict]:
        return {"cancelled": True}


class TabManager(ttk.Notebook):
    def __init__(self, parent, on_tab_change: Callable[[str], None]):
        super().__init__(parent)
        self.on_tab_change = on_tab_change
    
    def add_tab(self, path: str, title: str = None) -> str:
        return "tab_1"
    
    def close_tab(self, tab_id: str = None):
        pass


class PreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_file = None
        self._create_widgets()
    
    def _create_widgets(self):
        self.title_label = ttk.Label(self, text="👁️ Xem trước", 
                                    font=("Segoe UI", 12, "bold"))
        self.title_label.pack(anchor="w", padx=5, pady=5)
    
    def preview_file(self, file_path: str):
        pass
    
    def clear_preview(self):
        pass