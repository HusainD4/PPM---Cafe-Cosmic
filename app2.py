import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db.connection import db


app = Flask(__name__)
app.secret_key = 'your_secret_key_very_secret'  # Ganti dengan secret key yang kuat

# ---------------------- Halaman User ----------------------

@app.route('/')
def index():
    return render_template('view/user/index.html')

@app.route('/about')
def about():
    return render_template('view/user/about.html')

@app.route('/menu')
def menu():
    return render_template('view/user/menu.html')

# ---------------------- API MongoDB ----------------------

@app.route('/users')
def get_users():
    users = list(db['users'].find({}, {"_id": 0}))
    return jsonify(users)

# ---------------------- Admin Login ----------------------

# --- ROUTE LOGIN ADMIN ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Cek apakah users masih kosong
    cursor.execute("SELECT COUNT(*) as total FROM users")
    result = cursor.fetchone()
    if result[0] == 0:

        # Insert default user
        default_username = "husain"
        default_nama = "Husain Mulyansyah"
        default_password = "Husain281005!"
        hashed_pw = generate_password_hash(default_password)

        cursor.execute("""
            INSERT INTO users (username, nama_lengkap, password)
            VALUES (%s, %s, %s)
        """, (default_username, default_nama, hashed_pw))
        db.commit()
        print("[INFO] Default user inserted!")

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['admin_logged_in'] = True
            session['username'] = user['username']
            flash('Berhasil login!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('admin/login.html')

# --- DASHBOARD ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('admin_login'))
    return "<h2>Selamat datang di Dashboard Admin</h2>"

# --- LOGOUT ---
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Berhasil logout.', 'info')
    return redirect(url_for('admin_login'))

# ---------------------- Superadmin Middleware ----------------------

def is_superadmin():
    if not session.get('admin_logged_in'):
        return False
    user = db['users'].find_one({'username': session.get('username')})
    if user and user.get('role') == 'superadmin':
        return True
    return False

# ---------------------- Superadmin Masterkey ----------------------

@app.route('/admin/masterkey', methods=['GET', 'POST'])
def superadmin_dashboard():
    if not is_superadmin():
        flash('Akses ditolak. Anda bukan Super Admin.', 'danger')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if db['users'].find_one({'username': username}):
            flash('Username sudah ada.', 'warning')
        else:
            hashed_pw = generate_password_hash(password)
            db['users'].insert_one({
                'username': username,
                'password': hashed_pw,
                'role': 'admin'
            })
            flash('Admin baru berhasil ditambahkan!', 'success')

    admins = list(db['users'].find({'role': 'admin'}))
    return render_template('admin/masterkey.html', admins=admins)

@app.route('/admin/delete/<username>', methods=['POST'])
def delete_admin(username):
    if not is_superadmin():
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin_login'))

    if username == 'root':
        flash('Superadmin tidak bisa dihapus.', 'danger')
    else:
        db['users'].delete_one({'username': username})
        flash(f'Admin "{username}" telah dihapus.', 'info')
    return redirect(url_for('superadmin_dashboard'))

# ---------------------- Jalankan App ----------------------

if __name__ == '__main__':
    app.run(debug=True)
