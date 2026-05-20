from flask import Flask, render_template,request, redirect, session
from db import engine, Base, SessionLocal
import models
import PyPDF2
import docx
import json
import random
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ai import analyze_resume

load_dotenv()
 
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
 
GMAIL = os.getenv("GMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
 
Base.metadata.create_all(bind=engine)
 
def send_otp_email(to_email, otp):
    msg = MIMEMultipart()
    msg["From"] = GMAIL
    msg["To"] = to_email
    msg["Subject"] = "AI Career Copilot - Password Reset OTP"
 
    body = f"""
Hello,
 
Your OTP for password reset is:
 
{otp}
 
This OTP is valid for 10 minutes.
Do not share this with anyone.
 
- AI Career Copilot
"""
    msg.attach(MIMEText(body, "plain"))
 
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL, APP_PASSWORD)
        server.sendmail(GMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

#HOME
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login") 

#SIGNUP
@app.route("/signup", methods=["GET","POST"])
def signup():
    db=SessionLocal()

    if request.method =="POST":
        email = request.form.get("email")
        password = request.form.get("password")

        exixting_user = db.query(models.User).filter_by(email=email).first()
        if exixting_user:
            return "User already exists"
        
        user = models.User(email=email, password=password)
        db.add(user)
        db.commit()

        return redirect("/login")

    return render_template("signup.html")

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
 
        user = db.query(models.User).filter_by(email=email).first()
        if user and user.check_password(password):
            session["user"] = user.email
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid email or password")
 
    return render_template("login.html")

# FORGOT PASSWORD 
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        db = SessionLocal()
        user = db.query(models.User).filter_by(email=email).first()
 
        if not user:
            return render_template("forgot_password.html", error="Email not found!")
 
        otp = str(random.randint(100000, 999999))
        session["otp"] = otp
        session["otp_email"] = email
 
        sent = send_otp_email(email, otp)
        if sent:
            return redirect("/verify-otp")
        else:
            return render_template("forgot_password.html", error="Email send failed. Check Gmail settings.")
 
    return render_template("forgot_password.html")
 
# VERIFY OTP 
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "otp" not in session:
        return redirect("/forgot-password")
 
    if request.method == "POST":
        entered_otp = request.form.get("otp")
 
        if entered_otp == session["otp"]:
            session["otp_verified"] = True
            return redirect("/reset-password")
        else:
            return render_template("otp_verify.html", error="Invalid OTP! Try again.")
 
    return render_template("otp_verify.html")
 
# RESET PASSWORD 
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if not session.get("otp_verified"):
        return redirect("/forgot-password")
 
    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
 
        if new_password != confirm_password:
            return render_template("reset_password.html", error="Passwords do not match!")
 
        if len(new_password) < 6:
            return render_template("reset_password.html", error="Password must be at least 6 characters!")
 
        db = SessionLocal()
        user = db.query(models.User).filter_by(email=session["otp_email"]).first()
        user.set_password(new_password)
        db.commit()
 
        session.pop("otp", None)
        session.pop("otp_email", None)
        session.pop("otp_verified", None)
 
        return redirect("/login")
 
    return render_template("reset_password.html")

#DASHBOARD
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")
    
    result = None
    resume_text = ""
    user_goal = ""

    if request.method == "POST":
        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")

        file =  request.files.get("file")

        #file handling
        if file and file.filename != "":
            if file.filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text=""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {"error": f"PDF error: {str(e)}" }   

            elif file.filename.endswith(".docx"):
                try:
                    doc = docx.Document(file)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text +"\n"
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Docx error: {str(e)}"}        
    
    if resume_text and user_goal:
        try:
            result = analyze_resume(resume_text, user_goal)

            #save to db
            db = SessionLocal()
            user = db.query(models.User).filter_by(email=session["user"]).first()

            report = models.Reports(
                user_id = user.id,
                resume_text = resume_text,
                result = json.dumps(result)
            )

            db.add(report)
            db.commit()

        except Exception as e:
            result = {"error": f"AI error: {str(e)}"}

    return render_template(
        "dashboard.html",
        user = session["user"],
        result = result
    )  

#HISTORY
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")
 
    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()
    reports = db.query(models.Reports).filter_by(user_id=user.id).all()
 
    parsed_reports = []
    for r in reports:
        try:
            parsed_result = json.loads(r.result)
        except:
            parsed_result = {}
        parsed_reports.append({
            "resume": r.resume_text,
            "result": parsed_result
        })
 
    return render_template("history.html", reports=parsed_reports)

#LOGOUT
@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
