from rembg import remove
import PIL
from PIL import Image
import threading
from typing import Union, Callable

def remove_background(
    image: Union[PIL.Image.Image, bytes],
    progress_callback: Callable[[int], None] = None
) -> PIL.Image.Image:
    """
    Remove the background from an image using rembg library.
    
    Args:
        image: PIL Image object or bytes containing the image data
        progress_callback: Optional callback function to report progress (0-100)
    
    Returns:
        PIL Image object with background removed
    """
    if isinstance(image, PIL.Image.Image):
        # Convert PIL Image to bytes
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Process the image
        output = remove(image)
        
        if progress_callback:
            progress_callback(100)
            
        return output
    else:
        raise ValueError("Input must be a PIL Image object")

def process_image_async(
    image: PIL.Image.Image,
    on_complete: Callable[[PIL.Image.Image], None],
    on_error: Callable[[Exception], None],
    progress_callback: Callable[[int], None] = None
) -> threading.Thread:
    """
    Process image in a background thread to keep UI responsive.
    
    Args:
        image: PIL Image to process
        on_complete: Callback function to handle the processed image
        on_error: Callback function to handle any errors
        progress_callback: Optional callback function to report progress
    
    Returns:
        Thread object that is processing the image
    """
    def process_thread():
        try:
            result = remove_background(image, progress_callback)
            on_complete(result)
        except Exception as e:
            on_error(e)
    
    thread = threading.Thread(target=process_thread)
    thread.daemon = True
    thread.start()
    return thread