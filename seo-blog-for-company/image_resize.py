from PIL import Image
import os

def resize_and_compress_local_image(input_path, output_path, size=(1024, 1024), quality=80):
    """
    Resize and compress a local image, showing size before and after.
    """
    try:
        # Original size in KB
        original_size_kb = os.path.getsize(input_path) / 1024
        print(f"Original image size: {original_size_kb:.2f} KB")

        # Open image
        img = Image.open(input_path)

        # Resize using the correct resampling method
        img = img.resize(size, Image.Resampling.LANCZOS)

        # Convert if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Save compressed image
        img.save(output_path, format="JPEG", quality=quality, optimize=True)

        # New size in KB
        compressed_size_kb = os.path.getsize(output_path) / 1024
        print(f"Compressed image saved to {output_path}")
        print(f"Compressed image size: {compressed_size_kb:.2f} KB")

    except Exception as e:
        print(f"Error processing image: {e}")
