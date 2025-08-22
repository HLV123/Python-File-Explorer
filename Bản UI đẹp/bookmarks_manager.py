import json
from pathlib import Path
from typing import List, Dict, Optional
from logger import Logger


class BookmarksManager:
    def __init__(self):
        self.bookmarks_file = Path.cwd() / 'bookmarks.json'
        self.bookmarks = []
        self.load_bookmarks()
    
    def add_bookmark(self, path: str, name: str = None) -> bool:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return False
            
            bookmark_name = name or path_obj.name or str(path_obj)
            bookmark_path = str(path_obj.absolute())
            
            if any(b['path'] == bookmark_path for b in self.bookmarks):
                return False
            
            bookmark = {
                'name': bookmark_name,
                'path': bookmark_path,
                'icon': '📁' if path_obj.is_dir() else '📄'
            }
            
            self.bookmarks.append(bookmark)
            self.save_bookmarks()
            Logger.log_info(f"Added bookmark: {bookmark_name}")
            return True
            
        except Exception as e:
            Logger.log_error(f"Error adding bookmark: {e}")
            return False
    
    def remove_bookmark(self, path: str) -> bool:
        try:
            path_abs = str(Path(path).absolute())
            original_count = len(self.bookmarks)
            self.bookmarks = [b for b in self.bookmarks if b['path'] != path_abs]
            
            if len(self.bookmarks) < original_count:
                self.save_bookmarks()
                Logger.log_info(f"Removed bookmark: {path}")
                return True
            return False
            
        except Exception as e:
            Logger.log_error(f"Error removing bookmark: {e}")
            return False
    
    def get_bookmarks(self) -> List[Dict]:
        valid_bookmarks = []
        changed = False
        
        for bookmark in self.bookmarks:
            if Path(bookmark['path']).exists():
                valid_bookmarks.append(bookmark)
            else:
                Logger.log_debug(f"Removing invalid bookmark: {bookmark['path']}")
                changed = True
        
        if changed:
            self.bookmarks = valid_bookmarks
            self.save_bookmarks()
        
        return self.bookmarks
    
    def is_bookmarked(self, path: str) -> bool:
        try:
            path_abs = str(Path(path).absolute())
            return any(b['path'] == path_abs for b in self.bookmarks)
        except:
            return False
    
    def get_bookmark_by_path(self, path: str) -> Optional[Dict]:
        try:
            path_abs = str(Path(path).absolute())
            for bookmark in self.bookmarks:
                if bookmark['path'] == path_abs:
                    return bookmark
        except:
            pass
        return None
    
    def update_bookmark_name(self, path: str, new_name: str) -> bool:
        try:
            path_abs = str(Path(path).absolute())
            for bookmark in self.bookmarks:
                if bookmark['path'] == path_abs:
                    bookmark['name'] = new_name
                    self.save_bookmarks()
                    Logger.log_info(f"Updated bookmark name: {new_name}")
                    return True
            return False
            
        except Exception as e:
            Logger.log_error(f"Error updating bookmark: {e}")
            return False
    
    def reorder_bookmarks(self, from_index: int, to_index: int) -> bool:
        try:
            if 0 <= from_index < len(self.bookmarks) and 0 <= to_index < len(self.bookmarks):
                bookmark = self.bookmarks.pop(from_index)
                self.bookmarks.insert(to_index, bookmark)
                self.save_bookmarks()
                return True
            return False
            
        except Exception as e:
            Logger.log_error(f"Error reordering bookmarks: {e}")
            return False
    
    def save_bookmarks(self):
        try:
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            Logger.log_error(f"Error saving bookmarks: {e}")
    
    def load_bookmarks(self):
        try:
            if self.bookmarks_file.exists():
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            else:
                self._create_default_bookmarks()
        except Exception as e:
            Logger.log_debug(f"Error loading bookmarks: {e}")
            self._create_default_bookmarks()
    
    def _create_default_bookmarks(self):
        try:
            default_paths = [
                str(Path.home()),
                str(Path.home() / 'Desktop'),
                str(Path.home() / 'Documents'),
                str(Path.home() / 'Downloads')
            ]
            
            for path in default_paths:
                if Path(path).exists():
                    self.add_bookmark(path)
                    
        except Exception as e:
            Logger.log_debug(f"Error creating default bookmarks: {e}")
    
    def export_bookmarks(self, file_path: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
            Logger.log_info(f"Bookmarks exported to: {file_path}")
            return True
        except Exception as e:
            Logger.log_error(f"Error exporting bookmarks: {e}")
            return False
    
    def import_bookmarks(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_bookmarks = json.load(f)
            
            for bookmark in imported_bookmarks:
                if 'name' in bookmark and 'path' in bookmark:
                    self.add_bookmark(bookmark['path'], bookmark['name'])
            
            Logger.log_info(f"Bookmarks imported from: {file_path}")
            return True
        except Exception as e:
            Logger.log_error(f"Error importing bookmarks: {e}")
            return False