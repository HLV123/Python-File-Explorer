import logging
import sys
from pathlib import Path


class Logger:
    _logger = None
    
    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls._setup_logger()
        return cls._logger
    
    @classmethod
    def _setup_logger(cls):
        cls._logger = logging.getLogger('FileExplorer')
        cls._logger.setLevel(logging.DEBUG)
        
        if not cls._logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            log_file = Path.cwd() / 'file_explorer.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            cls._logger.addHandler(console_handler)
            cls._logger.addHandler(file_handler)
    
    @classmethod
    def log_info(cls, message):
        cls.get_logger().info(message)
    
    @classmethod
    def log_error(cls, message):
        cls.get_logger().error(message)
    
    @classmethod
    def log_warning(cls, message):
        cls.get_logger().warning(message)
    
    @classmethod
    def log_debug(cls, message):
        cls.get_logger().debug(message)