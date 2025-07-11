from flask import Flask, render_template, request, redirect, url_for, flash, session
from db.connection import get_db_connection
from functools import wraps
import re
from werkzeug.utils import secure_filename
import os

import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ==================== MIDDLEWARE: LOGIN ADMIN ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Silakan login terlebih dahulu.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== USER VIEWS ====================
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM produk')
    produk = cursor.fetchall()

    cursor.execute('SELECT * FROM best_seller')
    best_seller = cursor.fetchall()
    
    cursor.execute('SELECT * FROM menu_image')
    brosur = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view/user/index.html',brosur=brosur, produk=produk, best_seller=best_seller)



@app.route('/menu')
def menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nama, harga, deskripsi, gambar FROM produk")
    produk_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view/user/menu.html', produk_list=produk_list)

@app.route('/about')
def about():
    return render_template('view/user/about.html')

# ==================== ADMIN LOGIN ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Dummy login
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            flash('Berhasil login sebagai admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah.', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('Berhasil logout.', 'success')
    return redirect(url_for('admin_login'))

# ==================== ADMIN DASHBOARD ====================
# gambar_input = request.form['gambar']


# ==================== KONVERSI LINK GOOGLE DRIVE ====================
def convert_drive_link(link, mode='thumbnail'):
    """
    Mengonversi berbagai format link Google Drive ke format embed/thumbnail.
    mode: 'thumbnail' atau 'view'
    """
    if not link:
        return ""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', link) or re.search(r'[?&]id=([a-zA-Z0-9_-]+)', link)
    if match:
        file_id = match.group(1)
        if mode == 'view':
            return f"https://drive.google.com/uc?export=view&id={file_id}"
        return f"https://drive.google.com/thumbnail?id={file_id}"
    return link

# ==================== DASHBOARD ADMIN ====================
@app.route('/admin')
@login_required
def admin_dashboard():
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM produk")
    total_produk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM best_seller")
    total_best_seller = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        'admin/admin_dashboard.html',
        total_produk=total_produk,
        total_best_seller=total_best_seller
    )

# ==================== LIST PRODUK ====================
@app.route('/admin/produk')
@login_required
def admin_produk():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produk")
    daftar_produk = cursor.fetchall()

    for produk in daftar_produk:
        print(f"Gambar produk '{produk['nama']}': {produk['gambar']}")

    cursor.close()
    conn.close()
    return render_template('admin/produk/admin_produk.html', daftar_produk=daftar_produk)

# ==================== TAMBAH PRODUK ====================
@app.route('/admin/produk/tambah', methods=['GET', 'POST'])
@login_required
def tambah_produk():
    if request.method == 'POST':
        nama = request.form['nama']
        harga = request.form['harga']
        deskripsi = request.form['deskripsi']
        gambar_input = request.form['gambar']

        gambar = convert_drive_link(gambar_input, mode='thumbnail')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO produk (nama, harga, deskripsi, gambar) VALUES (%s, %s, %s, %s)",
            (nama, harga, deskripsi, gambar)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Produk berhasil ditambahkan.', 'success')
        return redirect(url_for('admin_produk'))

    return render_template('admin/produk/tambah_produk.html')

