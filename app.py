from flask import Flask, render_template, request, redirect, session, send_file
from flask_mysqldb import MySQL
from reportlab.pdfgen import canvas
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)

app.secret_key = "resume_builder_secret"

# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '0811'
app.config['MYSQL_DB'] = 'resume_builder'

mysql = MySQL(app)

# Home
@app.route("/")
def home():
    return render_template("index.html")

# Register
@app.route("/register")
def register():
    return render_template("register.html")

# Login
@app.route("/login")
def login():
    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", name=session["user"])
    return redirect("/login")

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# Login user
@app.route("/login_user", methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["password"]

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email, password)
    )
    user = cursor.fetchone()
    cursor.close()

    if user:
        session["user"] = user[1]
        return redirect("/dashboard")

    return "Invalid Email or Password"

# Register user
@app.route("/register_user", methods=["POST"])
def register_user():

    fullname = request.form["fullname"]
    email = request.form["email"]
    password = request.form["password"]

    cursor = mysql.connection.cursor()

    # Check if email already exists
    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    if user:
        cursor.close()
        return "Email already registered. Please Login."

    # Insert new user
    cursor.execute(
        "INSERT INTO users(fullname,email,password) VALUES(%s,%s,%s)",
        (fullname, email, password)
    )

    mysql.connection.commit()
    cursor.close()

    return redirect("/login")

# Create resume page
@app.route("/create_resume")
def create_resume():
    if "user" not in session:
        return redirect("/login")
    return render_template("create_resume.html")

# Save resume
@app.route("/save_resume", methods=["POST"])
def save_resume():

    fullname = request.form["fullname"]
    email = request.form["email"]
    phone = request.form["phone"]
    address = request.form["address"]
    education = request.form["education"]
    skills = request.form["skills"]
    projects = request.form["projects"]
    template = request.form["template"]
    photo = request.files["photo"]
    filename = ""

    if photo and photo.filename != "":
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO resumes
        (fullname,email,phone,address,education,skills,projects,photo,template)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        fullname, email, phone, address,
        education, skills, projects, filename,template
    ))

    mysql.connection.commit()
    cursor.close()

    return redirect("/my_resumes")

# MY RESUMES (MISSING BEFORE - FIXED)
@app.route("/my_resumes")
def my_resumes():

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM resumes")
    resumes = cursor.fetchall()
    cursor.close()

    return render_template("my_resumes.html", resumes=resumes)

# Edit
@app.route("/edit_resume/<int:id>")
def edit_resume(id):

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM resumes WHERE id=%s", (id,))
    resume = cursor.fetchone()
    cursor.close()

    return render_template("edit_resume.html", resume=resume)

# Update
@app.route("/update_resume/<int:id>", methods=["POST"])
def update_resume(id):

    fullname = request.form["fullname"]
    email = request.form["email"]
    phone = request.form["phone"]
    address = request.form["address"]
    education = request.form["education"]
    skills = request.form["skills"]
    projects = request.form["projects"]

    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE resumes
        SET fullname=%s,
            email=%s,
            phone=%s,
            address=%s,
            education=%s,
            skills=%s,
            projects=%s
        WHERE id=%s
    """, (
        fullname, email, phone,
        address, education, skills,
        projects, id
    ))

    mysql.connection.commit()
    cursor.close()

    return redirect("/my_resumes")

# Delete
@app.route("/delete_resume/<int:id>")
def delete_resume(id):

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM resumes WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()

    return redirect("/my_resumes")

# Preview
@app.route("/preview_resume/<int:id>")
def preview_resume(id):

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM resumes WHERE id=%s", (id,))
    resume = cursor.fetchone()
    cursor.close()

    if resume[9] == "modern":
        return render_template(
            "modern_template.html",
            resume=resume
        )

    elif resume[9] == "professional":
        return render_template(
            "professional_template.html",
            resume=resume
        )

    else:
        return render_template(
            "preview_resume.html",
            resume=resume
        )

    

@app.route("/download_pdf/<int:id>")
def download_pdf(id):

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM resumes WHERE id=%s", (id,))
    resume = cursor.fetchone()
    cursor.close()

    file_path = f"resume_{id}.pdf"

    c = canvas.Canvas(file_path)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "RESUME")

    c.setFont("Helvetica", 12)

    c.drawString(100, 750, f"Name: {resume[1]}")
    c.drawString(100, 730, f"Email: {resume[2]}")
    c.drawString(100, 710, f"Phone: {resume[3]}")
    c.drawString(100, 690, f"Address: {resume[4]}")

    c.drawString(100, 650, f"Education: {resume[5]}")
    c.drawString(100, 630, f"Skills: {resume[6]}")
    c.drawString(100, 610, f"Projects: {resume[7]}")

    c.save()

    return send_file(file_path, as_attachment=True)


@app.route("/ats_checker/<int:id>")
def ats_checker(id):

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM resumes WHERE id=%s", (id,))
    resume = cursor.fetchone()
    cursor.close()

    text = " ".join([str(x) for x in resume[1:8]])

    keywords = [
        "python",
        "java",
        "sql",
        "html",
        "css",
        "flask",
        "mysql",
        "communication",
        "teamwork",
        "project"
    ]

    score = 0
    found_keywords = []
    missing_keywords = []

    for word in keywords:
        if word.lower() in text.lower():
            score += 10
            found_keywords.append(word)
        else:
            missing_keywords.append(word)

    if score > 100:
        score = 100

    return render_template(
        "ats_checker.html",
        score=score,
        resume=resume,
        found_keywords=found_keywords,
        missing_keywords=missing_keywords
    )

if __name__ == "__main__":
    app.run(debug=True)

