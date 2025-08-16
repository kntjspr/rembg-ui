# Background Remover

A Python GUI application that removes backgrounds from images using the [rembg](https://github.com/danielgatis/rembg) library.

## Features

- Drag and drop image loading
- Real-time preview
- Zoom and pan controls
- Standard keyboard shortcuts (Ctrl+O, Ctrl+S)
- Progress indication during processing
- Supports common image formats
- Exports with transparency (PNG)

## Requirements

- Python >=3.10, <3.14
- tkinter (usually comes with Python)
- Other dependencies are listed in requirements.txt

## Installation

1. Clone the repository
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Load an image either by:
   - Dragging and dropping an image file onto the window
   - Using File > Open (or Ctrl+O)
   - Using the "Select Image" button

3. Click "Remove Background" to process the image

4. Save the result using:
   - File > Save (or Ctrl+S)
   - The "Save" button

## Controls

- **Zoom**: Use the + and - buttons below each image preview
- **Pan**: Click and drag within the image preview area
- **Fit to Window**: Click the "Fit" button below the preview

## Supported Image Formats

Input formats:
- PNG
- JPEG
- BMP
- GIF (first frame only)

Output format:
- PNG (with transparency)