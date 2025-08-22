import os
import platform
import psutil
from pathlib import Path
from typing import List, Dict
from logger import Logger


class DriveManager:
    
    @staticmethod
    def get_all_drives() -> List[Dict]:
        drives = []
        system = platform.system()
        
        try:
            if system == "Windows":
                drives = DriveManager._get_windows_drives()
            else:
                drives = DriveManager._get_unix_drives()
                
        except Exception as e:
            Logger.log_error(f"Error getting drives: {e}")
            
        return drives
    
    @staticmethod
    def _get_windows_drives() -> List[Dict]:
        drives = []
        
        for partition in psutil.disk_partitions():
            try:
                drive_info = {
                    'path': partition.mountpoint,
                    'device': partition.device,
                    'fstype': partition.fstype,
                    'name': f"{partition.device} ({partition.fstype})",
                    'icon': DriveManager._get_drive_icon(partition.device, partition.fstype)
                }
                
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drive_info.update({
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    })
                except (PermissionError, OSError):
                    drive_info.update({
                        'total': 0,
                        'used': 0,
                        'free': 0,
                        'percent': 0
                    })
                
                drives.append(drive_info)
                
            except Exception as e:
                Logger.log_debug(f"Error processing drive {partition.device}: {e}")
                continue
                
        return drives
    
    @staticmethod
    def _get_unix_drives() -> List[Dict]:
        drives = []
        
        home_drive = {
            'path': str(Path.home()),
            'device': 'Home',
            'fstype': 'local',
            'name': f"🏠 Home ({Path.home()})",
            'icon': '🏠'
        }
        drives.append(home_drive)
        
        root_drive = {
            'path': '/',
            'device': 'Root',
            'fstype': 'local',
            'name': '💻 Root (/)',
            'icon': '💻'
        }
        drives.append(root_drive)
        
        for partition in psutil.disk_partitions():
            if partition.mountpoint not in ['/', str(Path.home())]:
                try:
                    drive_info = {
                        'path': partition.mountpoint,
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'name': f"{partition.mountpoint} ({partition.fstype})",
                        'icon': DriveManager._get_drive_icon(partition.device, partition.fstype)
                    }
                    drives.append(drive_info)
                except Exception as e:
                    Logger.log_debug(f"Error processing drive {partition.device}: {e}")
                    continue
                    
        return drives
    
    @staticmethod
    def _get_drive_icon(device: str, fstype: str) -> str:
        device_lower = device.lower()
        fstype_lower = fstype.lower()
        
        if 'usb' in device_lower or 'removable' in fstype_lower:
            return '💾'
        elif 'cd' in device_lower or 'dvd' in device_lower:
            return '💿'
        elif 'network' in fstype_lower or 'nfs' in fstype_lower:
            return '🌐'
        elif device_lower.startswith('c:'):
            return '💻'
        else:
            return '💽'
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}" if size_bytes != int(size_bytes) else f"{int(size_bytes)} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"