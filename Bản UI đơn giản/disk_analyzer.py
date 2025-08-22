import os
import threading
from pathlib import Path
from typing import Dict, List, Callable, Optional, Tuple
from collections import defaultdict
from logger import Logger


class DiskAnalyzer:
    def __init__(self):
        self.analysis_thread = None
        self.stop_analysis = False
        
    def analyze_directory(self, path: str, 
                         on_progress: Callable[[str, int], None],
                         on_complete: Callable[[Dict], None],
                         max_depth: int = 3) -> None:
        
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.stop_analysis = True
            self.analysis_thread.join(timeout=2.0)
        
        self.stop_analysis = False
        self.analysis_thread = threading.Thread(
            target=self._analyze_worker,
            args=(path, on_progress, on_complete, max_depth)
        )
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
    
    def _analyze_worker(self, path: str, 
                       on_progress: Callable[[str, int], None],
                       on_complete: Callable[[Dict], None],
                       max_depth: int) -> None:
        
        try:
            result = {
                'total_size': 0,
                'file_count': 0,
                'folder_count': 0,
                'largest_files': [],
                'largest_folders': [],
                'file_types': defaultdict(lambda: {'count': 0, 'size': 0}),
                'depth_analysis': {},
                'empty_folders': [],
                'duplicate_candidates': defaultdict(list)
            }
            
            processed_items = 0
            
            for root, dirs, files in os.walk(path):
                if self.stop_analysis:
                    return
                
                try:
                    current_depth = root.replace(path, '').count(os.sep)
                    if current_depth > max_depth:
                        dirs.clear()
                        continue
                    
                    if not files and not dirs:
                        result['empty_folders'].append(root)
                    
                    folder_size = 0
                    
                    for file_name in files:
                        if self.stop_analysis:
                            return
                        
                        file_path = os.path.join(root, file_name)
                        
                        try:
                            file_size = os.path.getsize(file_path)
                            file_ext = Path(file_name).suffix.lower()
                            
                            result['total_size'] += file_size
                            result['file_count'] += 1
                            folder_size += file_size
                            
                            result['file_types'][file_ext]['count'] += 1
                            result['file_types'][file_ext]['size'] += file_size
                            
                            self._update_largest_files(result['largest_files'], {
                                'path': file_path,
                                'name': file_name,
                                'size': file_size
                            })
                            
                            self._add_duplicate_candidate(result['duplicate_candidates'], 
                                                        file_name, file_path, file_size)
                            
                            processed_items += 1
                            if processed_items % 100 == 0:
                                on_progress(f"Phân tích: {file_name}", processed_items)
                                
                        except (OSError, PermissionError) as e:
                            Logger.log_debug(f"Cannot access file {file_path}: {e}")
                            continue
                    
                    if folder_size > 0:
                        result['folder_count'] += 1
                        self._update_largest_folders(result['largest_folders'], {
                            'path': root,
                            'name': os.path.basename(root) or root,
                            'size': folder_size
                        })
                    
                    if current_depth not in result['depth_analysis']:
                        result['depth_analysis'][current_depth] = {
                            'folders': 0, 'files': 0, 'size': 0
                        }
                    
                    result['depth_analysis'][current_depth]['folders'] += 1
                    result['depth_analysis'][current_depth]['files'] += len(files)
                    result['depth_analysis'][current_depth]['size'] += folder_size
                    
                except (OSError, PermissionError) as e:
                    Logger.log_debug(f"Cannot access directory {root}: {e}")
                    continue
            
            result['largest_files'] = sorted(result['largest_files'], 
                                           key=lambda x: x['size'], reverse=True)[:20]
            result['largest_folders'] = sorted(result['largest_folders'], 
                                             key=lambda x: x['size'], reverse=True)[:20]
            
            result['file_types'] = dict(sorted(result['file_types'].items(), 
                                             key=lambda x: x[1]['size'], reverse=True))
            
            if not self.stop_analysis:
                on_complete(result)
                
        except Exception as e:
            Logger.log_error(f"Analysis error: {e}")
    
    def _update_largest_files(self, largest_files: List[Dict], file_info: Dict):
        largest_files.append(file_info)
        if len(largest_files) > 50:
            largest_files.sort(key=lambda x: x['size'], reverse=True)
            largest_files[:] = largest_files[:50]
    
    def _update_largest_folders(self, largest_folders: List[Dict], folder_info: Dict):
        largest_folders.append(folder_info)
        if len(largest_folders) > 50:
            largest_folders.sort(key=lambda x: x['size'], reverse=True)
            largest_folders[:] = largest_folders[:50]
    
    def _add_duplicate_candidate(self, duplicates: Dict, file_name: str, 
                               file_path: str, file_size: int):
        key = f"{file_name}_{file_size}"
        duplicates[key].append({
            'path': file_path,
            'name': file_name,
            'size': file_size
        })
    
    def stop_current_analysis(self):
        self.stop_analysis = True
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=3.0)
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}" if size_bytes != int(size_bytes) else f"{int(size_bytes)} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def get_folder_size(folder_path: str) -> Tuple[int, int]:
        total_size = 0
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file_name in files:
                    try:
                        file_path = os.path.join(root, file_name)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        
        return total_size, file_count