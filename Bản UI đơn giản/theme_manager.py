import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from typing import Dict, Any
from logger import Logger


class ThemeManager:
    THEMES = {
        'light': {
            'name': 'Light Theme',
            'bg': '#ffffff',
            'fg': '#000000',
            'select_bg': '#0078d4',
            'select_fg': '#ffffff',
            'tree_bg': '#ffffff',
            'tree_fg': '#000000',
            'tree_select': '#e6f3ff',
            'folder_color': '#0066cc',
            'file_color': '#333333',
            'button_bg': '#f0f0f0',
            'entry_bg': '#ffffff',
            'status_bg': '#f0f0f0',
            'border': '#cccccc'
        },
        'dark': {
            'name': 'Dark Theme',
            'bg': '#2d2d2d',
            'fg': '#ffffff',
            'select_bg': '#404040',
            'select_fg': '#ffffff',
            'tree_bg': '#383838',
            'tree_fg': '#ffffff',
            'tree_select': '#4a4a4a',
            'folder_color': '#66b3ff',
            'file_color': '#e0e0e0',
            'button_bg': '#404040',
            'entry_bg': '#505050',
            'status_bg': '#333333',
            'border': '#555555'
        },
        'blue': {
            'name': 'Blue Theme',
            'bg': '#f0f8ff',
            'fg': '#003366',
            'select_bg': '#0066cc',
            'select_fg': '#ffffff',
            'tree_bg': '#f8fcff',
            'tree_fg': '#003366',
            'tree_select': '#cce6ff',
            'folder_color': '#0066cc',
            'file_color': '#004080',
            'button_bg': '#e6f2ff',
            'entry_bg': '#ffffff',
            'status_bg': '#e6f2ff',
            'border': '#99ccff'
        },
        'green': {
            'name': 'Green Theme',
            'bg': '#f0fff0',
            'fg': '#006600',
            'select_bg': '#228b22',
            'select_fg': '#ffffff',
            'tree_bg': '#f8fff8',
            'tree_fg': '#006600',
            'tree_select': '#e6ffe6',
            'folder_color': '#228b22',
            'file_color': '#004d00',
            'button_bg': '#e6ffe6',
            'entry_bg': '#ffffff',
            'status_bg': '#e6ffe6',
            'border': '#99ff99'
        }
    }
    
    def __init__(self):
        self.current_theme = 'light'
        self.settings_file = Path.cwd() / 'theme_settings.json'
        self.load_settings()
    
    def get_current_theme(self) -> Dict[str, str]:
        return self.THEMES.get(self.current_theme, self.THEMES['light'])
    
    def set_theme(self, theme_name: str):
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            self.save_settings()
            Logger.log_info(f"Theme changed to: {theme_name}")
    
    def get_available_themes(self) -> Dict[str, str]:
        return {name: theme['name'] for name, theme in self.THEMES.items()}
    
    def apply_theme_to_widget(self, widget, widget_type: str = 'default'):
        theme = self.get_current_theme()
        
        try:
            if isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
                widget.configure(bg=theme['bg'])
            
            elif isinstance(widget, ttk.Frame):
                style = ttk.Style()
                style.configure('Themed.TFrame', background=theme['bg'])
                widget.configure(style='Themed.TFrame')
            
            elif isinstance(widget, ttk.Treeview):
                style = ttk.Style()
                style.configure('Themed.Treeview',
                               background=theme['tree_bg'],
                               foreground=theme['tree_fg'],
                               fieldbackground=theme['tree_bg'])
                style.configure('Themed.Treeview.Heading',
                               background=theme['button_bg'],
                               foreground=theme['fg'])
                widget.configure(style='Themed.Treeview')
            
            elif isinstance(widget, ttk.Button):
                style = ttk.Style()
                style.configure('Themed.TButton',
                               background=theme['button_bg'],
                               foreground=theme['fg'])
                widget.configure(style='Themed.TButton')
            
            elif isinstance(widget, ttk.Entry):
                style = ttk.Style()
                style.configure('Themed.TEntry',
                               fieldbackground=theme['entry_bg'],
                               foreground=theme['fg'])
                widget.configure(style='Themed.TEntry')
            
            elif isinstance(widget, ttk.Label):
                style = ttk.Style()
                style.configure('Themed.TLabel',
                               background=theme['bg'],
                               foreground=theme['fg'])
                widget.configure(style='Themed.TLabel')
                
        except Exception as e:
            Logger.log_debug(f"Error applying theme to widget: {e}")
    
    def apply_theme_to_app(self, root_widget):
        theme = self.get_current_theme()
        
        try:
            style = ttk.Style()
            
            style.configure('TFrame', background=theme['bg'])
            style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
            style.configure('TButton', background=theme['button_bg'], foreground=theme['fg'])
            style.configure('TEntry', fieldbackground=theme['entry_bg'], foreground=theme['fg'])
            
            style.configure('Treeview',
                           background=theme['tree_bg'],
                           foreground=theme['tree_fg'],
                           fieldbackground=theme['tree_bg'])
            style.configure('Treeview.Heading',
                           background=theme['button_bg'],
                           foreground=theme['fg'])
            
            style.map('Treeview.Heading',
                     background=[('active', theme['select_bg'])])
            style.map('Treeview',
                     background=[('selected', theme['tree_select'])],
                     foreground=[('selected', theme['fg'])])
            
            root_widget.configure(bg=theme['bg'])
            
        except Exception as e:
            Logger.log_error(f"Error applying theme to app: {e}")
    
    def get_color(self, color_key: str) -> str:
        theme = self.get_current_theme()
        return theme.get(color_key, '#000000')
    
    def save_settings(self):
        try:
            settings = {'current_theme': self.current_theme}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            Logger.log_error(f"Error saving theme settings: {e}")
    
    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_theme = settings.get('current_theme', 'light')
        except Exception as e:
            Logger.log_debug(f"Error loading theme settings: {e}")
            self.current_theme = 'light'