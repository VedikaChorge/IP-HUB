import os
import io
import base64

try:
    import qrcode
    from PIL import Image
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

def generate_qr_code_file(data_url, output_path):
    """
    Generate a QR code image file for the given verification URL.
    Returns:
        success (bool)
        filepath (str)
        error_message (str or None)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if HAS_QRCODE:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=2,
            )
            qr.add_data(data_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
            img.save(output_path)
            return True, output_path, None
        except Exception as e:
            return False, None, str(e)
    else:
        # Fallback: create an SVG representation or placeholder if qrcode package is missing
        return False, None, "QR code library not loaded yet."

def get_qr_base64(data_url):
    """
    Generate base64 encoded PNG data URI of the QR code for instant inline HTML rendering.
    """
    if not HAS_QRCODE:
        return None

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(data_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None
