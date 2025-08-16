import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
from image_processor import remove_background, process_image_async
from utils import create_scroll_image_view

class BackgroundRemoverApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.drop_target_register(DND_FILES)
        self.master.dnd_bind('<<Drop>>', self.handle_drop)
        self.master = master
        self.input_image = None
        self.output_image = None
        self.processing_queue = []
        self.processed_images = []  # Store processed images for batch saving
        self.current_thread = None
        self.cancelled = False
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        # Configure modern styling
        self.configure_styles()
        
        # Create menu bar
        self.create_menu()
        
        # Main content area with better padding
        content = ttk.Frame(self, style="Content.TFrame")
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for queue with improved styling
        queue_frame = ttk.LabelFrame(content, text="📁 Processing Queue", style="Queue.TLabelframe")
        queue_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0)
        
        # Add drag and drop hint
        hint_label = ttk.Label(queue_frame, text="Drag & drop images here or use 'Open' button", 
                              font=('TkDefaultFont', 8), foreground='gray')
        hint_label.pack(pady=(5, 0))
        
        # Queue list with scrollbar
        queue_list_frame = ttk.Frame(queue_frame)
        queue_list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self.queue_list = tk.Listbox(queue_list_frame, width=35, selectmode=tk.EXTENDED,
                                   font=('TkDefaultFont', 9), relief='flat', borderwidth=1)
        queue_scrollbar = ttk.Scrollbar(queue_list_frame, orient=tk.VERTICAL, command=self.queue_list.yview)
        self.queue_list.configure(yscrollcommand=queue_scrollbar.set)
        
        self.queue_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Queue controls with better layout
        queue_controls = ttk.Frame(queue_frame)
        queue_controls.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        ttk.Button(queue_controls, text="🗑️ Clear All", command=self.clear_queue, 
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(queue_controls, text="❌ Remove Selected", command=self.remove_selected,
                  style="Secondary.TButton").pack(side=tk.LEFT)
        
        # Right side container for previews and controls
        right_container = ttk.Frame(content)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Image preview frames with improved layout
        self.preview_frame = ttk.Frame(right_container)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Input preview
        input_frame = ttk.LabelFrame(self.preview_frame, text="📥 Original Image", style="Preview.TLabelframe")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.input_preview = create_scroll_image_view(input_frame)
        
        # Output preview
        output_frame = ttk.LabelFrame(self.preview_frame, text="📤 Processed Image", style="Preview.TLabelframe")
        output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.output_preview = create_scroll_image_view(output_frame)
        
        # Controls section with better styling
        controls_frame = ttk.LabelFrame(right_container, text="🎛️ Controls", style="Controls.TLabelframe")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons row
        action_buttons = ttk.Frame(controls_frame)
        action_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        # Primary action button (Start)
        self.process_btn = ttk.Button(action_buttons, text="🚀 Start Processing", command=self.process_image,
                                    style="Primary.TButton")
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Secondary buttons
        ttk.Button(action_buttons, text="📁 Open Images", command=self.open_file,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ttk.Button(action_buttons, text="💾 Save Results", command=self.save_image,
                                 style="Success.TButton")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.save_btn.state(['disabled'])
        
        # Cancel button (shown when processing)
        self.cancel_btn = ttk.Button(action_buttons, text="⛔ Cancel", command=self.cancel_processing,
                                   style="Danger.TButton")
        self.cancel_btn.pack(side=tk.RIGHT)
        self.cancel_btn.state(['disabled'])
        
        # Progress section
        progress_frame = ttk.Frame(controls_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(progress_frame, text="Progress:", font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', style="Custom.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        # Status bar with improved styling
        status_frame = ttk.Frame(self, style="Status.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar()
        self.status = ttk.Label(status_frame, textvariable=self.status_var, 
                              style="Status.TLabel", font=('TkDefaultFont', 9))
        self.status.pack(side=tk.LEFT, padx=10, pady=5)
        self.status_var.set("Ready - Load images to get started")

    def configure_styles(self):
        """Configure modern TTK styles"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure("Primary.TButton", font=('TkDefaultFont', 10, 'bold'))
        style.configure("Secondary.TButton", font=('TkDefaultFont', 9))
        style.configure("Success.TButton", font=('TkDefaultFont', 9))
        style.configure("Danger.TButton", font=('TkDefaultFont', 9))
        
        # Configure frame styles
        style.configure("Content.TFrame", relief='flat')
        style.configure("Status.TFrame", relief='sunken', borderwidth=1)
        
        # Configure label styles
        style.configure("Status.TLabel", background='lightgray')
        
        # Configure labelframe styles
        style.configure("Queue.TLabelframe.Label", font=('TkDefaultFont', 10, 'bold'))
        style.configure("Preview.TLabelframe.Label", font=('TkDefaultFont', 10, 'bold'))
        style.configure("Controls.TLabelframe.Label", font=('TkDefaultFont', 10, 'bold'))
        
        # Configure progressbar style
        style.configure("Custom.Horizontal.TProgressbar", thickness=20)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_bindings(self):
        # Keyboard shortcuts
        self.master.bind('<Control-o>', lambda e: self.open_file())
        self.master.bind('<Control-s>', lambda e: self.save_image())
        
        # Setup keyboard shortcuts

    def open_file(self):
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('All files', '*.*')
        )
        filenames = filedialog.askopenfilenames(filetypes=filetypes)
        for filename in filenames:
            self.add_to_queue(filename)

    def load_image(self, path):
        try:
            self.input_image = Image.open(path)
            self.input_preview.set_image(self.input_image)
            self.process_btn.state(['!disabled'])
            self.status_var.set(f"Loaded: {os.path.basename(path)}")
            self.output_preview.clear()
            self.save_btn.state(['disabled'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        for file in files:
            self.add_to_queue(file)

    def process_image(self):
        # Check if we have images to process
        if not self.input_image and not self.processing_queue:
            messagebox.showwarning("Warning", "Please load an image first")
            return
            
        if self.current_thread and self.current_thread.is_alive():
            return
        
        # For batch processing, ask for output directory first
        if self.processing_queue and not hasattr(self, 'output_directory'):
            self.output_directory = filedialog.askdirectory(
                title="Select Directory to Save Processed Images"
            )
            if not self.output_directory:
                return  # User cancelled
            
        # Initialize batch processing only once at the start
        if not hasattr(self, 'batch_total'):
            self.batch_total = len(self.processing_queue)
            self.batch_current = 0
            self.processed_files = []  # Track processed file names
            
        self.process_btn.configure(text="⏳ Processing...")
        self.process_btn.state(['disabled'])
        self.cancel_btn.state(['!disabled'])
        self.progress['value'] = 0
        self.cancelled = False
        
        # If we have a queue but no current image, load the first one
        if self.processing_queue and not self.input_image:
            self._load_next_from_queue()
        
        def on_progress(value):
            if not self.cancelled:
                # Calculate overall progress for batch
                batch_progress = (self.batch_current / self.batch_total) * 100
                individual_progress = (value / 100) * (100 / self.batch_total)
                total_progress = batch_progress + individual_progress
                self.progress['value'] = min(total_progress, 100)
                self.update_idletasks()
        
        def on_complete(result):
            if not self.cancelled:
                self.output_image = result
                self.processed_images.append(result)
                self.output_preview.set_image(self.output_image)
                self.save_btn.state(['!disabled'])
                
                # Auto-save for batch processing
                if hasattr(self, 'output_directory') and self.output_directory:
                    self._auto_save_image(result)
                
                self.batch_current += 1
                
                # Update status with batch progress
                if self.batch_total > 1:
                    self.status_var.set(f"Processed {self.batch_current} of {self.batch_total} images")
                else:
                    self.status_var.set("Background removed successfully")
                
                self.process_next()
        
        def on_error(error):
            messagebox.showerror("Error", f"Failed to process image: {str(error)}")
            self.status_var.set("Processing failed")
            self.batch_current += 1
            self.process_next()
        
        # Show current processing status
        if self.batch_total > 1:
            self.status_var.set(f"Processing image {self.batch_current + 1} of {self.batch_total}...")
        else:
            self.status_var.set("Processing...")
            
        self.current_thread = process_image_async(
            self.input_image,
            on_complete,
            on_error,
            on_progress
        )

    def save_image(self):
        if not self.output_image and len(self.processed_images) == 0:
            messagebox.showwarning("Warning", "No processed images to save")
            return
            
        # For single image
        if self.output_image and not self.processing_queue:
            self._save_single_image()
        # For batch saving
        else:
            self._save_batch_images()
    
    def _save_single_image(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ],
            title="Save Processed Image"
        )
        
        if filename:
            try:
                # Convert to RGB if saving as JPEG
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    # Create a white background for JPEG
                    rgb_image = Image.new('RGB', self.output_image.size, (255, 255, 255))
                    rgb_image.paste(self.output_image, mask=self.output_image.split()[-1])
                    rgb_image.save(filename, quality=95)
                else:
                    self.output_image.save(filename)
                    
                self.status_var.set(f"✅ Saved: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    def _auto_save_image(self, image, original_path=None):
        """Automatically save processed image to the selected output directory"""
        try:
            if not hasattr(self, 'output_directory') or not self.output_directory:
                return
            
            # Generate filename based on original image name or current count
            if original_path:
                # Use original filename with "_processed" suffix
                original_name = os.path.splitext(os.path.basename(original_path))[0]
                filename = f"{original_name}_processed.png"
            else:
                # Fallback to numbered naming
                filename = f"processed_{self.batch_current + 1}.png"
            
            # Full path for saving
            save_path = os.path.join(self.output_directory, filename)
            
            # Handle duplicate filenames by adding a counter
            counter = 1
            base_path = save_path
            while os.path.exists(save_path):
                name, ext = os.path.splitext(base_path)
                save_path = f"{name}_{counter}{ext}"
                counter += 1
            
            # Save the image
            image.save(save_path)
            
            # Track saved files
            if not hasattr(self, 'auto_saved_files'):
                self.auto_saved_files = []
            self.auto_saved_files.append(save_path)
            
            # Update status to show auto-save
            filename_only = os.path.basename(save_path)
            if hasattr(self, 'batch_total') and self.batch_total > 1:
                self.status_var.set(f"Auto-saved: {filename_only} ({self.batch_current + 1}/{self.batch_total})")
            else:
                self.status_var.set(f"Auto-saved: {filename_only}")
                
        except Exception as e:
            print(f"Auto-save failed: {str(e)}")  # Log error but don't interrupt processing

    def _save_batch_images(self):
        # Create a custom dialog for batch save options
        dialog = tk.Toplevel(self.master)
        dialog.title("Batch Save Options")
        dialog.geometry("400x300")
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - dialog.winfo_width()) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Directory selection
        ttk.Label(dialog, text="Save Location:", font=('TkDefaultFont', 10, 'bold')).pack(pady=(10, 5))
        
        dir_frame = ttk.Frame(dialog)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.selected_dir = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.selected_dir, width=50)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def browse_directory():
            directory = filedialog.askdirectory(title="Select Directory to Save Images")
            if directory:
                self.selected_dir.set(directory)
        
        ttk.Button(dir_frame, text="Browse", command=browse_directory).pack(side=tk.RIGHT)
        
        # Naming pattern
        ttk.Label(dialog, text="File Naming:", font=('TkDefaultFont', 10, 'bold')).pack(pady=(15, 5))
        
        naming_frame = ttk.Frame(dialog)
        naming_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.naming_pattern = tk.StringVar(value="processed_{index}")
        ttk.Label(naming_frame, text="Pattern:").pack(side=tk.LEFT)
        pattern_entry = ttk.Entry(naming_frame, textvariable=self.naming_pattern, width=30)
        pattern_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(dialog, text="Use {index} for numbering (e.g., image_{index}.png)", 
                 font=('TkDefaultFont', 8), foreground='gray').pack(pady=(0, 10))
        
        # File format selection
        ttk.Label(dialog, text="File Format:", font=('TkDefaultFont', 10, 'bold')).pack(pady=(5, 5))
        
        format_frame = ttk.Frame(dialog)
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_format = tk.StringVar(value="PNG")
        ttk.Radiobutton(format_frame, text="PNG (with transparency)", variable=self.file_format, 
                       value="PNG").pack(anchor='w')
        ttk.Radiobutton(format_frame, text="JPEG (white background)", variable=self.file_format, 
                       value="JPEG").pack(anchor='w')
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        def save_batch():
            directory = self.selected_dir.get()
            if not directory:
                messagebox.showwarning("Warning", "Please select a directory")
                return
                
            if not os.path.exists(directory):
                messagebox.showerror("Error", "Selected directory does not exist")
                return
            
            pattern = self.naming_pattern.get()
            file_format = self.file_format.get()
            
            try:
                saved_count = 0
                for i, img in enumerate(self.processed_images):
                    # Generate filename
                    if "{index}" in pattern:
                        base_name = pattern.replace("{index}", str(i + 1))
                    else:
                        base_name = f"{pattern}_{i + 1}"
                    
                    # Add extension
                    if file_format == "PNG":
                        filename = os.path.join(directory, f"{base_name}.png")
                        img.save(filename)
                    else:  # JPEG
                        filename = os.path.join(directory, f"{base_name}.jpg")
                        # Convert to RGB with white background
                        rgb_image = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_image.paste(img, mask=img.split()[-1])
                        rgb_image.save(filename, quality=95)
                    
                    saved_count += 1
                
                self.status_var.set(f"✅ Saved {saved_count} images to {os.path.basename(directory)}")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save images: {str(e)}")
        
        ttk.Button(button_frame, text="💾 Save All", command=save_batch,
                  style="Success.TButton").pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy,
                  style="Secondary.TButton").pack(side=tk.RIGHT)

    def add_to_queue(self, path):
        try:
            # Validate image before adding to queue
            Image.open(path)
            self.processing_queue.append(path)
            self.queue_list.insert(tk.END, os.path.basename(path))
            self.process_btn.state(['!disabled'])
            self.status_var.set(f"Added to queue: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add image: {str(e)}")

    def _load_next_from_queue(self):
        """Load the next image from the processing queue"""
        if self.processing_queue:
            next_image_path = self.processing_queue[0]  # Don't pop yet, will be done in process_next
            try:
                self.input_image = Image.open(next_image_path)
                self.input_preview.set_image(self.input_image)
                self.output_preview.clear()
                self.status_var.set(f"Loaded from queue: {os.path.basename(next_image_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image from queue: {str(e)}")
                # Remove the problematic image and try the next one
                self.processing_queue.pop(0)
                self.queue_list.delete(0)
                self._load_next_from_queue()

    def clear_queue(self):
        if not self.cancelled and self.current_thread and self.current_thread.is_alive():
            if messagebox.askyesno("Warning", "Processing in progress. Cancel and clear queue?"):
                self.cancel_processing()
            else:
                return
                
        self.processing_queue.clear()
        self.queue_list.delete(0, tk.END)
        self.status_var.set("Queue cleared")
        if not self.input_image:
            self.process_btn.state(['disabled'])

    def remove_selected(self):
        selected = self.queue_list.curselection()
        if not selected:
            return
            
        # Remove from both queue and listbox (in reverse order to maintain indices)
        for index in reversed(selected):
            del self.processing_queue[index]
            self.queue_list.delete(index)
            
        if not self.processing_queue and not self.input_image:
            self.process_btn.state(['disabled'])

    def process_next(self):
        self.progress['value'] = 0
        if self.cancelled:
            self.status_var.set("Processing cancelled")
            self.cancel_btn.state(['disabled'])
            self.process_btn.configure(text="🚀 Start Processing")
            self.process_btn.state(['!disabled'])
            # Reset batch processing state
            if hasattr(self, 'batch_total'):
                delattr(self, 'batch_total')
            return

        if len(self.processing_queue) > 0:
            next_image_path = self.processing_queue.pop(0)
            self.queue_list.delete(0)
            
            try:
                self.input_image = Image.open(next_image_path)
                self.input_preview.set_image(self.input_image)
                self.output_preview.clear()
                self.status_var.set(f"Processing: {os.path.basename(next_image_path)}")
                
                # Process the next image directly without calling process_image()
                def on_progress(value):
                    if not self.cancelled:
                        # Calculate overall progress for batch
                        if hasattr(self, 'batch_total') and self.batch_total > 0:
                            batch_progress = (self.batch_current / self.batch_total) * 100
                            individual_progress = (value / 100) * (100 / self.batch_total)
                            total_progress = batch_progress + individual_progress
                            self.progress['value'] = min(total_progress, 100)
                        else:
                            self.progress['value'] = value
                        self.update_idletasks()
                
                def on_complete(result):
                    if not self.cancelled:
                        self.output_image = result
                        self.processed_images.append(result)
                        self.output_preview.set_image(self.output_image)
                        self.save_btn.state(['!disabled'])
                        
                        # Auto-save for batch processing
                        if hasattr(self, 'output_directory') and self.output_directory:
                            self._auto_save_image(result, next_image_path)
                        
                        self.batch_current += 1
                        
                        # Update status with batch progress
                        if hasattr(self, 'batch_total') and self.batch_total > 1:
                            self.status_var.set(f"Processed {self.batch_current} of {self.batch_total} images")
                        else:
                            self.status_var.set("Background removed successfully")
                        
                        # Continue to next image
                        self.process_next()
                
                def on_error(error):
                    messagebox.showerror("Error", f"Failed to process image: {str(error)}")
                    self.status_var.set("Processing failed")
                    self.batch_current += 1
                    self.process_next()
                
                # Show current processing status
                if hasattr(self, 'batch_total') and self.batch_total > 1:
                    self.status_var.set(f"Processing image {self.batch_current + 1} of {self.batch_total}...")
                else:
                    self.status_var.set("Processing...")
                    
                self.current_thread = process_image_async(
                    self.input_image,
                    on_complete,
                    on_error,
                    on_progress
                )
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")
                self.batch_current += 1
                self.process_next()
        else:
            self.status_var.set("All images processed")
            self.cancel_btn.state(['disabled'])
            self.process_btn.configure(text="🚀 Start Processing")
            self.process_btn.state(['!disabled'])
            # Reset batch processing state
            if hasattr(self, 'batch_total'):
                delattr(self, 'batch_total')
            
    def cancel_processing(self):
        self.cancelled = True
        self.status_var.set("Cancelling...")
        self.cancel_btn.state(['disabled'])

    def show_about(self):
        messagebox.showinfo(
            "About Background Remover",
            "A simple tool to remove backgrounds from images\n\n" +
            "Built with Python, Tkinter, and rembg"
        )
