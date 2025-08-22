#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app import FileExplorerApp
    from logger import Logger
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all files are in the same directory and dependencies are installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import send2trash
        import psutil
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install send2trash psutil")
        return False


def main():
    """Main entry point for the File Explorer application"""
    try:
        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)
        
        # Initialize Tkinter root
        root = tk.Tk()
        
        # Set error handling for Tkinter
        def handle_tk_error(error):
            Logger.log_error(f"Tkinter error: {error}")
            return True  # Continue running
        
        root.report_callback_exception = handle_tk_error
        
        # Create and run the application
        app = FileExplorerApp(root)
        
        Logger.log_info("File Explorer application started successfully")
        
        # Start the main loop
        root.mainloop()
        
    except KeyboardInterrupt:
        Logger.log_info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        Logger.log_error(f"Critical application error: {e}")
        print(f"Application failed to start: {e}")
        sys.exit(1)
    finally:
        Logger.log_info("File Explorer application terminated")


if __name__ == "__main__":
    main()