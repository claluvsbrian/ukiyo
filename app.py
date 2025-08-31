from flask import Flask, render_template, request, send_file, send_from_directory, make_response
from flask.helpers import get_root_path
import qrcode
import os
import gzip
import io
from datetime import datetime, timedelta

app = Flask(__name__)

# Enable compression for better performance
@app.after_request
def compress_response(response):
    accept_encoding = request.headers.get('Accept-Encoding', '')
    
    if ('gzip' in accept_encoding.lower() and 
        response.status_code < 300 and 
        response.content_length is None and
        'Content-Encoding' not in response.headers):
        
        # Only compress text-based content
        if (response.content_type.startswith('text/') or 
            response.content_type.startswith('application/json') or
            response.content_type.startswith('application/javascript')):
            
            gzip_buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=gzip_buffer, mode='wb') as gzip_file:
                gzip_file.write(response.get_data())
            
            response.set_data(gzip_buffer.getvalue())
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(response.get_data())
    
    return response

# Security headers middleware
@app.after_request
def add_security_headers(response):
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://pagead2.googlesyndication.com https://www.google.com https://googleads.g.doubleclick.net; "
        "connect-src 'self' https://pagead2.googlesyndication.com; "
        "frame-src https://googleads.g.doubleclick.net; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    
    # HSTS (HTTP Strict Transport Security)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # X-Frame-Options (Clickjacking protection)
    response.headers['X-Frame-Options'] = 'DENY'
    
    # X-Content-Type-Options
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # X-XSS-Protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Cross-Origin Embedder Policy
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    
    # Cross-Origin Opener Policy
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    
    return response

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

@app.route('/ads.txt')
def ads():
    response = make_response(send_from_directory('.', 'ads.txt'))
    response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
    return response

# Optimized static file caching route
@app.route('/static/<path:filename>')
def static_files(filename):
    response = make_response(send_from_directory('static', filename))
    
    # Set appropriate cache headers based on file type
    if filename.endswith(('.css', '.js')):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        response.headers['Vary'] = 'Accept-Encoding'
    elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp')):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    elif filename.endswith('.json'):
        response.headers['Cache-Control'] = 'public, max-age=86400'
        response.headers['Content-Type'] = 'application/json'
    
    # Add ETag for better caching
    response.add_etag()
    return response.make_conditional(request)

@app.route('/robots.txt')
def robots():
    return '''User-agent: *
Allow: /
Sitemap: https://ukiyo.onrender.com/sitemap.xml''', 200, {'Content-Type': 'text/plain'}

@app.route('/manifest.json')
def manifest():
    response = make_response(send_from_directory('static', 'manifest.json'))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day
    return response

@app.route('/sitemap.xml')
def sitemap():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ukiyo.onrender.com/</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/blog</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/blog/qr-codes-business-guide</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/blog/qr-code-types-explained</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/blog/qr-code-security-best-practices</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/about</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/faq</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/contact</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/privacy-policy</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>quarterly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://ukiyo.onrender.com/terms-of-service</loc>
    <lastmod>2025-01-15</lastmod>
    <changefreq>quarterly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>''', 200, {'Content-Type': 'application/xml'}

# Blog and content pages for AdSense compliance
@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog/qr-codes-business-guide')
def blog_business_guide():
    return render_template('blog/business-guide.html')

@app.route('/blog/qr-code-types-explained')
def blog_qr_types():
    return render_template('blog/qr-types.html')

@app.route('/blog/qr-code-security-best-practices')
def blog_security():
    return render_template('blog/security.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms-of-service.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)