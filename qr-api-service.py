from flask import Flask, request, send_file, jsonify
from qrcodegen import QrCode
from io import BytesIO
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Static API Key (for simplicity, consider storing in environment variables for production)
# API_KEY = os.getenv("API_KEY", "your-secret-api-key")

# Access API key from environment variable
# API_KEY = os.getenv("API_KEY")

# Retrieve API key from environment variables
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY environment variable is not set!")

# Middleware to check API key
def require_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("x-api-key")
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/generate', methods=['POST'])
@require_api_key  # Protect this route with the API key check
def generate_qr():
    # Get the text and format from the request body
    text = request.json.get('text', '')
    response_format = request.json.get('format', 'png').lower()
    if not text:
        return jsonify({"error": "Text is required"}), 400
    if response_format not in {'png', 'svg'}:
        return jsonify({"error": "Invalid format. Use 'png' or 'svg'"}), 400

    # Generate QR Code
    qr = QrCode.encode_text(text, QrCode.Ecc.LOW)
    border = 4

    if response_format == 'png':
        # Convert QR Code to PNG
        size = qr.get_size() + border * 2
        png_image = BytesIO()
        png_image.write(b"P6\n%d %d\n255\n" % (size, size))
        for y in range(-border, qr.get_size() + border):
            for x in range(-border, qr.get_size() + border):
                color = b"\xff\xff\xff" if not qr.get_module(x, y) else b"\x00\x00\x00"
                png_image.write(color)
        png_image.seek(0)
        return send_file(png_image, mimetype='image/png')

    elif response_format == 'svg':
        # Convert QR Code to SVG
        svg_data = to_svg_str(qr, border)
        svg_response = BytesIO(svg_data.encode('utf-8'))
        return send_file(svg_response, mimetype='image/svg+xml')


def to_svg_str(qr: QrCode, border: int) -> str:
    """Converts the QR code to an SVG string."""
    if border < 0:
        raise ValueError("Border must be non-negative")
    parts = []
    for y in range(qr.get_size()):
        for x in range(qr.get_size()):
            if qr.get_module(x, y):
                parts.append(f"M{x+border},{y+border}h1v1h-1z")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {qr.get_size()+border*2} {qr.get_size()+border*2}" stroke="none">
    <rect width="100%" height="100%" fill="#FFFFFF"/>
    <path d="{" ".join(parts)}" fill="#000000"/>
</svg>
"""

if __name__ == '__main__':
    # Custom ASCII Art and Metadata
    app_name = "QR Code Service"
    version = "1.0.0"
    port = int(os.getenv("PORT", 5000))  # Default port is 5000
    host = os.getenv("HOST", "0.0.0.0")  # Default host

    # Print custom design on startup
    print(f"""
==============================================
        {app_name} - v{version}
==============================================

Running at:
    Local:   http://127.0.0.1:{port}
    Network: http://{host}:{port}

------------------------------------------------
   * Powered by Flask & Python
   * API Key Secured
   * Generate your QR Codes with ease!
------------------------------------------------
    """)

    # Start the Flask application
    app.run(host=host, port=port, debug=True)
