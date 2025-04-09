
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY, user_id INTEGER, filename TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT)")
    conn.commit()
    conn.close()

def get_user():
    if 'user_id' in session:
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id=?', (session['user_id'],))
        user = c.fetchone()
        conn.close()
        return user
    return None

@app.route('/')
def index():
    user = get_user()
    return render_template('index.html', user=user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
        conn.commit()
        conn.close()
        return redirect('/login')
    return """<form method="post">
    Username: <input name="username"><br>
    Email: <input name="email"><br>
    Password: <input name="password" type="password"><br>
    <input type="submit" value="Sign Up">
</form>"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect('/')
    return """<form method="post">
    Username: <input name="username"><br>
    Password: <input name="password" type="password"><br>
    <input type="submit" value="Log In">
</form>"""

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/profile')
def profile():
    user = get_user()
    if not user:
        return redirect('/login')
    return f"<h2>Profile</h2><p>Username: {user[1]}</p><p>Email: {user[2]}</p>"

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    user = get_user()
    if not user:
        return redirect('/login')
    if request.method == 'POST':
        new_password = request.form['new_password']
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute('UPDATE users SET password=? WHERE id=?', (new_password, user[0]))
        conn.commit()
        conn.close()
        return redirect('/profile')
    return """<form method="post">
    New Password: <input name="new_password" type="password"><br>
    <input type="submit" value="Change Password">
</form>"""

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    user = get_user()
    if not user:
        return redirect('/login')
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = sqlite3.connect('app.db')
            c = conn.cursor()
            c.execute('INSERT INTO uploads (user_id, filename) VALUES (?, ?)', (user[0], filename))
            conn.commit()
            conn.close()
    return """<form method="post" enctype="multipart/form-data">
    Upload Image: <input type="file" name="file"><br>
    <input type="submit" value="Upload">
</form>"""

@app.route('/gallery')
def gallery():
    user = get_user()
    if not user:
        return redirect('/login')
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('SELECT filename FROM uploads WHERE user_id=?', (user[0],))
    images = c.fetchall()
    conn.close()
    image_html = ''.join([f'<img src="/uploads/{img[0]}" width="200">' for img in images])
    return f"<h2>Your Gallery</h2>{image_html}"

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post', methods=['GET', 'POST'])
def post():
    user = get_user()
    if not user:
        return redirect('/login')
    if request.method == 'POST':
        content = request.form['content']
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute('INSERT INTO posts (user_id, content) VALUES (?, ?)', (user[0], content))
        conn.commit()
        conn.close()
    return """<form method="post">
    Post Content: <textarea name="content"></textarea><br>
    <input type="submit" value="Post">
</form>"""

if __name__ == '__main__':
    init_db()
    app.run()
