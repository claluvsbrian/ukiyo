from flask import Flask, render_template, request, send_file
import qrcode
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Ensure QR directory exists
QR_FOLDER = 'static/qr'
os.makedirs(QR_FOLDER, exist_ok=True)

def cleanup_old_qr_files(folder, max_age_minutes=5):
    """Delete files older than max_age_minutes in the given folder."""
    now = datetime.now()
    print(f"Running cleanup at {now}")
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            age = (now - file_mtime).total_seconds() / 60
            print(f"File: {filename}, Modified: {file_mtime}, Age (min): {age:.2f}")
            if now - file_mtime > timedelta(minutes=max_age_minutes):
                try:
                    os.remove(filepath)
                    print(f"Deleted old QR file: {filepath}")
                except Exception as e:
                    print(f"Failed to delete {filepath}: {e}")

@app.route('/', methods=['GET', 'POST'])
def index():
    # Clean up old QR codes before processing
    cleanup_old_qr_files(QR_FOLDER, max_age_minutes=5)
    qr_img_path = None
    if request.method == 'POST':
        data = request.form.get('data')
        if data:
            filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(QR_FOLDER, filename)
            img = qrcode.make(data)
            img.save(filepath)
            # Return web path for template
            qr_img_path = f"{QR_FOLDER}/{filename}".replace("\\", "/")
    return render_template('index.html', qr_path=qr_img_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

