# app.py

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from file_operations import FileOperations

class FileExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python File Explorer")
        self.root.geometry("800x600")

        # Lấy thư mục nhà làm thư mục bắt đầu
        self.current_path = os.path.expanduser("~") 
        self.file_ops = FileOperations()

        self._create_widgets()
        self.populate_tree(self.current_path)

    def _create_widgets(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Thanh địa chỉ và nút
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(path_frame, text="↑ Lên", command=self.go_up).pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.bind("<Return>", self.on_path_enter)

        # Treeview để hiển thị tệp
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, columns=("size", "modified"), selectmode="browse")
        self.tree.heading("#0", text="Tên")
        self.tree.heading("size", text="Kích thước (Bytes)")
        self.tree.heading("modified", text="Ngày sửa đổi")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Thanh cuộn
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_item_double_click)

        # Frame chứa các nút hành động
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="Tạo thư mục mới", command=self.create_new_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Đổi tên", command=self.rename_selected_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Xóa", command=self.delete_selected_item).pack(side=tk.LEFT, padx=5)

    def populate_tree(self, path):
        """Làm mới Treeview với nội dung của một đường dẫn mới."""
        if not os.path.isdir(path):
            messagebox.showerror("Lỗi", f"Đường dẫn không hợp lệ: {path}")
            return

        self.current_path = path
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.current_path)

        # Xóa nội dung cũ
        for item in self.tree.get_children():
            self.tree.delete(item)

        contents = self.file_ops.get_directory_contents(path)
        if contents is None:
            return

        # Sắp xếp: thư mục lên trước
        contents.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        for item in contents:
            # Thêm tag để phân biệt màu sắc hoặc icon
            tag = "folder" if item["is_dir"] else "file"
            self.tree.insert("", tk.END, text=item["name"], values=(item["size"], item["modified"]), tags=(tag,), iid=item["path"])

        self.tree.tag_configure("folder", foreground="blue")

    def on_item_double_click(self, event):
        """Xử lý khi double-click vào một mục trong Treeview."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            return

        if os.path.isdir(selected_item_id):
            self.populate_tree(selected_item_id)
        else:
            try:
                # Mở tệp bằng ứng dụng mặc định của hệ điều hành
                os.startfile(selected_item_id)
            except AttributeError:
                # Cho macOS và Linux
                import subprocess
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, selected_item_id])
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở tệp: {e}")

    def go_up(self):
        """Đi lên thư mục cha."""
        parent_path = os.path.dirname(self.current_path)
        if parent_path != self.current_path: # Để tránh bị kẹt ở thư mục gốc
            self.populate_tree(parent_path)

    def on_path_enter(self, event):
        """Xử lý khi người dùng nhập đường dẫn và nhấn Enter."""
        new_path = self.path_entry.get()
        self.populate_tree(new_path)

    def delete_selected_item(self):
        """Xóa mục đang được chọn."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một mục để xóa.")
            return

        item_name = os.path.basename(selected_item_id)
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn chuyển '{item_name}' vào thùng rác?"):
            success, message = self.file_ops.send_to_trash(selected_item_id)
            if success:
                self.populate_tree(self.current_path) # Làm mới
            messagebox.showinfo("Thông báo", message)

    def create_new_folder(self):
        """Tạo một thư mục mới."""
        folder_name = simpledialog.askstring("Tạo thư mục", "Nhập tên thư mục mới:")
        if folder_name:
            success, message = self.file_ops.create_folder(self.current_path, folder_name)
            if success:
                self.populate_tree(self.current_path)
            messagebox.showinfo("Thông báo", message)

    def rename_selected_item(self):
        """Đổi tên mục đang được chọn."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một mục để đổi tên.")
            return
        
        old_name = os.path.basename(selected_item_id)
        new_name = simpledialog.askstring("Đổi tên", f"Nhập tên mới cho '{old_name}':", initialvalue=old_name)

        if new_name and new_name != old_name:
            success, message = self.file_ops.rename_item(selected_item_id, new_name)
            if success:
                self.populate_tree(self.current_path)
            messagebox.showinfo("Thông báo", message)