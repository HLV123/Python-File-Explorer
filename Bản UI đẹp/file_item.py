import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import Config


class FileItem:
    def __init__(self, path: str):
        self.path = Path(path)
        self._name = None
        self._size = None
        self._modified = None
        self._is_dir = None
        self._is_hidden = None
        self._extension = None
        self._category = None
        
    @property
    def name(self) -> str:
        if self._name is None:
            self._name = self.path.name
        return self._name
    
    @property
    def size(self) -> int:
        if self._size is None:
            try:
                self._size = self.path.stat().st_size if not self.is_dir else 0
            except (OSError, PermissionError):
                self._size = 0
        return self._size
    
    @property
    def size_formatted(self) -> str:
        if self.is_dir:
            return ""
        
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}" if size != int(size) else f"{int(size)} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    @property
    def modified(self) -> datetime:
        if self._modified is None:
            try:
                timestamp = self.path.stat().st_mtime
                self._modified = datetime.fromtimestamp(timestamp)
            except (OSError, PermissionError):
                self._modified = datetime.now()
        return self._modified
    
    @property
    def modified_formatted(self) -> str:
        return self.modified.strftime('%Y-%m-%d %H:%M:%S')
    
    @property
    def is_dir(self) -> bool:
        if self._is_dir is None:
            self._is_dir = self.path.is_dir()
        return self._is_dir
    
    @property
    def is_hidden(self) -> bool:
        if self._is_hidden is None:
            self._is_hidden = self.name.startswith('.')
        return self._is_hidden
    
    @property
    def extension(self) -> str:
        if self._extension is None:
            self._extension = self.path.suffix.lower()
        return self._extension
    
    @property
    def category(self) -> str:
        if self._category is None:
            if self.is_dir:
                self._category = 'folder'
            else:
                self._category = Config.get_file_category(self.extension)
        return self._category
    
    @property
    def full_path(self) -> str:
        return str(self.path.absolute())
    
    @property
    def parent_path(self) -> str:
        return str(self.path.parent.absolute())
    
    def exists(self) -> bool:
        return self.path.exists()
    
    def is_accessible(self) -> bool:
        try:
            self.path.stat()
            return True
        except (OSError, PermissionError):
            return False
    
    def get_icon(self) -> str:
        icons = {
            'folder': '📁',
            'text': '📄',
            'image': '🖼️',
            'document': '📝',
            'archive': '📦',
            'video': '🎬',
            'audio': '🎵',
            'unknown': '📄'
        }
        return icons.get(self.category, '📄')
    
    def __str__(self) -> str:
        return f"FileItem(name='{self.name}', path='{self.full_path}', is_dir={self.is_dir})"
    
    def __repr__(self) -> str:
        return self.__str__()