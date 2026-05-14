from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "smartportal123"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

# =========================
# DATABASE INIT
# =========================

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS jobs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
location TEXT,
salary TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS applied_jobs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
job_title TEXT,
location TEXT,
salary TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS profile(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
skills TEXT,
resume TEXT,
photo TEXT
)
""")

conn.commit()
conn.close()

# =========================
# HOME
# =========================

@app.route('/')
def home():
    return render_template('index.html')

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO users(name,email,password) VALUES(?,?,?)",
        (name,email,password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email,password)
        )

        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            return redirect('/dashboard')

        else:
            return "<h1>Invalid Login ❌</h1>"

    return render_template('login.html')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if "user" not in session:
        return redirect('/login')

    return render_template('dashboard.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =========================
# JOBS
# =========================

@app.route('/jobs')
def jobs():

    search = request.args.get('search','')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
    "SELECT * FROM jobs WHERE title LIKE ? OR location LIKE ? OR salary LIKE ?",
    ('%'+search+'%','%'+search+'%','%'+search+'%')
    )

    jobs_data = cur.fetchall()
    conn.close()

    return render_template('jobs.html', jobs=jobs_data)

# =========================
# ADD JOB
# =========================

@app.route('/add-job', methods=['GET','POST'])
def add_job():

    if request.method == 'POST':

        title = request.form['title']
        location = request.form['location']
        salary = request.form['salary']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO jobs(title,location,salary) VALUES(?,?,?)",
        (title,location,salary)
        )

        conn.commit()
        conn.close()

        return redirect('/jobs')

    return render_template('post_job.html')

# =========================
# APPLY JOB
# =========================

@app.route('/apply/<title>/<location>/<salary>')
def apply_job(title, location, salary):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
    "INSERT INTO applied_jobs(job_title,location,salary) VALUES(?,?,?)",
    (title,location,salary)
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# =========================
# PROFILE
# =========================

@app.route('/profile', methods=['GET','POST'])
def profile():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        skills = request.form['skills']

        photo_name = ''
        resume_name = ''

        photo = request.files.get('photo')
        resume = request.files.get('resume')

        if photo and photo.filename != '':
            photo_name = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_name))

        if resume and resume.filename != '':
            resume_name = secure_filename(resume.filename)
            resume.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_name))

        cur.execute(
        "INSERT INTO profile(name,email,skills,resume,photo) VALUES(?,?,?,?,?)",
        (name,email,skills,resume_name,photo_name)
        )

        conn.commit()

    cur.execute("SELECT * FROM profile ORDER BY id DESC LIMIT 1")
    user = cur.fetchone()

    conn.close()

    return render_template('profile.html', user=user)

# =========================
# RESUME AI
# =========================

@app.route('/resume-ai', methods=['GET','POST'])
def resume_ai():

    score = 0
    skills = []
    suggestions = []

    if request.method == 'POST':

        text = request.form['resume'].lower()

        keywords = ['python','html','css','sql','flask','java']

        for word in keywords:
            if word in text:
                skills.append(word)
                score += 15

        if 'project' not in text:
            suggestions.append("Add Projects Section")

        if 'experience' not in text:
            suggestions.append("Add Experience Section")

        if 'summary' not in text:
            suggestions.append("Add Professional Summary")

        if score > 100:
            score = 100

    return render_template(
    'resume_ai.html',
    score=score,
    skills=skills,
    suggestions=suggestions
    )

# =========================
# CHATBOT
# =========================

@app.route('/chatbot', methods=['GET','POST'])
def chatbot():

    reply = ""
    msg = ""

    if request.method == 'POST':

        msg = request.form['msg'].lower()

        if 'hello' in msg or 'hi' in msg:
            reply = "👋 Hello! Main Career Bot hu."

        elif 'job' in msg:
            reply = "💼 Daily apply karo aur resume strong rakho."

        elif 'salary' in msg:
            reply = "💰 Fresher salary ₹3-6 LPA ho sakti hai."

        elif 'python' in msg:
            reply = "🐍 Python best skill hai."

        elif 'resume' in msg:
            reply = "📄 Resume me projects aur skills add karo."

        else:
            reply = "🤖 Aap job, salary, python, resume puch sakte ho."

    return render_template(
    'chatbot.html',
    reply=reply,
    user_msg=msg
    )

# =========================
# ADMIN
# =========================

@app.route('/admin')
def admin():
    return render_template('admin.html')

# =========================
# ABOUT / CONTACT
# =========================

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# =========================
# RUN
# =========================

if __name__ == '__main__':
    app.run(debug=True)