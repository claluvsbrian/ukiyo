from flask import Flask, render_template, request, send_file
import qrcode
import os
from datetime import datetime

app = Flask(__name__)

# Ensure QR directory exists
QR_FOLDER = 'static/qr'
os.makedirs(QR_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    qr_img_path = None
    if request.method == 'POST':
        data = request.form.get('data')
        if data:
            filename = f"qr_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(QR_FOLDER, filename)
            img = qrcode.make(data)
            img.save(filepath)
            qr_img_path = filepath
    return render_template('index.html', qr_path=qr_img_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

