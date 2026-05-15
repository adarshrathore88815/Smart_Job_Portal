from pydoc import text
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from docx import Document
from PyPDF2 import PdfReader

def check_login():

    if 'user' not in session:
        return False

    return True

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
username TEXT,
job_title TEXT,
company TEXT,
location TEXT,
salary TEXT,
status TEXT,
apply_date TEXT
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

    if not check_login():
        return redirect('/login')

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



@app.route('/apply/<title>/<company>/<location>/<salary>')
def apply_job(title, company, location, salary):

    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # TABLE

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applicants(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    salary TEXT,
    status TEXT,
    apply_date TEXT
    )
    """)

    # CHECK ALREADY APPLIED

    cur.execute(
    "SELECT * FROM applicants WHERE username=? AND title=?",
    (username, title)
    )

    already = cur.fetchone()

    if already:

        conn.close()

        return """
        <h1 style='font-family:Arial;text-align:center;margin-top:100px;color:red;'>
        ⚠ Already Applied
        </h1>
        """

    # DATE

    apply_date = datetime.now().strftime("%d %B %Y")

    # INSERT

    cur.execute("""
    INSERT INTO applicants(
    username,
    title,
    company,
    location,
    salary,
    status,
    apply_date
    )

    VALUES(?,?,?,?,?,?,?)
    """,

    (
    username,
    title,
    company,
    location,
    salary,
    "Applied ✅",
    apply_date
    )
    )

    conn.commit()
    conn.close()

    return render_template(
    'apply.html',
    title=title,
    company=company,
    location=location,
    salary=salary
    )


@app.route('/applicants')
def applicants():

    if 'admin' not in session:
        return redirect('/admin-login')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM applicants")

    data = cur.fetchall()

    conn.close()

    return render_template(
    'applicants.html',
    applicants=data
    )

@app.route('/profile', methods=['GET','POST'])
def profile():

    if not check_login():
        return redirect('/login')

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


@app.route('/applied-jobs')
def applied_jobs():

    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
    "SELECT * FROM applied_jobs WHERE username=?",
    (username,)
    )

    jobs = cur.fetchall()

    conn.close()

    return render_template('applied_jobs.html', jobs=jobs)


# =========================
# RESUME AI
# =========================

@app.route('/resume-ai', methods=['GET', 'POST'])
def resume_ai():


    if not check_login():
        return redirect('/login')
    
    score = 0
    skills = []
    suggestions = []

    if request.method == 'POST':

        file = request.files.get('resume_file')

        text = ""

        if file and file.filename != "":

            filename = file.filename.lower()

            try:

                # PDF
                if filename.endswith('.pdf'):

                    pdf = PdfReader(file)

                    for page in pdf.pages:

                        page_text = page.extract_text()

                        if page_text:
                            text += page_text

                # DOCX
                elif filename.endswith('.docx'):

                    doc = Document(file)

                    for para in doc.paragraphs:
                        text += para.text

                # TXT
                elif filename.endswith('.txt'):

                    text = file.read().decode('utf-8')

            except:
                text = ""

            text = text.lower()

            keywords = [
                'python',
                'html',
                'css',
                'sql',
                'flask',
                'java',
                'javascript',
                'react',
                'mysql',
                'machine learning',
                'ai',
                'c++'
            ]

            for word in keywords:

                if word in text:
                    skills.append(word)
                    score += 8

            # EXTRA SCORE

            if 'project' in text:
                score += 15

            if 'experience' in text:
                score += 15

            if 'education' in text:
                score += 10

            if 'skills' in text:
                score += 10

            # LIMIT

            if score > 100:
                score = 100

            # AI SUGGESTIONS

            if 'project' not in text:
                suggestions.append("❌ Add Projects Section to show practical experience.")

            if 'experience' not in text:
                suggestions.append("❌ Add Internship or Experience section.")

            if 'summary' not in text:
                suggestions.append("❌ Add Professional Summary at top.")

            if 'skills' not in text:
                suggestions.append("❌ Add Technical Skills section.")

            if 'github' not in text:
                suggestions.append("❌ Add GitHub profile link.")

            if 'linkedin' not in text:
                suggestions.append("❌ Add LinkedIn profile link.")

            if 'certificate' not in text:
                suggestions.append("❌ Add Certifications section.")

            if len(skills) < 4:
                suggestions.append("⚠ Add more technical skills for better ATS score.")

            if score >= 80:
                suggestions.append("✅ Excellent Resume for fresher jobs.")

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

    if not check_login():
        return redirect('/login')

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

# =========================
# ADMIN LOGIN
# =========================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin123':

            session['admin'] = 'admin'

            return redirect('/admin-dashboard')

        else:
            return "Wrong Admin Login ❌"

    return render_template('admin_login.html')




# =========================
# ADMIN DASHBOARD
# =========================

@app.route('/admin-dashboard')
def admin_dashboard():

     if 'admin' not in session:
        return redirect('/admin-login')

     return render_template('admin_dashboard.html')


# =========================
# MANAGE JOBS
# =========================

@app.route('/manage-jobs')
def manage_jobs():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()

    conn.close()

    return render_template('manage_jobs.html', jobs=jobs)


# =========================
# DELETE JOB
# =========================

@app.route('/delete-job/<int:id>')
def delete_job(id):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("DELETE FROM jobs WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/manage-jobs')


# =========================
# MANAGE USERS
# =========================

@app.route('/admin/users')
def admin_users():

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    conn.close()

    return render_template('manage_users.html', users=users)

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