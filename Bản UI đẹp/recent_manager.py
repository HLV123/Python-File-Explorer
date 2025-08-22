import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from logger import Logger


class RecentManager:
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.recent_file = Path.cwd() / 'recent_files.json'
        self.recent_items = []
        self.load_recent_items()
    
    def add_recent_item(self, path: str, action: str = 'opened') -> bool:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return False
            
            path_abs = str(path_obj.absolute())
            
            self.remove_item_by_path(path_abs)
            
            recent_item = {
                'name': path_obj.name,
                'path': path_abs,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'is_dir': path_obj.is_dir(),
                'size': path_obj.stat().st_size if path_obj.is_file() else 0,
                'icon': '📁' if path_obj.is_dir() else '📄'
            }
            
            self.recent_items.insert(0, recent_item)
            
            if len(self.recent_items) > self.max_items:
                self.recent_items = self.recent_items[:self.max_items]
            
            self.save_recent_items()
            Logger.log_debug(f"Added to recent: {path_obj.name}")
            return True
            
        except Exception as e:
            Logger.log_error(f"Error adding recent item: {e}")
            return False
    
    def remove_item_by_path(self, path: str) -> bool:
        try:
            path_abs = str(Path(path).absolute())
            original_count = len(self.recent_items)
            self.recent_items = [item for item in self.recent_items if item['path'] != path_abs]
            
            if len(self.recent_items) < original_count:
                self.save_recent_items()
                return True
            return False
            
        except Exception as e:
            Logger.log_error(f"Error removing recent item: {e}")
            return False
    
    def get_recent_items(self, limit: int = None) -> List[Dict]:
        self.cleanup_invalid_items()
        
        if limit:
            return self.recent_items[:limit]
        return self.recent_items
    
    def get_recent_files(self, limit: int = 20) -> List[Dict]:
        files = [item for item in self.recent_items if not item['is_dir']]
        return files[:limit] if limit else files
    
    def get_recent_folders(self, limit: int = 20) -> List[Dict]:
        folders = [item for item in self.recent_items if item['is_dir']]
        return folders[:limit] if limit else folders
    
    def cleanup_invalid_items(self) -> int:
        valid_items = []
        removed_count = 0
        
        for item in self.recent_items:
            if Path(item['path']).exists():
                valid_items.append(item)
            else:
                removed_count += 1
                Logger.log_debug(f"Removing invalid recent item: {item['path']}")
        
        if removed_count > 0:
            self.recent_items = valid_items
            self.save_recent_items()
        
        return removed_count
    
    def clear_recent_items(self):
        self.recent_items = []
        self.save_recent_items()
        Logger.log_info("Cleared all recent items")
    
    def search_recent_items(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        matches = []
        
        for item in self.recent_items:
            if (query_lower in item['name'].lower() or 
                query_lower in item['path'].lower()):
                matches.append(item)
        
        return matches
    
    def get_item_by_path(self, path: str) -> Optional[Dict]:
        try:
            path_abs = str(Path(path).absolute())
            for item in self.recent_items:
                if item['path'] == path_abs:
                    return item
        except:
            pass
        return None
    
    def get_frequent_items(self, limit: int = 10) -> List[Dict]:
        path_counts = {}
        
        for item in self.recent_items:
            path = item['path']
            if path in path_counts:
                path_counts[path]['count'] += 1
            else:
                path_counts[path] = {
                    'item': item,
                    'count': 1
                }
        
        sorted_items = sorted(path_counts.values(), 
                            key=lambda x: x['count'], 
                            reverse=True)
        
        return [item['item'] for item in sorted_items[:limit]]
    
    def get_recent_by_date(self, days: int = 7) -> List[Dict]:
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_items = []
        
        for item in self.recent_items:
            try:
                item_date = datetime.fromisoformat(item['timestamp'])
                if item_date >= cutoff_date:
                    recent_items.append(item)
            except:
                continue
        
        return recent_items
    
    def save_recent_items(self):
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_items, f, indent=2, ensure_ascii=False)
        except Exception as e:
            Logger.log_error(f"Error saving recent items: {e}")
    
    def load_recent_items(self):
        try:
            if self.recent_file.exists():
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    self.recent_items = json.load(f)
                self.cleanup_invalid_items()
        except Exception as e:
            Logger.log_debug(f"Error loading recent items: {e}")
            self.recent_items = []