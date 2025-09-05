#!/usr/bin/env python3
"""
Simple test script to verify the UI works without dependencies
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tkinterdnd2 import TkinterDnD
    from gui import BackgroundRemoverApp
    
    def main():
        root = TkinterDnD.Tk()
        root.title("Background Remover - UI Test")
        root.minsize(800, 600)
        
        app = BackgroundRemoverApp(root)
        app.pack(fill=tk.BOTH, expand=True)
        
        print("✅ UI loaded successfully!")
        print("🎨 The interface should show a clean, modern design")
        print("📁 Try the drag & drop area and buttons")
        
        root.mainloop()

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed:")
    print("   pip install tkinterdnd2 Pillow")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()