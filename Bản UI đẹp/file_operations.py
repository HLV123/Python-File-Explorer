import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
from send2trash import send2trash
from file_item import FileItem
from exceptions import *
from logger import Logger
from config import Config


class FileOperations:
    
    @staticmethod
    def get_directory_contents(path: str, show_hidden: bool = False) -> List[FileItem]:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise ItemNotFoundError(f"Path does not exist: {path}")
            
            if not path_obj.is_dir():
                raise InvalidPathError(f"Path is not a directory: {path}")
            
            items = []
            item_count = 0
            
            try:
                for item_path in path_obj.iterdir():
                    if item_count >= Config.MAX_ITEMS_DISPLAY:
                        Logger.log_warning(f"Directory contains too many items. Showing first {Config.MAX_ITEMS_DISPLAY} items.")
                        break
                    
                    try:
                        file_item = FileItem(str(item_path))
                        
                        if not show_hidden and file_item.is_hidden:
                            continue
                        
                        if file_item.is_accessible():
                            items.append(file_item)
                            item_count += 1
                        else:
                            Logger.log_debug(f"Skipping inaccessible item: {item_path}")
                            
                    except Exception as e:
                        Logger.log_debug(f"Error processing item {item_path}: {e}")
                        continue
                        
            except PermissionError:
                raise PermissionDeniedError(f"Access denied to directory: {path}")
            
            return FileOperations._sort_items(items)
            
        except PermissionError:
            raise PermissionDeniedError(f"Access denied to directory: {path}")
        except OSError as e:
            raise PathAccessError(f"Cannot access directory {path}: {e}")
    
    @staticmethod
    def _sort_items(items: List[FileItem]) -> List[FileItem]:
        return sorted(items, key=lambda x: (not x.is_dir, x.name.lower()))
    
    @staticmethod
    def send_to_trash(path: str) -> Tuple[bool, str]:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise ItemNotFoundError(f"Item does not exist: {path}")
            
            item_name = path_obj.name
            send2trash(str(path_obj))
            
            Logger.log_info(f"Successfully moved to trash: {item_name}")
            return True, f"Đã chuyển '{item_name}' vào thùng rác."
            
        except Exception as e:
            error_msg = f"Lỗi khi xóa '{Path(path).name}': {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
    
    @staticmethod
    def create_folder(parent_path: str, folder_name: str) -> Tuple[bool, str]:
        try:
            if not folder_name or not folder_name.strip():
                raise ValueError("Folder name cannot be empty")
            
            folder_name = folder_name.strip()
            
            # Validate folder name characters
            invalid_chars = r'<>:"/\|?*'
            if any(char in folder_name for char in invalid_chars):
                raise ValueError(f"Folder name contains invalid characters: {invalid_chars}")
            
            parent = Path(parent_path)
            if not parent.exists() or not parent.is_dir():
                raise InvalidPathError(f"Parent directory does not exist: {parent_path}")
            
            new_folder_path = parent / folder_name
            if new_folder_path.exists():
                return False, f"Thư mục '{folder_name}' đã tồn tại."
            
            new_folder_path.mkdir(parents=True, exist_ok=False)
            
            Logger.log_info(f"Created folder: {new_folder_path}")
            return True, f"Đã tạo thư mục '{folder_name}'."
            
        except PermissionError:
            error_msg = f"Không có quyền tạo thư mục trong '{parent_path}'"
            Logger.log_error(error_msg)
            return False, error_msg
        except ValueError as e:
            error_msg = str(e)
            Logger.log_error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Lỗi khi tạo thư mục: {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
    
    @staticmethod
    def rename_item(old_path: str, new_name: str) -> Tuple[bool, str]:
        try:
            if not new_name or not new_name.strip():
                raise ValueError("New name cannot be empty")
            
            new_name = new_name.strip()
            
            # Validate new name characters
            invalid_chars = r'<>:"/\|?*'
            if any(char in new_name for char in invalid_chars):
                raise ValueError(f"Name contains invalid characters: {invalid_chars}")
            
            old_path_obj = Path(old_path)
            if not old_path_obj.exists():
                raise ItemNotFoundError(f"Item does not exist: {old_path}")
            
            new_path_obj = old_path_obj.parent / new_name
            if new_path_obj.exists():
                return False, f"Tên '{new_name}' đã tồn tại."
            
            old_path_obj.rename(new_path_obj)
            
            Logger.log_info(f"Renamed: {old_path_obj.name} -> {new_name}")
            return True, f"Đã đổi tên thành '{new_name}'."
            
        except PermissionError:
            error_msg = f"Không có quyền đổi tên '{Path(old_path).name}'"
            Logger.log_error(error_msg)
            return False, error_msg
        except ValueError as e:
            error_msg = str(e)
            Logger.log_error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Lỗi khi đổi tên: {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
    
    @staticmethod
    def copy_item(source_path: str, destination_path: str) -> Tuple[bool, str]:
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                raise ItemNotFoundError(f"Source does not exist: {source_path}")
            
            if destination.exists():
                return False, f"Destination already exists: {destination.name}"
            
            # Ensure destination parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            if source.is_dir():
                shutil.copytree(source, destination)
                action = "Copied folder"
            else:
                shutil.copy2(source, destination)
                action = "Copied file"
            
            Logger.log_info(f"{action}: {source.name} -> {destination.name}")
            return True, f"Đã sao chép '{source.name}' thành công."
            
        except PermissionError:
            error_msg = f"Không có quyền sao chép '{Path(source_path).name}'"
            Logger.log_error(error_msg)
            return False, error_msg
        except shutil.Error as e:
            error_msg = f"Lỗi khi sao chép: {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Lỗi khi sao chép: {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
    
    @staticmethod
    def move_item(source_path: str, destination_path: str) -> Tuple[bool, str]:
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            
            if not source.exists():
                raise ItemNotFoundError(f"Source does not exist: {source_path}")
            
            if destination.exists():
                return False, f"Destination already exists: {destination.name}"
            
            # Ensure destination parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            
            Logger.log_info(f"Moved: {source.name} -> {destination.name}")
            return True, f"Đã di chuyển '{source.name}' thành công."
            
        except PermissionError:
            error_msg = f"Không có quyền di chuyển '{Path(source_path).name}'"
            Logger.log_error(error_msg)
            return False, error_msg
        except shutil.Error as e:
            error_msg = f"Lỗi khi di chuyển: {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Lỗi khi di chuyển: {str(e)}"
            Logger.log_error(error_msg)
            return False, error_msg
    
    @staticmethod
    def get_item_info(path: str) -> Optional[dict]:
        try:
            file_item = FileItem(path)
            if not file_item.exists():
                return None
            
            return {
                'name': file_item.name,
                'path': file_item.full_path,
                'size': file_item.size_formatted,
                'modified': file_item.modified_formatted,
                'is_dir': file_item.is_dir,
                'category': file_item.category,
                'extension': file_item.extension,
                'is_hidden': file_item.is_hidden
            }
        except Exception as e:
            Logger.log_error(f"Error getting item info for {path}: {e}")
            return None
    
    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate if path is safe and accessible"""
        try:
            path_obj = Path(path).resolve()
            return path_obj.exists() and path_obj.is_dir()
        except (OSError, ValueError):
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Generate a safe filename by removing invalid characters"""
        invalid_chars = r'<>:"/\|?*'
        safe_name = filename
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name.strip()
    
    @staticmethod
    def get_available_space(path: str) -> Optional[int]:
        """Get available disk space for given path"""
        try:
            stat = os.statvfs(path) if hasattr(os, 'statvfs') else None
            if stat:
                return stat.f_bavail * stat.f_frsize
            else:
                # Windows fallback
                import shutil
                return shutil.disk_usage(path).free
        except Exception as e:
            Logger.log_debug(f"Could not get disk space for {path}: {e}")
            return None