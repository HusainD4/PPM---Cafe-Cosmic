import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta


# Import koneksi & cursor
from db.connection import db, cursor

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'


# ----- Dekorator untuk proteksi route admin -----
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ----- Admin Authentication Routes -----

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page (GET) and login processing (POST)"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_id'] = user['id_users']
            flash('Login berhasil', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    """Logout admin and clear session"""
    session.clear()
    flash('Anda berhasil logout', 'success')
    return redirect(url_for('admin_login'))


# ----- Admin Dashboard -----

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard showing summary data and recent products/best sellers"""
    jumlah_users = get_total_users()
    jumlah_produk = get_total_produk()
    jumlah_best_seller = get_total_best_seller()
    jumlah_promo = get_total_promo()

    produk_terbaru = get_latest_produk(limit=5)
    best_seller_terbaru = get_latest_best_seller(limit=5)

    return render_template('admin/dashboard.html',
                           jumlah_users=jumlah_users,
                           jumlah_produk=jumlah_produk,
                           jumlah_best_seller=jumlah_best_seller,
                           jumlah_promo=jumlah_promo,
                           produk_terbaru=produk_terbaru,
                           best_seller_terbaru=best_seller_terbaru)


# # ----- Admin Update Produk Interaktif Status -----

# @app.route('/admin/update_interaktif', methods=['POST'])
# @login_required
# def admin_update_interaktif():
#     """Update the 'interaktif' status (biasa, promo, best seller) for products"""
#     for key, value in request.form.items():
#         if key.startswith('interaktif_'):
#             id_produk = key.split('_')[1]
#             interaktif = value
#             cursor.execute("UPDATE produk SET interaktif = %s WHERE id_produk = %s", (interaktif, id_produk))
#     db.commit()
#     flash('Status interaktif produk berhasil diperbarui.', 'success')
#     return redirect(url_for('admin_best_seller'))


# ----- Helper Functions to Fetch Summary Data -----

def get_total_users():
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    result = cursor.fetchone()
    return result['total'] if result else 0


def get_total_produk():
    cursor.execute("SELECT COUNT(*) AS total FROM produk")
    result = cursor.fetchone()
    return result['total'] if result else 0


def get_total_best_seller():
    cursor.execute("SELECT COUNT(*) AS total FROM best_seller")
    result = cursor.fetchone()
    return result['total'] if result else 0


def get_total_promo():
    # Jika kamu punya tabel promo, sesuaikan nama tabelnya
    cursor.execute("SELECT COUNT(*) AS total FROM promo")
    result = cursor.fetchone()
    return result['total'] if result else 0


def get_latest_produk(limit=5):
    cursor.execute("""
        SELECT p.*, u.username AS added_by FROM produk p
        LEFT JOIN users u ON p.id_user = u.id_users
        ORDER BY p.created_at DESC
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()


def get_latest_best_seller(limit=5):
    cursor.execute("""
        SELECT bs.*, p.nama_produk, u.username FROM best_seller bs
        JOIN produk p ON bs.id_produk = p.id_produk
        JOIN users u ON bs.id_users = u.id_users
        ORDER BY bs.created_at DESC
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()


# ----- CRUD Users -----

@app.route('/admin/users')
@login_required
def admin_users():
    """List all users"""
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    """Add new user form and submission"""
    if request.method == 'POST':
        username = request.form['username']
        nama_lengkap = request.form['nama_lengkap']
        password = request.form['password']
        konfirmasi_password = request.form['konfirmasi_password']

        if password != konfirmasi_password:
            flash('Password dan konfirmasi password tidak sama', 'danger')
            return redirect(url_for('admin_add_user'))

        hashed_pw = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, nama_lengkap, password)
            VALUES (%s, %s, %s)
        """, (username, nama_lengkap, hashed_pw))
        db.commit()
        flash('User berhasil ditambahkan', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/add_user.html')


@app.route('/admin/users/edit/<int:id_users>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(id_users):
    """Edit user details form and submission"""
    cursor.execute("SELECT * FROM users WHERE id_users=%s", (id_users,))
    user = cursor.fetchone()

    if request.method == 'POST':
        username = request.form['username']
        nama_lengkap = request.form['nama_lengkap']
        password = request.form.get('password')
        konfirmasi_password = request.form.get('konfirmasi_password')

        if password:
            if password != konfirmasi_password:
                flash('Password dan konfirmasi password tidak sama', 'danger')
                return redirect(url_for('admin_edit_user', id_users=id_users))
            hashed_pw = generate_password_hash(password)
            cursor.execute("""
                UPDATE users SET username=%s, nama_lengkap=%s, password=%s
                WHERE id_users=%s
            """, (username, nama_lengkap, hashed_pw, id_users))
        else:
            cursor.execute("""
                UPDATE users SET username=%s, nama_lengkap=%s
                WHERE id_users=%s
            """, (username, nama_lengkap, id_users))

        db.commit()
        flash('User berhasil diupdate', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/edit_user.html', user=user)


@app.route('/admin/users/delete/<int:id_users>', methods=['POST'])
@login_required
def admin_delete_user(id_users):
    """Delete user by id"""
    cursor.execute("DELETE FROM users WHERE id_users=%s", (id_users,))
    db.commit()
    flash('User berhasil dihapus', 'success')
    return redirect(url_for('admin_users'))


# ----- CRUD Produk -----

@app.route('/admin/produk')
@login_required
def admin_produk():
    """List all products"""
    cursor.execute("""
        SELECT p.*, u.username AS added_by FROM produk p
        LEFT JOIN users u ON p.id_user = u.id_users
        ORDER BY p.created_at DESC
    """)
    produk = cursor.fetchall()
    return render_template('admin/produk.html', produk=produk)


@app.route('/admin/produk/add', methods=['GET', 'POST'])
@login_required
def admin_add_produk():
    """Add new product form and submission"""
    cursor.execute("SELECT id_users, username FROM users")
    users = cursor.fetchall()

    if request.method == 'POST':
        nama_produk = request.form['nama_produk']
        deskripsi_produk = request.form['deskripsi_produk']
        harga_produk = request.form['harga_produk']
        interaktif = request.form['interaktif']
        gambar = request.form['gambar']  # Hanya nama file, bisa dikembangkan upload file
        id_user = request.form.get('id_user') or None

        cursor.execute("""
            INSERT INTO produk (nama_produk, deskripsi_produk, harga_produk, interaktif, gambar, id_user)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nama_produk, deskripsi_produk, harga_produk, interaktif, gambar, id_user))
        db.commit()
        flash('Produk berhasil ditambahkan', 'success')
        return redirect(url_for('admin_produk'))

    return render_template('admin/add_produk.html', users=users)


@app.route('/admin/produk/edit/<int:id_produk>', methods=['GET', 'POST'])
@login_required
def admin_edit_produk(id_produk):
    """Edit product details form and submission"""
    cursor.execute("SELECT * FROM produk WHERE id_produk=%s", (id_produk,))
    produk = cursor.fetchone()
    cursor.execute("SELECT id_users, username FROM users")
    users = cursor.fetchall()

    if request.method == 'POST':
        nama_produk = request.form['nama_produk']
        deskripsi_produk = request.form['deskripsi_produk']
        harga_produk = request.form['harga_produk']
        interaktif = request.form['interaktif']
        gambar = request.form['gambar']
        id_user = request.form.get('id_user') or None

        cursor.execute("""
            UPDATE produk SET nama_produk=%s, deskripsi_produk=%s, harga_produk=%s, interaktif=%s, gambar=%s, id_user=%s
            WHERE id_produk=%s
        """, (nama_produk, deskripsi_produk, harga_produk, interaktif, gambar, id_user, id_produk))
        db.commit()
        flash('Produk berhasil diupdate', 'success')
        return redirect(url_for('admin_produk'))

    return render_template('admin/edit_produk.html', produk=produk, users=users)


@app.route('/admin/produk/delete/<int:id_produk>', methods=['POST'])
@login_required
def admin_delete_produk(id_produk):
    """Delete product by id"""
    cursor.execute("DELETE FROM produk WHERE id_produk=%s", (id_produk,))
    db.commit()
    flash('Produk berhasil dihapus', 'success')
    return redirect(url_for('admin_produk'))


# ----- CRUD Tentang Kami -----

@app.route('/admin/tentang_kami')
@login_required
def admin_tentang_kami():
    """List all 'Tentang Kami' entries"""
    cursor.execute("SELECT * FROM tentang_kami")
    tentang = cursor.fetchall()
    return render_template('admin/tentang_kami.html', tentang=tentang)


@app.route('/admin/tentang_kami/add', methods=['GET', 'POST'])
@login_required
def admin_add_tentang_kami():
    """Add 'Tentang Kami' entry"""
    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']

        cursor.execute("""
            INSERT INTO tentang_kami (judul, isi)
            VALUES (%s, %s)
        """, (judul, isi))
        db.commit()
        flash('Data tentang kami berhasil ditambahkan', 'success')
        return redirect(url_for('admin_tentang_kami'))

    return render_template('admin/add_tentang_kami.html')


@app.route('/admin/tentang_kami/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_tentang_kami(id):
    """Edit 'Tentang Kami' entry"""
    cursor.execute("SELECT * FROM tentang_kami WHERE id=%s", (id,))
    tentang = cursor.fetchone()

    if request.method == 'POST':
        judul = request.form['judul']
        isi = request.form['isi']

        cursor.execute("""
            UPDATE tentang_kami SET judul=%s, isi=%s WHERE id=%s
        """, (judul, isi, id))
        db.commit()
        flash('Data tentang kami berhasil diupdate', 'success')
        return redirect(url_for('admin_tentang_kami'))

    return render_template('admin/edit_tentang_kami.html', tentang=tentang)


@app.route('/admin/tentang_kami/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_tentang_kami(id):
    """Delete 'Tentang Kami' entry"""
    cursor.execute("DELETE FROM tentang_kami WHERE id=%s", (id,))
    db.commit()
    flash('Data tentang kami berhasil dihapus', 'success')
    return redirect(url_for('admin_tentang_kami'))

# ----- CRUD Best Seller -----

@app.route('/admin/best_seller')
@login_required
def admin_best_seller():
    cursor.execute("""
        SELECT bs.*, p.nama_produk, p.harga_produk, u.username 
        FROM best_seller bs
        JOIN produk p ON bs.id_produk = p.id_produk
        JOIN users u ON bs.id_users = u.id_users
        ORDER BY bs.created_at DESC
    """)
    best_seller = cursor.fetchall()

    cursor.execute("SELECT id_produk, nama_produk, harga_produk, interaktif FROM produk")
    produk_list = cursor.fetchall()

    cursor.execute("SELECT id_users, username FROM users")
    users_list = cursor.fetchall()

    return render_template('admin/best_seller.html',
                           best_seller=best_seller,
                           produk=produk_list,
                           users_list=users_list)


@app.route('/admin/best_seller/add', methods=['POST'])
@login_required
def admin_add_best_seller():
    id_produk = request.form['id_produk']
    id_users = current_user.id_users  # Pakai user login sekarang

    cursor.execute("""
        INSERT INTO best_seller (id_produk, id_users, created_at, updated_at)
        VALUES (%s, %s, NOW(), NOW())
    """, (id_produk, id_users))
    db.commit()
    flash('Best seller berhasil ditambahkan', 'success')
    return redirect(url_for('admin_best_seller'))


@app.route('/admin/update_interaktif', methods=['POST'])
@login_required
def admin_update_interaktif():
    cursor.execute("SELECT id_produk, harga_produk FROM produk")
    produk_list = cursor.fetchall()

    for p in produk_list:
        id_produk = p['id_produk']

        # Ambil status dari form
        status = request.form.get(f'interaktif_{id_produk}')

        # Hapus dulu best_seller dan promo terkait produk ini
        cursor.execute("DELETE FROM best_seller WHERE id_produk = %s", (id_produk,))
        cursor.execute("DELETE FROM promo WHERE id_produk = %s", (id_produk,))

        if status == 'best seller':
            # Insert ke best_seller dengan user sekarang
            cursor.execute("""
                INSERT INTO best_seller (id_produk, id_users, nama_produk, harga_produk, deskripsi_produk, tanggal_berlaku_dari, tanggal_berlaku_sampai, created_at, updated_at, action)
                SELECT id_produk, %s, nama_produk, harga_produk, deskripsi_produk, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), NOW(), NOW(), 'added'
                FROM produk WHERE id_produk = %s
            """, (current_user.id_users, id_produk))

        elif status == 'promo':
            harga_promo = request.form.get(f'harga_promo_{id_produk}')
            tanggal_mulai = request.form.get(f'tanggal_mulai_{id_produk}')
            tanggal_berakhir = request.form.get(f'tanggal_berakhir_{id_produk}')

            # Validasi input promo sederhana
            if not harga_promo or not tanggal_mulai or not tanggal_berakhir:
                flash(f'Lengkapi data promo untuk produk ID {id_produk}', 'danger')
                continue

            cursor.execute("""
                INSERT INTO promo (id_produk, nama_promo, deskripsi, tanggal_mulai, tanggal_berakhir, harga_promo, created_at, updated_at)
                SELECT id_produk, nama_produk, deskripsi_produk, %s, %s, %s, NOW(), NOW()
                FROM produk WHERE id_produk = %s
            """, (tanggal_mulai, tanggal_berakhir, harga_promo, id_produk))

        # Update status interaktif di produk
        cursor.execute("UPDATE produk SET interaktif = %s WHERE id_produk = %s", (status, id_produk))

    db.commit()
    flash("Status interaktif berhasil diperbarui.", "success")
    return redirect(url_for('admin_best_seller'))


@app.route('/admin/best_seller/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_best_seller(id):
    cursor.execute("DELETE FROM best_seller WHERE id=%s", (id,))
    db.commit()
    flash('Best seller berhasil dihapus', 'success')
    return redirect(url_for('admin_best_seller'))


# ----- CRUD Promo -----

@app.route('/admin/promo')
@login_required
def admin_promo():
    cursor.execute("SELECT * FROM promo ORDER BY created_at DESC")
    promo = cursor.fetchall()
    return render_template('admin/promo.html', promo=promo)


@app.route('/admin/promo/add', methods=['GET', 'POST'])
@login_required
def admin_add_promo():
    if request.method == 'POST':
        nama_promo = request.form['nama_promo']
        deskripsi_promo = request.form['deskripsi_promo']
        tanggal_mulai = request.form['tanggal_mulai']
        tanggal_selesai = request.form['tanggal_selesai']

        cursor.execute("""
            INSERT INTO promo (nama_promo, deskripsi_promo, tanggal_mulai, tanggal_selesai, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (nama_promo, deskripsi_promo, tanggal_mulai, tanggal_selesai))
        db.commit()
        flash('Promo berhasil ditambahkan', 'success')
        return redirect(url_for('admin_promo'))

    return render_template('admin/add_promo.html')


@app.route('/admin/promo/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_promo(id):
    cursor.execute("SELECT * FROM promo WHERE id=%s", (id,))
    promo = cursor.fetchone()

    if request.method == 'POST':
        nama_promo = request.form['nama_promo']
        deskripsi_promo = request.form['deskripsi_promo']
        tanggal_mulai = request.form['tanggal_mulai']
        tanggal_selesai = request.form['tanggal_selesai']

        cursor.execute("""
            UPDATE promo SET nama_promo=%s, deskripsi_promo=%s, tanggal_mulai=%s, tanggal_selesai=%s, updated_at=NOW()
            WHERE id=%s
        """, (nama_promo, deskripsi_promo, tanggal_mulai, tanggal_selesai, id))
        db.commit()
        flash('Promo berhasil diupdate', 'success')
        return redirect(url_for('admin_promo'))

    return render_template('admin/edit_promo.html', promo=promo)


@app.route('/admin/promo/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_promo(id):
    cursor.execute("DELETE FROM promo WHERE id=%s", (id,))
    db.commit()
    flash('Promo berhasil dihapus', 'success')
    return redirect(url_for('admin_promo'))

# ----- Jalankan aplikasi -----
if __name__ == '__main__':
    app.run(debug=True)
