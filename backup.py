from flask import Flask, request, render_template, redirect, url_for, render_template_string, send_from_directory, abort
import os
import sqlite3
from werkzeug.utils import secure_filename

# konfigurasi
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# apakah /static/uploads ada?
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# database judul, hastag, metadata gambar lainnya
DATABASE = 'images.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # buat tabel jika tiada, dengan judul kolom
    c.execute('''CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    title TEXT,
                    filepath TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    conn.commit()
    conn.close()

# panggil database
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, filename, title FROM images ORDER BY upload_date DESC")
    images = [{'id': row[0], 'filename': row[1], 'title': row[2]} for row in c.fetchall()]
    conn.close()
    
    # bangun html untuk menampilkan gambar
    return render_template('index.html', images=images)

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/<int:item_id>')
def images(item_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT filename, title FROM images WHERE id = ?", (item_id,))
    row = c.fetchone()
    conn.close()

    if row is None:
        return "404 Not Found", 404

    image = {'filename': row[0], 'title': row[1]}
    return render_template('gambar.html', image=image)


@app.route('/post', methods=['POST'])
def post():
    if 'image' not in request.files:
        return "No file part", 400
    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    # ambil judul gambar
    title = request.form.get('title', '').strip()

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # tambahkan data judul ke database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO images (filename, title, filepath) VALUES (?, ?, ?)",
                  (filename, title, file_path))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory('static/uploads', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

# if __name__ == '__main__':
#     app.run(debug=True)
