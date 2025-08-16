#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD
from gui import BackgroundRemoverApp
import sys
import subprocess
import importlib.util

def check_dependencies():
    required_packages = {
        'rembg': 'rembg[cli]',
        'onnxruntime': 'onnxruntime'
    }
    missing = []
    
    for package, install_name in required_packages.items():
        if importlib.util.find_spec(package) is None:
            missing.append(install_name)
    
    if missing:
        msg = "The following dependencies need to be installed:\n\n"
        msg += "\n".join([f"• {pkg}" for pkg in missing])
        msg += "\n\nWould you like to install them now?"
        
        if messagebox.askyesno("Install Dependencies", msg):
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install'
                ] + missing, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                messagebox.showinfo("Success", "Dependencies installed successfully!")
                return True
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to install dependencies: {str(e)}")
                return False
        return False
    return True

def main():
    # Create a temporary root window for dependency check dialog
    temp_root = tk.Tk()
    temp_root.withdraw()  # Hide the temporary window
    
    if not check_dependencies():
        temp_root.destroy()
        return
        
    temp_root.destroy()
    root = TkinterDnD.Tk()
    root.title("Background Remover")
    # Set minimum window size
    root.minsize(800, 600)
    
    # Check dependencies before starting
    from utils import install_dependencies
    if not install_dependencies(root):
        return
    
    app = BackgroundRemoverApp(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    main()