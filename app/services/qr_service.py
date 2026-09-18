import io
import base64
import qrcode
from qrcode.image.styledpil import StyledPilImage

def generate_qr_base64(data_payload, box_size=8, border=2):
    """
    Generates a base64-encoded PNG data URI for the given string payload.
    Used for on-the-fly rendering in web pages and printable labels.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(str(data_payload))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"

def get_product_qr_data(product):
    """
    Returns standard payload for a product's QR code.
    Can be decoded by any warehouse handheld scanner or our web camera scanner.
    """
    return product.sku

def save_qr_image(data_payload, target_filepath, box_size=10, border=2):
    """
    Saves a generated QR code PNG file directly to disk in the specified filepath.
    Ensures the target directory exists.
    """
    import os
    os.makedirs(os.path.dirname(target_filepath), exist_ok=True)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(str(data_payload))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(target_filepath, format="PNG")
    return target_filepath
