import hashlib

def calculate_stream_hash(stream):
    """
    Calculate the SHA-256 cryptographic hash of a binary stream (e.g. uploaded file).
    Reads the stream in 64KB chunks to efficiently handle large files without high memory usage.
    Resets the stream position back to 0 so the file can still be saved afterwards.
    """
    hasher = hashlib.sha256()
    while True:
        chunk = stream.read(65536)
        if not chunk:
            break
        hasher.update(chunk)
    stream.seek(0)
    return hasher.hexdigest().lower()

def calculate_file_hash(filepath):
    """
    Calculate the SHA-256 cryptographic hash of a file on disk.
    Returns lowercase hexadecimal string (64 characters).
    """
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest().lower()

def compare_hashes(registered_hash, uploaded_hash):
    """
    Compare two SHA-256 hashes.
    Returns:
        is_match (bool): True if hashes are identical.
        analysis (str): Plain-English explanation suitable for beginners and presentations.
    """
    reg = (registered_hash or '').strip().lower()
    upl = (uploaded_hash or '').strip().lower()

    if not reg or not upl:
        return False, "Invalid or empty hash provided for comparison."

    if reg == upl:
        return True, (
            "CRYPTOGRAPHIC MATCH CONFIRMED: The uploaded file has the exact same SHA-256 digital fingerprint "
            "as the registered original. Every single bit in this file is identical to the version registered "
            "in the evidence vault."
        )
    else:
        return False, (
            "INTEGRITY MISMATCH DETECTED: The uploaded file has a different SHA-256 digital fingerprint "
            "from the registered original. Due to the SHA-256 avalanche effect, even modifying a single pixel, "
            "metadata tag, or color value produces an entirely different hash. Note: A mismatch confirms the "
            "file is not bit-for-bit identical, but does not alone constitute legal proof of unauthorized copying or infringement."
        )
