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
        
        # Initialize UI state
        self.batch_mode = False
        
        # Main container with modern padding
        self.main_container = ttk.Frame(self, style="Main.TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create the initial simple interface
        self.create_simple_interface()
        
        # Status bar with improved styling
        status_frame = ttk.Frame(self, style="Status.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar()
        self.status = ttk.Label(status_frame, textvariable=self.status_var, 
                              style="Status.TLabel", font=('TkDefaultFont', 9))
        self.status.pack(side=tk.LEFT, padx=15, pady=8)
        self.status_var.set("Ready to remove backgrounds from your images")

    def create_simple_interface(self):
        """Create the initial simple, clean interface"""
        # Clear any existing content
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Welcome section
        welcome_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        welcome_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Title and description with improved icons
        title_label = ttk.Label(welcome_frame, text="✂ Background Remover",
                               style="Title.TLabel")
        title_label.pack(pady=(20, 10))

        desc_label = ttk.Label(welcome_frame,
                              text="Remove backgrounds from your images automatically\nDrag & drop an image or click to browse",
                              style="Description.TLabel", justify=tk.CENTER)
        desc_label.pack(pady=(0, 20))

        # Main action area - large drop zone with improved styling
        self.drop_zone = ttk.Frame(self.main_container, style="DropZone.TFrame")
        self.drop_zone.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Drop zone content
        drop_content = ttk.Frame(self.drop_zone)
        drop_content.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Large icon with better Unicode symbol
        icon_label = ttk.Label(drop_content, text="⬆",
                              font=('Segoe UI', 64),
                              foreground='#3498db')
        icon_label.pack(pady=(0, 20))

        # Drop instruction with improved styling
        drop_label = ttk.Label(drop_content, text="Drop your image here",
                              style="DropText.TLabel")
        drop_label.pack(pady=(0, 15))

        # Or text with better spacing
        or_label = ttk.Label(drop_content, text="— or —",
                            style="Description.TLabel")
        or_label.pack(pady=(0, 20))

        # Browse button with improved icon - using tk.Button for better control
        self.browse_btn = tk.Button(drop_content, text="⊞ Choose Image",
                                   command=self.open_single_file,
                                   font=('Segoe UI', 11, 'bold'),
                                   bg='#3498db', fg='white',
                                   relief='raised', bd=1,
                                   padx=20, pady=12,
                                   cursor='hand2')
        self.browse_btn.pack(pady=(0, 20))

        # Batch mode toggle with improved layout
        batch_frame = ttk.Frame(drop_content)
        batch_frame.pack()

        ttk.Label(batch_frame, text="Need to process multiple images?",
                 style="Description.TLabel").pack()

        self.batch_toggle_btn = tk.Button(batch_frame, text="⚡ Switch to Batch Mode",
                                          command=self.toggle_batch_mode,
                                          font=('Segoe UI', 9, 'underline'),
                                          bg='white', fg='#3498db',
                                          relief='flat', bd=0,
                                          padx=8, pady=6,
                                          cursor='hand2')
        self.batch_toggle_btn.pack(pady=(8, 0))
        
        # Configure drop zone bindings
        self.configure_drop_zone()
    
    def create_batch_interface(self):
        """Create the batch processing interface"""
        # Clear any existing content
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Header with back button and improved styling
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Button(header_frame, text="← Back to Simple Mode",
                  command=self.toggle_batch_mode, style="Link.TButton").pack(side=tk.LEFT)

        ttk.Label(header_frame, text="⚡ Batch Processing Mode",
                 font=('Segoe UI', 16, 'bold'),
                 foreground='#2c3e50').pack(side=tk.LEFT, padx=(20, 0))

        # Main content area
        content = ttk.Frame(self.main_container)
        content.pack(fill=tk.BOTH, expand=True)

        # Left panel for queue with improved icon
        queue_frame = ttk.LabelFrame(content, text="⊞ Image Queue", style="Card.TLabelframe")
        queue_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=0)

        # Queue list with scrollbar and improved styling
        queue_list_frame = ttk.Frame(queue_frame)
        queue_list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.queue_list = tk.Listbox(queue_list_frame, width=35, selectmode=tk.EXTENDED,
                                   font=('Segoe UI', 9), relief='flat', borderwidth=1,
                                   bg='white', fg='#2c3e50', selectbackground='#3498db',
                                   selectforeground='white')
        queue_scrollbar = ttk.Scrollbar(queue_list_frame, orient=tk.VERTICAL, command=self.queue_list.yview)
        self.queue_list.configure(yscrollcommand=queue_scrollbar.set)

        self.queue_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Queue controls with improved icons
        queue_controls = ttk.Frame(queue_frame)
        queue_controls.pack(fill=tk.X, padx=15, pady=(0, 15))

        add_btn = tk.Button(queue_controls, text="+ Add Images", command=self.open_file,
                           font=('Segoe UI', 11, 'bold'),
                           bg='#3498db', fg='white',
                           relief='raised', bd=1,
                           padx=20, pady=12,
                           cursor='hand2')
        add_btn.pack(fill=tk.X, pady=(0, 8))

        control_row = ttk.Frame(queue_controls)
        control_row.pack(fill=tk.X)

        clear_btn = tk.Button(control_row, text="⌫ Clear", command=self.clear_queue,
                             font=('Segoe UI', 9),
                             bg='#95a5a6', fg='white',
                             relief='raised', bd=1,
                             padx=15, pady=10,
                             cursor='hand2')
        clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        remove_btn = tk.Button(control_row, text="✕ Remove", command=self.remove_selected,
                              font=('Segoe UI', 9),
                              bg='#95a5a6', fg='white',
                              relief='raised', bd=1,
                              padx=15, pady=10,
                              cursor='hand2')
        remove_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # Right side for previews and controls
        right_container = ttk.Frame(content)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Image preview frames with improved icons
        self.preview_frame = ttk.Frame(right_container)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Input preview with better icon
        input_frame = ttk.LabelFrame(self.preview_frame, text="⬇ Original", style="Card.TLabelframe")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.input_preview = create_scroll_image_view(input_frame)

        # Output preview with better icon
        output_frame = ttk.LabelFrame(self.preview_frame, text="⬆ Processed", style="Card.TLabelframe")
        output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))
        self.output_preview = create_scroll_image_view(output_frame)
        
        # Controls section
        self.create_controls_section(right_container)
    
    def create_processing_interface(self):
        """Create the interface shown during processing with improved visual design"""
        # Clear any existing content
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Center content with card styling
        center_frame = ttk.Frame(self.main_container, style="Card.TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Processing animation/icon with better styling
        ttk.Label(center_frame, text="⟳",
                 font=('Segoe UI', 72),
                 foreground='#3498db').pack(pady=(20, 25))

        # Processing text with improved typography
        ttk.Label(center_frame, text="Removing Background...",
                 font=('Segoe UI', 18, 'bold'),
                 foreground='#2c3e50').pack(pady=(0, 15))

        # Status text for more detailed feedback
        self.processing_status = tk.StringVar(value="Initializing...")
        ttk.Label(center_frame, textvariable=self.processing_status,
                 font=('Segoe UI', 10),
                 foreground='#7f8c8d').pack(pady=(0, 20))

        # Progress bar with improved styling
        self.progress = ttk.Progressbar(center_frame, mode='determinate',
                                       style="Custom.Horizontal.TProgressbar", length=350)
        self.progress.pack(pady=(0, 25))

        # Cancel button with improved styling
        self.cancel_btn = tk.Button(center_frame, text="✕ Cancel",
                                   command=self.cancel_processing,
                                   font=('Segoe UI', 9),
                                   bg='#e74c3c', fg='white',
                                   relief='raised', bd=1,
                                   padx=15, pady=10,
                                   cursor='hand2')
        self.cancel_btn.pack(pady=(0, 20))
    
    def create_result_interface(self):
        """Create the interface shown after processing is complete with improved design"""
        # Clear any existing content
        for widget in self.main_container.winfo_children():
            widget.destroy()

        # Header with success message
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 25))

        # Success icon and text
        success_container = ttk.Frame(header_frame)
        success_container.pack()

        ttk.Label(success_container, text="✓",
                 font=('Segoe UI', 24, 'bold'),
                 foreground='#27ae60').pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(success_container, text="Background Removed Successfully!",
                 style="Success.TLabel").pack(side=tk.LEFT)

        # Image comparison with improved layout
        comparison_frame = ttk.Frame(self.main_container)
        comparison_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))

        # Before image with better icon
        before_frame = ttk.LabelFrame(comparison_frame, text="⬇ Before", style="Card.TLabelframe")
        before_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        self.input_preview = create_scroll_image_view(before_frame)

        # After image with better icon
        after_frame = ttk.LabelFrame(comparison_frame, text="⬆ After", style="Card.TLabelframe")
        after_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        self.output_preview = create_scroll_image_view(after_frame)

        # Action buttons with improved layout and icons
        action_frame = ttk.Frame(self.main_container)
        action_frame.pack(fill=tk.X)

        # Primary actions with better spacing
        primary_frame = ttk.Frame(action_frame)
        primary_frame.pack(pady=(0, 20))

        self.save_btn = tk.Button(primary_frame, text="⬇ Save Image",
                                 command=self.save_image,
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#27ae60', fg='white',
                                 relief='raised', bd=1,
                                 padx=15, pady=10,
                                 cursor='hand2')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 20))

        process_another_btn = tk.Button(primary_frame, text="⟳ Process Another",
                                       command=self.reset_to_simple,
                                       font=('Segoe UI', 11, 'bold'),
                                       bg='#3498db', fg='white',
                                       relief='raised', bd=1,
                                       padx=20, pady=12,
                                       cursor='hand2')
        process_another_btn.pack(side=tk.LEFT)

        # Secondary actions with improved styling
        secondary_frame = ttk.Frame(action_frame)
        secondary_frame.pack()

        open_new_btn = tk.Button(secondary_frame, text="⊞ Open New Image",
                                command=self.open_single_file,
                                font=('Segoe UI', 9, 'underline'),
                                bg='white', fg='#3498db',
                                relief='flat', bd=0,
                                padx=8, pady=6,
                                cursor='hand2')
        open_new_btn.pack(side=tk.LEFT, padx=(0, 20))

        batch_mode_btn = tk.Button(secondary_frame, text="⚡ Switch to Batch Mode",
                                  command=self.toggle_batch_mode,
                                  font=('Segoe UI', 9, 'underline'),
                                  bg='white', fg='#3498db',
                                  relief='flat', bd=0,
                                  padx=8, pady=6,
                                  cursor='hand2')
        batch_mode_btn.pack(side=tk.LEFT)
    
    def create_controls_section(self, parent):
        """Create the controls section for batch mode with improved design"""
        controls_frame = ttk.LabelFrame(parent, text="⚙ Controls", style="Card.TLabelframe")
        controls_frame.pack(fill=tk.X)

        # Action buttons with improved layout
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, padx=20, pady=20)

        # Primary action button with better icon
        self.process_btn = tk.Button(action_frame, text="▶ Start Processing",
                                    command=self.process_image,
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#3498db', fg='white',
                                    relief='raised', bd=1,
                                    padx=20, pady=12,
                                    cursor='hand2')
        self.process_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Save button with improved icon
        self.save_btn = tk.Button(action_frame, text="⬇ Save All",
                                 command=self.save_image,
                                 font=('Segoe UI', 10, 'bold'),
                                 bg='#27ae60', fg='white',
                                 relief='raised', bd=1,
                                 padx=15, pady=10,
                                 cursor='hand2',
                                 state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Cancel button with better icon
        self.cancel_btn = tk.Button(action_frame, text="✕ Cancel",
                                   command=self.cancel_processing,
                                   font=('Segoe UI', 9),
                                   bg='#e74c3c', fg='white',
                                   relief='raised', bd=1,
                                   padx=15, pady=10,
                                   cursor='hand2',
                                   state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT)

        # Progress section with improved styling
        progress_frame = ttk.Frame(controls_frame)
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Label(progress_frame, text="Progress:",
                 font=('Segoe UI', 10, 'bold'),
                 foreground='#2c3e50').pack(anchor='w', pady=(0, 8))

        self.progress = ttk.Progressbar(progress_frame, mode='determinate',
                                       style="Custom.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X)

    def configure_styles(self):
        """Configure modern TTK styles with improved color scheme and visual hierarchy"""
        style = ttk.Style()

        # Modern color palette
        colors = {
            'primary': '#3498db',      # Blue
            'primary_dark': '#2980b9', # Darker blue
            'success': '#27ae60',      # Green
            'success_dark': '#229954', # Darker green
            'danger': '#e74c3c',       # Red
            'danger_dark': '#c0392b',  # Darker red
            'warning': '#f39c12',      # Orange
            'secondary': '#95a5a6',    # Gray
            'dark': '#2c3e50',         # Dark gray
            'light': '#ecf0f1',        # Light gray
            'white': '#ffffff',
            'border': '#bdc3c7',       # Light border
            'hover': '#e8f4fd',        # Light blue hover
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
            'text_muted': '#95a5a6'
        }

        # Configure button styles with simpler, more compatible approach
        style.configure("Primary.TButton",
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 12))

        style.configure("Secondary.TButton",
                       font=('Segoe UI', 9),
                       padding=(15, 10))

        style.configure("Success.TButton",
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 10))

        style.configure("Danger.TButton",
                       font=('Segoe UI', 9),
                       padding=(15, 10))

        style.configure("Link.TButton",
                       font=('Segoe UI', 9, 'underline'),
                       relief='flat',
                       borderwidth=0,
                       padding=(8, 6))

        # Configure frame styles with proper backgrounds
        style.configure("Main.TFrame",
                       relief='flat')

        style.configure("Card.TFrame",
                       relief='solid',
                       borderwidth=1,
                       padding=25)

        style.configure("DropZone.TFrame",
                       relief='solid',
                       borderwidth=2,
                       padding=50)

        style.configure("DropZoneHover.TFrame",
                       relief='solid',
                       borderwidth=2,
                       padding=50)

        style.configure("Status.TFrame",
                       relief='flat',
                       borderwidth=0)

        # Configure label styles with proper contrast
        style.configure("Title.TLabel",
                       foreground=colors['text_primary'],
                       font=('Segoe UI', 18, 'bold'))

        style.configure("Description.TLabel",
                       foreground=colors['text_secondary'],
                       font=('Segoe UI', 11))

        style.configure("DropText.TLabel",
                       foreground=colors['primary'],
                       font=('Segoe UI', 14, 'bold'))

        style.configure("Success.TLabel",
                       foreground=colors['success'],
                       font=('Segoe UI', 16, 'bold'))

        style.configure("Status.TLabel",
                       foreground=colors['text_secondary'],
                       padding=(15, 8),
                       font=('Segoe UI', 9))

        # Configure labelframe styles
        style.configure("Card.TLabelframe.Label",
                       font=('Segoe UI', 10, 'bold'),
                       foreground=colors['text_primary'])

        style.configure("Card.TLabelframe",
                       relief='solid',
                       borderwidth=1,
                       padding=15)

        # Configure progressbar style with modern appearance
        style.configure("Custom.Horizontal.TProgressbar",
                       thickness=30,
                       background=colors['primary'],
                       troughcolor=colors['light'],
                       borderwidth=0,
                       lightcolor=colors['primary'],
                       darkcolor=colors['primary'])

    def create_menu(self):
        """Create menu bar with improved keyboard shortcuts and accessibility"""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # File menu with comprehensive shortcuts
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu, underline=0)
        file_menu.add_command(label="Open Image...", command=self.open_single_file, accelerator="Ctrl+O", underline=0)
        file_menu.add_command(label="Add Images to Queue...", command=self.open_file, accelerator="Ctrl+Shift+O", underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Save Image", command=self.save_image, accelerator="Ctrl+S", underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="New Session", command=self.reset_to_simple, accelerator="Ctrl+N", underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit, accelerator="Ctrl+Q", underline=1)

        # View menu for mode switching
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu, underline=0)
        view_menu.add_command(label="Toggle Batch Mode", command=self.toggle_batch_mode, accelerator="Ctrl+B", underline=7)

        # Process menu
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Process", menu=process_menu, underline=0)
        process_menu.add_command(label="Start Processing", command=self.process_image, accelerator="F5", underline=0)
        process_menu.add_command(label="Cancel Processing", command=self.cancel_processing, accelerator="Esc", underline=0)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu, underline=0)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts, accelerator="F1", underline=0)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about, underline=0)

    def setup_bindings(self):
        """Setup keyboard shortcuts and accessibility bindings"""
        # File operations
        self.master.bind('<Control-o>', lambda e: self.open_single_file() if not self.batch_mode else self.open_file())
        self.master.bind('<Control-s>', lambda e: self.save_image())
        self.master.bind('<Control-n>', lambda e: self.reset_to_simple())

        # Mode switching
        self.master.bind('<Control-b>', lambda e: self.toggle_batch_mode())

        # Processing controls
        self.master.bind('<F5>', lambda e: self.process_image() if self.batch_mode else None)
        self.master.bind('<Escape>', lambda e: self.cancel_processing() if hasattr(self, 'cancel_btn') and not self.cancel_btn.instate(['disabled']) else None)

        # Navigation shortcuts
        self.master.bind('<Control-q>', lambda e: self.master.quit())
        self.master.bind('<F1>', lambda e: self.show_about())

        # Focus management for accessibility
        self.master.bind('<Tab>', self._handle_tab_navigation)
        self.master.bind('<Shift-Tab>', self._handle_shift_tab_navigation)

        # Make the main window focusable
        self.master.focus_set()

    def _handle_tab_navigation(self, event):
        """Handle Tab key for better keyboard navigation"""
        # Let the default Tab behavior work, but ensure proper focus management
        return None

    def _handle_shift_tab_navigation(self, event):
        """Handle Shift+Tab key for reverse navigation"""
        # Let the default Shift+Tab behavior work
        return None
    
    def configure_drop_zone(self):
        """Configure drag and drop for the drop zone with enhanced visual feedback"""
        if hasattr(self, 'drop_zone'):
            # Make drop zone clickable
            self.drop_zone.bind('<Button-1>', lambda e: self.open_single_file())

            # Enhanced visual feedback for hover and drag operations
            def on_enter(event):
                self.drop_zone.configure(style="DropZoneHover.TFrame")
                # Update status message for better user guidance
                self.status_var.set("Click to browse or drop your image here")

            def on_leave(event):
                self.drop_zone.configure(style="DropZone.TFrame")
                # Reset status message
                self.status_var.set("Ready to remove backgrounds from your images")

            # Bind hover events
            self.drop_zone.bind('<Enter>', on_enter)
            self.drop_zone.bind('<Leave>', on_leave)

            # Enhanced drag and drop feedback
            def on_drag_enter(event):
                self.drop_zone.configure(style="DropZoneHover.TFrame")
                self.status_var.set("Drop your image to start processing")
                return 'copy'

            def on_drag_leave(event):
                self.drop_zone.configure(style="DropZone.TFrame")
                self.status_var.set("Ready to remove backgrounds from your images")

            # Configure drag and drop events for better feedback
            self.master.dnd_bind('<<DragEnter>>', on_drag_enter)
            self.master.dnd_bind('<<DragLeave>>', on_drag_leave)
    
    def toggle_batch_mode(self):
        """Toggle between simple and batch processing modes"""
        self.batch_mode = not self.batch_mode
        
        if self.batch_mode:
            self.create_batch_interface()
            self.status_var.set("Batch mode - Add multiple images to process")
        else:
            self.create_simple_interface()
            self.status_var.set("Ready to remove backgrounds from your images")
    
    def reset_to_simple(self):
        """Reset to simple interface and clear state"""
        self.batch_mode = False
        self.input_image = None
        self.output_image = None
        self.processing_queue.clear()
        self.processed_images.clear()
        self.create_simple_interface()
        self.status_var.set("Ready to remove backgrounds from your images")
    
    def open_single_file(self):
        """Open a single file for simple mode"""
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.load_single_image(filename)
    
    def load_single_image(self, path):
        """Load a single image and switch to processing interface with validation"""
        try:
            # Validate file existence
            if not os.path.exists(path):
                messagebox.showerror("File Not Found", f"The file '{os.path.basename(path)}' could not be found.")
                return

            # Check file size
            file_size = os.path.getsize(path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                messagebox.showerror("File Too Large",
                                   f"The file is too large to process.\n"
                                   f"Maximum file size is 50MB.\n"
                                   f"Current file size: {file_size / (1024*1024):.1f}MB")
                return

            # Load and validate image
            with Image.open(path) as img:
                # Check image dimensions
                if img.width > 8000 or img.height > 8000:
                    result = messagebox.askyesno("Large Image",
                                               f"This image is very large ({img.width}x{img.height} pixels).\n"
                                               f"Processing may take a long time. Continue?")
                    if not result:
                        return

                # Load the image
                self.input_image = img.copy()

            self.status_var.set(f"Loaded: {os.path.basename(path)} ({self.input_image.width}x{self.input_image.height})")

            # Switch to processing interface
            self.create_processing_interface()

            # Start processing immediately
            self.process_single_image()

        except Exception as e:
            error_msg = self._get_user_friendly_error_message(str(e))
            messagebox.showerror("Failed to Load Image",
                               f"Could not load '{os.path.basename(path)}':\n{error_msg}")
            # Stay on the simple interface if loading fails
    
    def process_single_image(self):
        """Process a single image"""
        if not self.input_image:
            return
        
        self.cancelled = False
        
        def on_progress(value):
            if not self.cancelled:
                self.progress['value'] = value
                # Update processing status with more detailed feedback
                if hasattr(self, 'processing_status'):
                    if value < 30:
                        self.processing_status.set("Analyzing image...")
                    elif value < 60:
                        self.processing_status.set("Detecting objects...")
                    elif value < 90:
                        self.processing_status.set("Removing background...")
                    else:
                        self.processing_status.set("Finalizing...")
                self.update_idletasks()
        
        def on_complete(result):
            if not self.cancelled:
                self.output_image = result
                self.create_result_interface()
                
                # Set the images in the preview
                if hasattr(self, 'input_preview'):
                    self.input_preview.set_image(self.input_image)
                if hasattr(self, 'output_preview'):
                    self.output_preview.set_image(self.output_image)
                
                self.status_var.set("Background removed successfully!")
        
        def on_error(error):
            error_msg = self._get_user_friendly_error_message(str(error))
            messagebox.showerror("Processing Failed",
                               f"Failed to process the image:\n{error_msg}\n\n"
                               f"Please try again with a different image or check that the image is valid.")
            self.status_var.set("Processing failed - please try again")
            self.reset_to_simple()
        
        self.status_var.set("Processing image...")
        self.current_thread = process_image_async(
            self.input_image,
            on_complete,
            on_error,
            on_progress
        )

    def open_file(self):
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('All files', '*.*')
        )
        filenames = filedialog.askopenfilenames(filetypes=filetypes)
        for filename in filenames:
            self.add_to_queue(filename)

    def load_image(self, path):
        """Legacy method for batch mode compatibility"""
        try:
            self.input_image = Image.open(path)
            if hasattr(self, 'input_preview'):
                self.input_preview.set_image(self.input_image)
            if hasattr(self, 'process_btn'):
                self.process_btn.config(state='normal')
            self.status_var.set(f"Loaded: {os.path.basename(path)}")
            if hasattr(self, 'output_preview'):
                self.output_preview.clear()
            if hasattr(self, 'save_btn'):
                self.save_btn.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        
        if not self.batch_mode and len(files) == 1:
            # Single file in simple mode - process immediately
            self.load_single_image(files[0])
        elif not self.batch_mode and len(files) > 1:
            # Multiple files in simple mode - ask to switch to batch mode
            if messagebox.askyesno("Multiple Images", 
                                 "You dropped multiple images. Would you like to switch to batch mode to process them all?"):
                self.batch_mode = True
                self.create_batch_interface()
                for file in files:
                    self.add_to_queue(file)
            else:
                # Just process the first image
                self.load_single_image(files[0])
        else:
            # Batch mode - add all files to queue
            for file in files:
                self.add_to_queue(file)

    def process_image(self):
        # This method is only used for batch processing now
        # Single image processing uses process_single_image()
        
        if not self.batch_mode:
            return
            
        # Check if we have images to process
        if not self.processing_queue:
            messagebox.showwarning("Warning", "Please add images to the queue first")
            return
            
        if self.current_thread and self.current_thread.is_alive():
            return
        
        # For batch processing, ask for output directory first
        if not hasattr(self, 'output_directory'):
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
        self.process_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.progress['value'] = 0
        self.cancelled = False
        
        # Load the first image from queue
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
                if hasattr(self, 'output_preview'):
                    self.output_preview.set_image(self.output_image)
                if hasattr(self, 'save_btn'):
                    self.save_btn.config(state='normal')
                
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
            
        # For single image (simple mode)
        if not self.batch_mode and self.output_image:
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
        """Add image to processing queue with comprehensive validation"""
        try:
            # Check if file exists
            if not os.path.exists(path):
                messagebox.showerror("File Not Found", f"The file '{os.path.basename(path)}' could not be found.")
                return

            # Check file size (limit to 50MB)
            file_size = os.path.getsize(path)
            if file_size > 50 * 1024 * 1024:  # 50MB
                messagebox.showerror("File Too Large",
                                   f"The file '{os.path.basename(path)}' is too large.\n"
                                   f"Maximum file size is 50MB.\n"
                                   f"Current file size: {file_size / (1024*1024):.1f}MB")
                return

            # Validate image format and integrity
            with Image.open(path) as img:
                # Check image dimensions
                if img.width > 8000 or img.height > 8000:
                    result = messagebox.askyesno("Large Image",
                                               f"The image '{os.path.basename(path)}' is very large "
                                               f"({img.width}x{img.height} pixels).\n"
                                               f"Processing may take a long time. Continue?")
                    if not result:
                        return

                # Check if image is already in queue
                if path in self.processing_queue:
                    messagebox.showwarning("Duplicate Image",
                                         f"'{os.path.basename(path)}' is already in the queue.")
                    return

                # Add to queue
                self.processing_queue.append(path)
                self.queue_list.insert(tk.END, f"{os.path.basename(path)} ({img.width}x{img.height})")

                if hasattr(self, 'process_btn'):
                    self.process_btn.config(state='normal')

                self.status_var.set(f"Added to queue: {os.path.basename(path)} ({len(self.processing_queue)} images total)")

        except Exception as e:
            error_msg = self._get_user_friendly_error_message(str(e))
            messagebox.showerror("Invalid Image",
                               f"Failed to add '{os.path.basename(path)}':\n{error_msg}")

    def _get_user_friendly_error_message(self, error_str):
        """Convert technical error messages to user-friendly ones"""
        error_lower = error_str.lower()

        if "cannot identify image file" in error_lower:
            return "This file is not a supported image format.\nSupported formats: PNG, JPEG, BMP, GIF"
        elif "truncated" in error_lower or "incomplete" in error_lower:
            return "The image file appears to be corrupted or incomplete."
        elif "permission" in error_lower or "access" in error_lower:
            return "Cannot access the file. Please check file permissions."
        elif "memory" in error_lower or "out of memory" in error_lower:
            return "The image is too large to process. Try a smaller image."
        else:
            return f"An error occurred: {error_str}"

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
            self.process_btn.config(state='disabled')

    def remove_selected(self):
        selected = self.queue_list.curselection()
        if not selected:
            return
            
        # Remove from both queue and listbox (in reverse order to maintain indices)
        for index in reversed(selected):
            del self.processing_queue[index]
            self.queue_list.delete(index)
            
        if not self.processing_queue and not self.input_image:
            self.process_btn.config(state='disabled')

    def process_next(self):
        self.progress['value'] = 0
        if self.cancelled:
            self.status_var.set("Processing cancelled")
            self.cancel_btn.config(state='disabled')
            self.process_btn.configure(text="▶ Start Processing")
            self.process_btn.config(state='normal')
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
                        self.save_btn.config(state='normal')
                        
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
            self.cancel_btn.config(state='disabled')
            self.process_btn.configure(text="▶ Start Processing")
            self.process_btn.config(state='normal')
            # Reset batch processing state
            if hasattr(self, 'batch_total'):
                delattr(self, 'batch_total')
            
    def cancel_processing(self):
        self.cancelled = True
        self.status_var.set("Cancelling...")
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(state='disabled')
        
        # Return to appropriate interface
        if not self.batch_mode:
            self.reset_to_simple()
        else:
            # Reset batch processing state
            if hasattr(self, 'batch_total'):
                delattr(self, 'batch_total')
            if hasattr(self, 'process_btn'):
                self.process_btn.configure(text="▶ Start Processing")
                self.process_btn.config(state='normal')

    def show_shortcuts(self):
        """Show keyboard shortcuts help dialog"""
        shortcuts_text = """Keyboard Shortcuts:

File Operations:
• Ctrl+O - Open image (or add to queue in batch mode)
• Ctrl+S - Save processed image
• Ctrl+N - Start new session

View:
• Ctrl+B - Toggle batch mode

Processing:
• F5 - Start processing (batch mode)
• Esc - Cancel processing

Navigation:
• F1 - Show this help
• Ctrl+Q - Exit application
• Tab - Navigate between controls
• Shift+Tab - Navigate backwards"""

        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)

    def show_about(self):
        """Show about dialog with application information"""
        about_text = """Background Remover v2.0

A modern tool to automatically remove backgrounds from images using AI.

Features:
• Single image processing
• Batch processing mode
• Drag & drop support
• Multiple export formats
• Keyboard shortcuts

Built with Python, Tkinter, and rembg
Powered by machine learning models"""

        messagebox.showinfo("About Background Remover", about_text)
