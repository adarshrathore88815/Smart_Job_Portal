from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from flask import Flask, render_template, request, redirect
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

app.secret_key = "smartportal123"

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Applied Jobs Table
cur.execute("""
CREATE TABLE IF NOT EXISTS applied_jobs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
job_title TEXT,
location TEXT,
salary TEXT
)
""")

# Profile Table
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password TEXT)")
        cur.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)", (name,email,password))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
        user = cur.fetchone()

        conn.close()

        if user:
           return render_template('dashboard.html')
        else:
            return "<h1>Invalid Login ❌</h1>"

    return render_template('login.html')

    
 
@app.route('/jobs')
def jobs():

    search = request.args.get('search', '')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
       "SELECT * FROM jobs WHERE title LIKE ? OR location LIKE ? OR salary LIKE ?",
        ('%'+search+'%', '%'+search+'%', '%'+search+'%')
    )

    jobs_data = cur.fetchall()

    conn.close()

    return render_template('jobs.html', jobs=jobs_data)

@app.route('/apply/<title>/<location>/<salary>')
def apply_job(title, location, salary):

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO applied_jobs(job_title, location, salary) VALUES(?,?,?)",
        (title, location, salary)
    )

    conn.commit()
    conn.close()

    return redirect('/history')

# 👇 YAHAN ADD KARO
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        name = request.form['name']
        file = request.files['resume']

        if file:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        return "<h1>Job Applied Successfully 🚀</h1>"

    return render_template('apply.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# 👇 ISKE NICHE PASTE KARO


@app.route('/profile', methods=['GET', 'POST'])
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
            (name, email, skills, resume_name, photo_name)
        )

        conn.commit()

        return redirect('/profile')

    cur.execute("SELECT * FROM profile ORDER BY id DESC LIMIT 1")
    user = cur.fetchone()

    conn.close()

    return render_template('profile.html', user=user)

@app.route('/resume-ai', methods=['GET', 'POST'])
def resume_ai():

    score = 0
    skills = []
    suggestions = []

    if request.method == 'POST':

        text = request.form['resume'].lower()

        keywords = ['python', 'html', 'css', 'sql', 'flask', 'java']

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
 
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():

    reply = ""
    msg = ""

    if request.method == 'POST':

        msg = request.form.get('msg', '').lower().strip()

        # Name save
        if 'my name is' in msg:
            name = msg.replace('my name is', '').strip()
            session['name'] = name.title()
            reply = f"😊 Nice to meet you {session['name']}!"

        elif 'mera naam' in msg:
            name = msg.replace('mera naam', '').strip()
            session['name'] = name.title()
            reply = f"😊 Namaste {session['name']}!"

        elif any(x in msg for x in ['hello','hi','hey']):
            if 'name' in session:
                reply = f"👋 Hello {session['name']}! Main aapki help ke liye hu."
            else:
                reply = "👋 Hello! Main Smart Career Bot hu."

        elif 'company' in msg and 'job' in msg:
            reply = "🏢 Achhi company ke liye Python, SQL, Projects, Communication aur interview prep karo."

        elif 'job' in msg:
            reply = "💼 Daily apply karo, resume strong rakho aur skills improve karo."

        elif 'salary' in msg:
            reply = "💰 Fresher salary ₹3-6 LPA se start ho sakti hai."

        elif 'python' in msg:
            reply = "🐍 Python AI, Backend, Automation ke liye excellent hai."

        elif 'resume' in msg:
            reply = "📄 Resume me projects, skills aur internships add karo."

        elif 'thank' in msg:
            if 'name' in session:
                reply = f"😊 Welcome {session['name']}!"
            else:
                reply = "😊 Welcome!"

        else:
            reply = "🤖 Aap job, salary, python, company, resume puch sakte ho."

    return render_template('chatbot.html', reply=reply, user_msg=msg)
             
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            return render_template('admin_dashboard.html')
        else:
            return "<h1>Wrong Admin Login ❌</h1>"

    return render_template('admin_login.html')

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    location TEXT,
    salary TEXT
)
""")

conn.commit()
conn.close()

@app.route('/add-job', methods=['GET', 'POST'])
def add_job():

    if request.method == 'POST':
        title = request.form['title']
        location = request.form['location']
        salary = request.form['salary']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO jobs(title, location, salary) VALUES(?,?,?)",
            (title, location, salary)
        )

        conn.commit()
        conn.close()

        return redirect('/jobs')

    return render_template('post_job.html')

@app.route('/admin/users')
def admin_users():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    data = cur.fetchall()

    conn.close()

    return render_template('manage_users.html', users=data)

if __name__ == '__main__':
    app.run(debug=True)