# ==================== UPDATE PRODUK ====================
@app.route('/admin/produk/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_produk(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nama = request.form['nama']
        harga = request.form['harga']
        deskripsi = request.form['deskripsi']
        gambar_input = request.form['gambar']

        # Ganti 'view' dengan 'thumbnail' agar gambar tampil sebagai thumbnail
        gambar = convert_drive_link(gambar_input, mode='thumbnail')

        cursor.execute(
            "UPDATE produk SET nama = %s, harga = %s, deskripsi = %s, gambar = %s WHERE id = %s",
            (nama, harga, deskripsi, gambar, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Produk berhasil diupdate.', 'success')
        return redirect(url_for('admin_produk'))

    cursor.execute("SELECT * FROM produk WHERE id = %s", (id,))
    produk = cursor.fetchone()

    cursor.close()
    conn.close()

    if not produk:
        flash('Produk tidak ditemukan.', 'danger')
        return redirect(url_for('admin_produk'))

    return render_template('admin/produk/update_produk.html', produk=produk)



@app.route('/admin/produk/hapus/<int:id>')
@login_required
def hapus_produk(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produk WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Produk berhasil dihapus.', 'success')
    return redirect(url_for('admin_produk'))

# ==================== UPDATE BROSUR ====================

@app.route('/admin/brosur')
@login_required
def admin_brosur():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_image")
    daftar_brosur = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/brosur/admin_brosur.html', daftar_brosur=daftar_brosur)

@app.route('/admin/brosur/tambah', methods=['GET', 'POST'])
@login_required
def tambah_brosur():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ambil data brosur (maksimum 1 yang disimpan)
    cursor.execute("SELECT * FROM menu_image LIMIT 1")
    brosur = cursor.fetchone()

    if request.method == 'POST':
        link_gdrive = request.form['gambar']

        # Ekstrak file ID dari link Google Drive
        try:
            file_id = link_gdrive.split('/d/')[1].split('/')[0]
        except IndexError:
            flash("Link Google Drive tidak valid!", "danger")
            return redirect(request.url)

        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        filename = secure_filename(f'brosur_{file_id}.jpg')
        save_path = os.path.join('static/images', filename)
        gambar_baru = f'images/{filename}'

        try:
            # Hapus gambar lama jika ada dan file-nya masih ada di folder
            if brosur and brosur.get('gambar'):
                gambar_lama_path = os.path.join('static', brosur['gambar'])
                if os.path.exists(gambar_lama_path):
                    os.remove(gambar_lama_path)

            # Download gambar baru
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                flash("Gagal mengunduh gambar dari Google Drive.", "danger")
                return redirect(request.url)

            # Simpan atau perbarui di database
            if brosur:
                cursor.execute(
                    "UPDATE menu_image SET gambar = %s WHERE id = %s",
                    (gambar_baru, brosur['id'])
                )
            else:
                cursor.execute(
                    "INSERT INTO menu_image (gambar) VALUES (%s)",
                    (gambar_baru,)
                )

            conn.commit()
            flash("Brosur berhasil diperbarui!", "success")
            return redirect(url_for('admin_brosur'))

        except Exception as e:
            flash(f"Gagal memproses gambar: {str(e)}", "danger")
            return redirect(request.url)

    cursor.close()
    conn.close()
    return render_template('admin/brosur/tambah_brosur.html', brosur=brosur)


@app.route('/admin/brosur/hapus/<int:id>')
@login_required
def hapus_brosur(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_image WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Brosur berhasil dihapus.', 'success')
    return redirect(url_for('admin_brosur'))

# ==================== ADMIN - BEST SELLER ====================
@app.route('/admin/best_seller')
@login_required
def admin_best_seller():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM best_seller")
    best_seller = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin/bestseller/admin_best_seller.html', best_seller=best_seller)

@app.route('/admin/best_seller/tambah', methods=['GET', 'POST'])
@login_required
def tambah_best_seller():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ambil daftar produk dari database
    cursor.execute("SELECT id, nama, harga, deskripsi, gambar FROM produk")
    produk_list = cursor.fetchall()

    if request.method == 'POST':
        produk_id = request.form['produk_id']

        # Ambil data produk yang dipilih
        cursor.execute("SELECT * FROM produk WHERE id = %s", (produk_id,))
        produk = cursor.fetchone()

        if not produk:
            flash('Produk tidak ditemukan.', 'danger')
            return redirect(url_for('tambah_best_seller'))

        # Konversi link gambar
        gambar = convert_drive_link(produk['gambar'], mode='thumbnail')

        # Simpan ke tabel best_seller
        cursor.execute(
            "INSERT INTO best_seller (nama, harga, deskripsi, gambar) VALUES (%s, %s, %s, %s)",
            (produk['nama'], produk['harga'], produk['deskripsi'], gambar)
        )
        conn.commit()
        flash('Best Seller berhasil ditambahkan.', 'success')
        return redirect(url_for('admin_best_seller'))

    cursor.close()
    conn.close()
    return render_template('admin/bestseller/tambah_best_seller.html', produk_list=produk_list)


@app.route('/admin/best_seller/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_best_seller(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ambil semua produk
    cursor.execute("SELECT id, nama FROM produk")
    produk_list = cursor.fetchall()

    # Ambil data best seller saat ini
    cursor.execute("SELECT * FROM best_seller WHERE id = %s", (id,))
    best_seller = cursor.fetchone()

    if not best_seller:
        flash('Data Best Seller tidak ditemukan.', 'danger')
        return redirect(url_for('admin_best_seller'))

    if request.method == 'POST':
        produk_id = request.form['produk_id']

        # Ambil detail produk dari pilihan user
        cursor.execute("SELECT * FROM produk WHERE id = %s", (produk_id,))
        produk = cursor.fetchone()

        if not produk:
            flash('Produk tidak ditemukan.', 'danger')
            return redirect(url_for('update_best_seller', id=id))

        gambar = convert_drive_link(produk['gambar'], mode='thumbnail')

        # Update data best seller
        cursor.execute(
            "UPDATE best_seller SET nama = %s, harga = %s, deskripsi = %s, gambar = %s WHERE id = %s",
            (produk['nama'], produk['harga'], produk['deskripsi'], gambar, id)
        )
        conn.commit()
        flash('Best Seller berhasil diupdate.', 'success')
        return redirect(url_for('admin_best_seller'))

    cursor.close()
    conn.close()
    return render_template('admin/bestseller/update_best_seller.html',
                           best_seller=best_seller,
                           produk_list=produk_list)


@app.route('/admin/best_seller/hapus/<int:id>')
@login_required
def hapus_best_seller(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM best_seller WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Best Seller berhasil dihapus.', 'success')
    return redirect(url_for('admin_best_seller'))

# ==================== RUN APP ====================
if __name__ == '__main__':
    app.run(debug=True)
