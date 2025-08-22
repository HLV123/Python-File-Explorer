import os
import re
import threading
from pathlib import Path
from typing import List, Callable, Optional
from file_item import FileItem
from logger import Logger
from config import Config


class SearchManager:
    def __init__(self):
        self.search_thread = None
        self.stop_search = False
        
    def search_files(self, search_path: str, query: str, 
                    on_result: Callable[[FileItem], None],
                    on_complete: Callable[[int], None],
                    case_sensitive: bool = False,
                    search_content: bool = False,
                    file_extensions: List[str] = None) -> None:
        
        # Stop any existing search
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search = True
            self.search_thread.join(timeout=2.0)
        
        self.stop_search = False
        self.search_thread = threading.Thread(
            target=self._search_worker,
            args=(search_path, query, on_result, on_complete, 
                 case_sensitive, search_content, file_extensions),
            daemon=True
        )
        self.search_thread.start()
    
    def _search_worker(self, search_path: str, query: str,
                      on_result: Callable[[FileItem], None],
                      on_complete: Callable[[int], None],
                      case_sensitive: bool,
                      search_content: bool,
                      file_extensions: List[str]) -> None:
        
        results_count = 0
        query_pattern = query if case_sensitive else query.lower()
        
        try:
            for root, dirs, files in os.walk(search_path):
                if self.stop_search:
                    break
                
                # Search directories first
                for dir_name in dirs[:]:  # Use slice to allow modification
                    if self.stop_search:
                        break
                    
                    try:
                        dir_path = os.path.join(root, dir_name)
                        
                        if self._matches_name_criteria(dir_name, query_pattern, case_sensitive):
                            file_item = FileItem(dir_path)
                            if file_item.is_accessible():
                                on_result(file_item)
                                results_count += 1
                                
                                if results_count >= Config.MAX_SEARCH_RESULTS:
                                    self.stop_search = True
                                    break
                                    
                    except (PermissionError, OSError) as e:
                        Logger.log_debug(f"Search access denied: {dir_path} - {e}")
                        # Remove inaccessible directory from search
                        dirs.remove(dir_name)
                        continue
                
                # Search files
                for file_name in files:
                    if self.stop_search:
                        break
                    
                    try:
                        file_path = os.path.join(root, file_name)
                        
                        if self._matches_criteria(file_name, file_path, query_pattern, 
                                                case_sensitive, search_content, 
                                                file_extensions):
                            file_item = FileItem(file_path)
                            if file_item.is_accessible():
                                on_result(file_item)
                                results_count += 1
                                
                                if results_count >= Config.MAX_SEARCH_RESULTS:
                                    self.stop_search = True
                                    break
                                    
                    except (PermissionError, OSError) as e:
                        Logger.log_debug(f"Search access denied: {file_path} - {e}")
                        continue
                        
        except Exception as e:
            Logger.log_error(f"Search error: {e}")
        finally:
            if not self.stop_search:
                on_complete(results_count)
    
    def _matches_name_criteria(self, item_name: str, query: str, case_sensitive: bool) -> bool:
        """Check if item name matches search query"""
        search_name = item_name if case_sensitive else item_name.lower()
        return query in search_name
    
    def _matches_criteria(self, file_name: str, file_path: str, query: str,
                         case_sensitive: bool, search_content: bool,
                         file_extensions: List[str]) -> bool:
        
        # Check name match first
        if self._matches_name_criteria(file_name, query, case_sensitive):
            # If extensions filter is specified, check extension
            if file_extensions:
                file_ext = Path(file_name).suffix.lower()
                return file_ext in file_extensions
            return True
        
        # If name doesn't match, try content search
        if search_content and self._should_search_content(file_path):
            return self._search_file_content(file_path, query, case_sensitive)
            
        return False
    
    def _should_search_content(self, file_path: str) -> bool:
        """Determine if file should be searched for content"""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > Config.MAX_CONTENT_SEARCH_SIZE:
                return False
            
            # Check if it's likely a text file
            file_ext = Path(file_path).suffix.lower()
            return Config.is_text_file(file_ext)
            
        except (OSError, PermissionError):
            return False
    
    def _search_file_content(self, file_path: str, query: str, case_sensitive: bool) -> bool:
        """Search within file content"""
        try:
            # Try different encodings
            for encoding in Config.TEXT_ENCODINGS:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        # Read in chunks to handle large files
                        chunk_size = 8192
                        buffer = ""
                        query_to_search = query if case_sensitive else query.lower()
                        
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                                
                            buffer += chunk
                            search_text = buffer if case_sensitive else buffer.lower()
                            
                            if query_to_search in search_text:
                                return True
                            
                            # Keep some overlap for multi-chunk matches
                            if len(buffer) > len(query) * 2:
                                buffer = buffer[-len(query):]
                                
                    break  # Successfully read with this encoding
                    
                except UnicodeDecodeError:
                    continue  # Try next encoding
                    
            return False
            
        except (PermissionError, OSError, MemoryError) as e:
            Logger.log_debug(f"Could not search content of {file_path}: {e}")
            return False
    
    def stop_current_search(self):
        """Stop the current search operation"""
        self.stop_search = True
        if self.search_thread and self.search_thread.is_alive():
            self.search_thread.join(timeout=3.0)
            if self.search_thread.is_alive():
                Logger.log_warning("Search thread did not terminate cleanly")
    
    def is_searching(self) -> bool:
        """Check if a search is currently in progress"""
        return self.search_thread and self.search_thread.is_alive() and not self.stop_search