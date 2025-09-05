import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Optional

class ScrollableImageView(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self)
        
        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set
        )
        
        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Image display
        self.image_label = ttk.Label(self.canvas)
        self.canvas.create_window((0, 0), window=self.image_label, anchor="nw")
        
        # Enhanced zoom control with better styling
        zoom_frame = ttk.Frame(self)
        zoom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        # Zoom controls with improved icons and layout
        ttk.Button(zoom_frame, text="−", width=3, command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="+", width=3, command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="⊞", width=3, command=self.zoom_fit).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="1:1", width=3, command=self.zoom_actual).pack(side=tk.LEFT, padx=2)

        # Zoom level display
        self.zoom_var = tk.StringVar(value="100%")
        ttk.Label(zoom_frame, textvariable=self.zoom_var, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10, 2))
        
        # State
        self.photo_image = None
        self.pil_image = None
        self.zoom_factor = 1.0
        
        # Bind events for better interaction
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

        # Variables for panning
        self.last_x = 0
        self.last_y = 0
        
    def set_image(self, image: Image.Image):
        """Set a new image to display"""
        self.pil_image = image
        self.zoom_factor = 1.0
        self.update_view()
        
    def clear(self):
        """Clear the current image"""
        self.pil_image = None
        self.photo_image = None
        self.image_label.configure(image=None)
        
    def update_view(self):
        """Update the displayed image with current zoom factor and zoom level display"""
        if self.pil_image:
            # Calculate new size
            new_width = int(self.pil_image.width * self.zoom_factor)
            new_height = int(self.pil_image.height * self.zoom_factor)

            # Resize image with high quality
            resized = self.pil_image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )

            # Update photo image
            self.photo_image = ImageTk.PhotoImage(resized)
            self.image_label.configure(image=self.photo_image)

            # Update zoom level display
            zoom_percent = int(self.zoom_factor * 100)
            self.zoom_var.set(f"{zoom_percent}%")

            # Update canvas scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
    def zoom_in(self):
        """Increase zoom factor by 20%"""
        if self.pil_image:
            self.zoom_factor *= 1.2
            self.update_view()
            
    def zoom_out(self):
        """Decrease zoom factor by 20%"""
        if self.pil_image:
            self.zoom_factor *= 0.8
            self.update_view()
            
    def zoom_fit(self):
        """Fit image to window size"""
        if self.pil_image:
            # Get canvas size
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:  # Ensure canvas is properly sized
                # Calculate zoom factors for width and height
                width_factor = canvas_width / self.pil_image.width
                height_factor = canvas_height / self.pil_image.height

                # Use smallest factor to fit image in both dimensions
                self.zoom_factor = min(width_factor, height_factor) * 0.9
                self.update_view()

    def zoom_actual(self):
        """Reset zoom to actual size (100%)"""
        if self.pil_image:
            self.zoom_factor = 1.0
            self.update_view()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        if self.pil_image:
            # Zoom in/out based on wheel direction
            if event.delta > 0:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor *= 0.9

            # Limit zoom range
            self.zoom_factor = max(0.1, min(self.zoom_factor, 10.0))
            self.update_view()

    def on_canvas_click(self, event):
        """Handle canvas click for panning start"""
        self.last_x = event.x
        self.last_y = event.y

    def on_canvas_drag(self, event):
        """Handle canvas drag for panning"""
        # Calculate movement
        dx = event.x - self.last_x
        dy = event.y - self.last_y

        # Scroll the canvas
        self.canvas.scan_dragto(event.x, event.y, gain=1)

        # Update last position
        self.last_x = event.x
        self.last_y = event.y

    def on_canvas_configure(self, event):
        """Handle canvas resize"""
        if self.pil_image:
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

def create_scroll_image_view(master) -> ScrollableImageView:
    """Create and configure a ScrollableImageView widget"""
    view = ScrollableImageView(master)
    view.pack(fill=tk.BOTH, expand=True)
    return view

def check_dependencies():
    """Check if required dependencies are installed and install them if needed"""
    dependencies = {
        'rembg': 'rembg[cli]',
        'onnxruntime': 'onnxruntime'
    }
    
    missing = []
    for package, install_name in dependencies.items():
        try:
            __import__(package)
        except ImportError:
            missing.append(install_name)
    
    return missing

def install_dependencies(parent_window):
    """Show dialog to install missing dependencies"""
    missing_deps = check_dependencies()
    
    if not missing_deps:
        return True
        
    dialog = tk.Toplevel(parent_window)
    dialog.title("Install Dependencies")
    dialog.geometry("400x200")
    dialog.transient(parent_window)
    dialog.grab_set()
    
    # Center the dialog
    dialog.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width() - dialog.winfo_width()) // 2
    y = parent_window.winfo_y() + (parent_window.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")
    
    ttk.Label(
        dialog,
        text="The following dependencies need to be installed:",
        wraplength=380
    ).pack(pady=10)
    
    deps_text = "\n".join([f"• {dep}" for dep in missing_deps])
    ttk.Label(dialog, text=deps_text).pack(pady=5)
    
    progress_var = tk.StringVar(value="")
    progress_label = ttk.Label(dialog, textvariable=progress_var)
    progress_label.pack(pady=5)
    
    def do_install():
        try:
            import subprocess
            import sys
            
            progress_var.set("Installing dependencies...")
            dialog.update()
            
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_deps, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            progress_var.set("Dependencies installed successfully!")
            install_btn.state(['disabled'])
            dialog.after(1500, dialog.destroy)
            return True
            
        except subprocess.CalledProcessError as e:
            progress_var.set(f"Error installing dependencies: {str(e)}")
            return False
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(side=tk.BOTTOM, pady=10)
    
    install_btn = ttk.Button(btn_frame, text="Install", command=do_install)
    install_btn.pack(side=tk.LEFT, padx=5)
    
    ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    dialog.wait_window()