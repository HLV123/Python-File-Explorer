import os
from pathlib import Path


class Config:
    APP_NAME = "Python File Explorer"
    APP_VERSION = "2.0"
    
    DEFAULT_WINDOW_WIDTH = 1000
    DEFAULT_WINDOW_HEIGHT = 700
    MIN_WINDOW_WIDTH = 600
    MIN_WINDOW_HEIGHT = 400
    
    DEFAULT_START_PATH = str(Path.home())
    
    # File size limits
    MAX_PREVIEW_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_SEARCH_RESULTS = 1000
    MAX_CONTENT_SEARCH_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ITEMS_DISPLAY = 10000
    CACHE_SIZE = 1000
    
    # Text preview limits
    MAX_TEXT_PREVIEW_SIZE = 50000  # 50KB
    
    SUPPORTED_FORMATS = {
        'text': ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.log', '.ini', '.cfg', '.conf'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg'],
        'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
        'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg']
    }
    
    THEME_COLORS = {
        'folder': '#0066cc',
        'file': '#333333',
        'selected': '#e6f3ff',
        'background': '#ffffff',
        'error': '#ff0000',
        'success': '#00aa00'
    }
    
    # Encoding fallbacks for text files
    TEXT_ENCODINGS = ['utf-8', 'utf-16', 'cp1252', 'latin-1', 'ascii']
    
    @classmethod
    def get_file_category(cls, file_extension):
        for category, extensions in cls.SUPPORTED_FORMATS.items():
            if file_extension.lower() in extensions:
                return category
        return 'unknown'
    
    @classmethod
    def is_text_file(cls, file_extension):
        return file_extension.lower() in cls.SUPPORTED_FORMATS['text']
    
    @classmethod
    def is_image_file(cls, file_extension):
        return file_extension.lower() in cls.SUPPORTED_FORMATS['image']