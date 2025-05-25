# Phostel

Sebuah Website repositori gambar dinamis yang memiliki performa yang sangat lambat.

## Reproduksi
Anda harus membuat lingkungan terisolasi. Package yang diperlukan untuk sistem anda ialah `python`,`pip`, dan `nodejs`.

Berikut Caranya membuat lingkungan yang terisolasi.
```
python3 -m venv venv
```

Untuk Linux/MacOS/Mirip-UNIX
```
source venv/bin/activate
```

Untuk Microsoft® Windows
```
venv\Scripts\activate.bat
```

Untuk memasang keperluan-keperluan website
```
pip install -r requirements.txt
```

Untuk menjalankan website dalam mode awakutu. Berada di port `5500`
```
python app.py
```

Untuk menjalankan website. Berada di port `8000`
```
npm run serve
```