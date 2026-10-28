"""
Invisible Watermarking Service
Technique: Least Significant Bit (LSB) Steganography
Target: Lossless Image Formats (PNG)

How LSB Watermarking Works:
In digital images, each pixel consists of color channels (Red, Green, Blue, Alpha),
where each channel is an 8-bit byte from 0 to 255.
The least significant bit (the 1s place, 2^0) contributes minimal visual brightness (1/256th).
Altering this bit produces a change that is completely imperceptible to the human eye.
By replacing the LSB of consecutive pixel bytes with the bits of an encoded identifier string,
we embed an invisible watermark directly into the image structure.

Limitations:
- Must be stored in a lossless format like PNG.
- Lossy compression (e.g. converting to JPEG), downscaling, cropping, or color filtering
  will alter pixel values and degrade or destroy LSB data.
- This is a student prototype demonstrating steganographic concepts, not a forensic-grade DRM system.
"""

import os
from PIL import Image
from services.hashing import calculate_file_hash

START_DELIMITER = "<<IPE_START>>"
END_DELIMITER = "<<IPE_END>>"

def text_to_bits(text):
    """Convert a UTF-8 string to a list of bits (0s and 1s)."""
    bits = []
    byte_array = text.encode('utf-8')
    for byte in byte_array:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def bits_to_text(bits):
    """Convert a sequence of bits back into a UTF-8 string."""
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            break
        val = 0
        for bit in byte_bits:
            val = (val << 1) | bit
        bytes_list.append(val)
    try:
        return bytes(bytes_list).decode('utf-8', errors='ignore')
    except Exception:
        return ""

def embed_watermark(input_image_path, output_image_path, evidence_id, short_hash=""):
    """
    Embed an invisible watermark containing the evidence ID into a copy of the image.
    Saves the result as a lossless PNG.
    Returns:
        success (bool)
        watermark_sha256 (str)
        message (str)
    """
    try:
        payload = f"{START_DELIMITER}EVIDENCE_ID:{evidence_id}|HASH:{short_hash}{END_DELIMITER}"
        bits = text_to_bits(payload)
        num_bits = len(bits)

        with Image.open(input_image_path) as img:
            # Ensure RGB or RGBA mode
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'transparency' in img.info or img.mode == 'P' else 'RGB')
            else:
                img = img.copy()

            width, height = img.size
            raw_bytes = bytearray(img.tobytes())

            if num_bits > len(raw_bytes):
                return False, "", f"Image resolution ({width}x{height}) is too small to embed the watermark payload."

            for i in range(num_bits):
                raw_bytes[i] = (raw_bytes[i] & ~1) | bits[i]

            watermarked_img = Image.frombytes(img.mode, img.size, bytes(raw_bytes))

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            # Save strictly as lossless PNG to protect LSB fidelity
            watermarked_img.save(output_image_path, format='PNG', optimize=False)

        # Calculate the hash of the generated watermarked file
        watermark_sha256 = calculate_file_hash(output_image_path)
        return True, watermark_sha256, "Invisible watermark embedded successfully using LSB steganography."

    except Exception as e:
        return False, "", f"Watermark embedding failed: {str(e)}"

def extract_watermark(image_path):
    """
    Scan an image file and attempt to extract an embedded IPE watermark identifier.
    Returns:
        found (bool)
        evidence_id (str or None)
        details (str)
    """
    try:
        with Image.open(image_path) as img:
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
                
            raw_bytes = img.tobytes()
            # Sample up to the first 16,000 bytes (plenty for our marker and ID)
            sample_bytes = raw_bytes[:16000]
            extracted_bits = [b & 1 for b in sample_bytes]
            extracted_text = bits_to_text(extracted_bits)

            if START_DELIMITER in extracted_text and END_DELIMITER in extracted_text:
                start_pos = extracted_text.find(START_DELIMITER) + len(START_DELIMITER)
                end_pos = extracted_text.find(END_DELIMITER, start_pos)
                payload_content = extracted_text[start_pos:end_pos]

                # Extract Evidence ID
                evidence_id = None
                for part in payload_content.split('|'):
                    if part.startswith('EVIDENCE_ID:'):
                        evidence_id = part.replace('EVIDENCE_ID:', '').strip()

                if evidence_id:
                    return True, evidence_id, f"Detected watermark payload: '{payload_content}'"
                else:
                    return False, None, "Marker delimiters found, but evidence ID could not be parsed."
            else:
                return False, None, (
                    "No invisible watermark identifier detected. The image may be unmodified original, "
                    "or compression/resizing/editing may have disrupted the delicate LSB bits."
                )

    except Exception as e:
        return False, None, f"Watermark extraction error: {str(e)}"
