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
        self.up_button = ttk.Button(self, text="⬆ Lên", command=self._on_up_click)
        self.up_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.drives_button = ttk.Button(self, text="💾 Drives", command=self._on_drives_click)
        self.drives_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add Recent Files dropdown
        self.recent_var = tk.StringVar()
        self.recent_dropdown = ttk.Combobox(self, textvariable=self.recent_var, 
                                           width=30, state="readonly")
        self.recent_dropdown.pack(side=tk.LEFT, padx=(0, 5))
        self.recent_dropdown.bind("<<ComboboxSelected>>", self._on_recent_select)
        self._populate_recent_files()
        
        self.path_entry = ttk.Entry(self)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.path_entry.bind("<Return>", self._on_enter)
        
        # Removed refresh button
        
        self.search_button = ttk.Button(self, text="Hướng dẫn", command=self._on_search)
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
                if len(display_name) > 35:
                    display_name = display_name[:32] + "..."
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
                
                # Find the corresponding path
                index = self.recent_dropdown.current() - 1  # -1 because first item is header
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
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        self.select_all_button = ttk.Button(controls_frame, text="✅ Select All", 
                                           command=self._select_all)
        self.select_all_button.pack(side=tk.LEFT)
        
        columns = ("size", "modified", "type")
        self.tree = ttk.Treeview(self, columns=columns, selectmode="extended")
        
        self.tree.heading("#0", text="Tên", anchor=tk.W)
        self.tree.heading("size", text="Kích thước", anchor=tk.E)
        self.tree.heading("modified", text="Ngày sửa đổi", anchor=tk.W)
        self.tree.heading("type", text="Loại", anchor=tk.W)
        
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("size", width=100, minwidth=80, anchor=tk.E)
        self.tree.column("modified", width=150, minwidth=120)
        self.tree.column("type", width=80, minwidth=60)
        
        scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar_y.grid(row=1, column=1, sticky="ns")
        scrollbar_x.grid(row=2, column=0, sticky="ew")
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
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
        self.tree.tag_configure("folder", foreground=Config.THEME_COLORS['folder'])
        self.tree.tag_configure("file", foreground=Config.THEME_COLORS['file'])
        self.tree.tag_configure("hidden", foreground="gray")
    
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
            # Calculate folder size for display
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
        buttons_config = [
            ("📁 Tạo thư mục", "create_folder"),
            ("✏️ Đổi tên", "rename"),
            ("🗑️ Xóa", "delete"),
            ("📋 Sao chép", "copy"),
            ("📦 Di chuyển", "move"),
            ("ℹ️ Thông tin", "info"),
            ("👁️ Ẩn/Hiện", "toggle_hidden")
        ]
        
        for i, (text, action) in enumerate(buttons_config):
            if action in self.actions:
                btn = ttk.Button(self, text=text, command=self.actions[action])
                btn.grid(row=0, column=i, padx=2, sticky="ew")
                self.grid_columnconfigure(i, weight=1)


class StatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._create_widgets()
    
    def _create_widgets(self):
        self.status_label = ttk.Label(self, text="Sẵn sàng", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 5))
        
        self.item_count_label = ttk.Label(self, text="", relief=tk.SUNKEN, anchor=tk.E)
        self.item_count_label.pack(side=tk.RIGHT, padx=(5, 2))
    
    def set_status(self, message: str, is_error: bool = False):
        color = Config.THEME_COLORS['error'] if is_error else Config.THEME_COLORS['file']
        self.status_label.config(text=message, foreground=color)
    
    def set_item_count(self, count: int, total: int = None):
        if total:
            text = f"{count}/{total} mục"
        else:
            text = f"{count} mục"
        self.item_count_label.config(text=text)
    
    def clear(self):
        self.status_label.config(text="Sẵn sàng", foreground=Config.THEME_COLORS['file'])
        self.item_count_label.config(text="")


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
            dialog.title("Thông tin chi tiết")
            dialog.geometry("450x350")
            dialog.resizable(False, False)
            dialog.transient(parent)
            dialog.grab_set()
            
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            info_items = [
                ("Tên:", item_info.get('name', '')),
                ("Đường dẫn:", item_info.get('path', '')),
                ("Loại:", "Thư mục" if item_info.get('is_dir') else "Tệp"),
                ("Kích thước:", item_info.get('size', '')),
                ("Ngày sửa đổi:", item_info.get('modified', '')),
                ("Phần mở rộng:", item_info.get('extension', 'Không có')),
                ("Danh mục:", item_info.get('category', '')),
                ("Ẩn:", "Có" if item_info.get('is_hidden') else "Không")
            ]
            
            for i, (label, value) in enumerate(info_items):
                ttk.Label(main_frame, text=label, font=("TkDefaultFont", 9, "bold")).grid(
                    row=i, column=0, sticky="w", padx=(0, 10), pady=3
                )
                
                if label == "Đường dẫn:":
                    value_label = ttk.Label(main_frame, text=str(value), wraplength=300)
                else:
                    value_label = ttk.Label(main_frame, text=str(value))
                
                value_label.grid(row=i, column=1, sticky="w", pady=3)
            
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=len(info_items), column=0, columnspan=2, pady=(20, 0))
            
            ttk.Button(button_frame, text="Đóng", command=dialog.destroy).pack()
            
            dialog.focus_set()
            
            center_x = parent.winfo_rootx() + parent.winfo_width() // 2 - 225
            center_y = parent.winfo_rooty() + parent.winfo_height() // 2 - 175
            dialog.geometry(f"450x350+{center_x}+{center_y}")
            
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
                                    font=("TkDefaultFont", 10, "bold"))
        self.title_label.pack(anchor="w", padx=5, pady=5)
    
    def preview_file(self, file_path: str):
        pass
    
    def clear_preview(self):
        pass