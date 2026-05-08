from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import os
import PyPDF2
from datetime import datetime

app = Flask(__name__)

# =========================================
# MYSQL CONFIGURATION
# =========================================

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'interviewiq'
from flask_mail import Mail, Message
mysql = MySQL(app)
# =========================================
# EMAIL CONFIGURATION
# =========================================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = 'krupadasari2022@gmail.com'

app.config['MAIL_PASSWORD'] = 'uzcohpjsufxahsvf'

mail = Mail(app)


# =========================================
# ENABLE CORS
# =========================================

CORS(app)

# =========================================
# FILE UPLOAD CONFIGURATION
# =========================================

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# =========================================
# SKILLS DATABASE
# =========================================

skills_db = [
    "Python",
    "Java",
    "HTML",
    "CSS",
    "JavaScript",
    "SQL",
    "Machine Learning",
    "Flask",
    "React",
    "Node.js",
    "MongoDB",
    "Bootstrap",
    "Git",
    "GitHub",
    "C",
    "C++"
]

# =========================================
# HOME ROUTE
# =========================================

@app.route('/')
def home():

    return jsonify({
        "message": "InterviewIQ AI Backend Running Successfully 🚀"
    })

# =========================================
# TEST DATABASE CONNECTION
# =========================================

@app.route('/testdb')
def testdb():

    try:

        cur = mysql.connection.cursor()

        cur.execute("SELECT 1")

        cur.close()

        return jsonify({
            "status": "success",
            "message": "Database Connected Successfully ✅"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })

# =========================================
# CREATE USERS TABLE
# =========================================

@app.route('/create_users_table')
def create_users_table():

    cur = mysql.connection.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INT AUTO_INCREMENT PRIMARY KEY,

            name VARCHAR(100),

            email VARCHAR(100),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    mysql.connection.commit()

    cur.close()

    return jsonify({
        "message": "Users Table Created Successfully ✅"
    })

# =========================================
# CREATE RESUME TABLE
# =========================================

@app.route('/create_resume_table')
def create_resume_table():

    cur = mysql.connection.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (

            id INT AUTO_INCREMENT PRIMARY KEY,

            filename VARCHAR(255),

            ats_score INT,

            skills TEXT,

            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    mysql.connection.commit()

    cur.close()

    return jsonify({
        "message": "Resume Table Created Successfully ✅"
    })

# =========================================
# ADD USER
# =========================================

@app.route('/add_user')
def add_user():

    cur = mysql.connection.cursor()

    cur.execute(
        """
        INSERT INTO users(name, email)
        VALUES(%s, %s)
        """,
        ('Krupa', 'krupadasari@gmail.com')
    )

    mysql.connection.commit()

    cur.close()

    return jsonify({
        "message": "User Added Successfully ✅"
    })

# =========================================
# VIEW USERS
# =========================================

@app.route('/users')
def users():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT * FROM users
        ORDER BY id DESC
    """)

    data = cur.fetchall()

    cur.close()

    return jsonify(data)

# =========================================
# RESUME ANALYZER
# =========================================

@app.route('/analyze_resume', methods=['POST'])
def analyze_resume():

    try:

        # CHECK FILE

        if 'resume' not in request.files:

            return jsonify({
                "status": "error",
                "message": "No Resume Uploaded"
            })

        file = request.files['resume']

        if file.filename == '':

            return jsonify({
                "status": "error",
                "message": "Please Select PDF Resume"
            })

        # SAVE FILE

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            file.filename
        )

        file.save(filepath)

        # EXTRACT PDF TEXT

        text = ""

        with open(filepath, 'rb') as pdf_file:

            reader = PyPDF2.PdfReader(pdf_file)

            for page in reader.pages:

                extracted = page.extract_text()

                if extracted:
                    text += extracted

        # DETECT SKILLS

        detected_skills = []

        for skill in skills_db:

            if skill.lower() in text.lower():

                detected_skills.append(skill)

        # CALCULATE ATS SCORE

        ats_score = min(len(detected_skills) * 10, 100)

        # SAVE TO DATABASE

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO resumes
            (filename, ats_score, skills)

            VALUES(%s, %s, %s)
            """,
            (
                file.filename,
                ats_score,
                ", ".join(detected_skills)
            )
        )

        mysql.connection.commit()

        cur.close()

        # RETURN RESPONSE

        return jsonify({

            "status": "success",

            "message": "Resume Analyzed Successfully ✅",

            "filename": file.filename,

            "ats_score": ats_score,

            "skills": detected_skills

        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })

# =========================================
# VIEW RESUMES
# =========================================


def resumes():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT * FROM resumes
        ORDER BY id DESC
    """)

    data = cur.fetchall()

    cur.close()

    return jsonify(data)

# =========================================
# DASHBOARD ANALYTICS
# =========================================

@app.route('/analytics')
def analytics():

    cur = mysql.connection.cursor()

    # TOTAL RESUMES

    cur.execute("SELECT COUNT(*) FROM resumes")

    total_resumes = cur.fetchone()[0]

    # AVERAGE ATS SCORE

    cur.execute("SELECT AVG(ats_score) FROM resumes")

    avg_score = cur.fetchone()[0]

    if avg_score is None:
        avg_score = 0

    # TOP SKILLS

    cur.execute("SELECT skills FROM resumes")

    skills_data = cur.fetchall()

    cur.close()

    return jsonify({

        "total_resumes": total_resumes,

        "average_ats_score": round(avg_score, 2),

        "message": "Analytics Loaded Successfully 🚀"

    })

# =========================================
# DELETE RESUME
# =========================================

@app.route('/delete_resume/<int:id>')
def delete_resume(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM resumes WHERE id = %s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return jsonify({
        "message": "Resume Deleted Successfully 🗑️"
    })

# =========================================
# RUN APPLICATION
# =========================================
# =========================================
# VIEW RESUMES
# =========================================

@app.route('/resumes')
def resumes():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM resumes")

    data = cur.fetchall()

    cur.close()

    return str(data)

# =========================================
# SEND WELCOME EMAIL
# =========================================

@app.route('/send_email')
def send_email():

    msg = Message(

        'Welcome to InterviewIQ AI 🚀',

        sender=app.config['MAIL_USERNAME'],

        recipients=['krupadasari2022@gmail.com']

    )

    msg.body = """

Hello,

Thank you for registering with InterviewIQ AI 🚀

Your AI interview preparation journey starts now.

Best Regards,
InterviewIQ AI Team

"""

    mail.send(msg)

    return "Email Sent Successfully!"

# =========================================
# RUN APP
# =========================================

if __name__ == '__main__':
    app.run(debug=True)

