from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import json
import os
from datetime import datetime
from openpyxl import Workbook
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ------------------ CONFIG ------------------
ACTIVE_FILE = "active_exams.json"
RESULT_FILE = "results.xlsx"
UPLOAD_FOLDER = "static"
ALLOWED_EXTENSIONS = {"xlsx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------------ HELPERS ------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_active():
    if not os.path.exists(ACTIVE_FILE):
        return {}
    with open(ACTIVE_FILE, "r") as f:
        return json.load(f)

def save_active(data):
    with open(ACTIVE_FILE, "w") as f:
        json.dump(data, f)


# ------------------ STUDENT ROUTES ------------------

@app.route("/")
def home():
    return render_template("login.html")   # student login page


@app.route("/login", methods=["POST"])
def login():
    student_id = request.form.get("student_id").strip()
    active = load_active()

    # Security check: prevent multiple logins
    if student_id in active:
        if active[student_id]["started"]:
            return "❌ You have already started the exam. Multiple logins are not allowed.", 403
        else:
            return "❌ You are already logged in and waiting for the exam.", 403

    # Otherwise, register student as waiting
    active[student_id] = {
        "started": False,
        "start_time": None,
        "score": None,
        "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_active(active)

    return redirect(url_for("wait", student_id=student_id))


@app.route("/wait/<student_id>")
def wait(student_id):
    return render_template("wait.html", student_id=student_id)


@app.route("/check_status/<student_id>")
def check_status(student_id):
    active = load_active()
    if student_id in active and active[student_id]["started"]:
        return jsonify({"active": True})
    return jsonify({"active": False})


@app.route("/exam/<student_id>")
def exam(student_id):
    return render_template("index.html", student_id=student_id)


# ------------------ PROCTOR/CONTROL ROUTES ------------------

@app.route("/control")
def control():
    active = load_active()
    return render_template("control.html", students=active)


@app.route("/start_exam/<student_id>", methods=["POST"])
def start_exam(student_id):
    active = load_active()
    if student_id in active:
        active[student_id]["started"] = True
        active[student_id]["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_active(active)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Student not found"})


@app.route("/reset", methods=["POST"])
def reset():
    save_active({})
    return jsonify({"success": True})


@app.route("/upload_questions", methods=["POST"])
def upload_questions():
    """Allow proctor to upload a new questions.xlsx file"""
    if "file" not in request.files:
        return "No file uploaded", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = secure_filename("questions.xlsx")  # overwrite
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return redirect(url_for("control"))
    return "Invalid file format. Please upload an .xlsx file", 400


# ------------------ RESULTS ------------------

@app.route("/submit_result/<student_id>", methods=["POST"])
def submit_result(student_id):
    """Receive exam score from student frontend"""
    data = request.get_json()
    score = data.get("score")

    active = load_active()
    if student_id in active:
        active[student_id]["score"] = score
        save_active(active)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Student not found"})


@app.route("/export_results")
def export_results():
    active = load_active()

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"

    # Headers
    ws.append(["Student ID", "Login Time", "Started", "Start Time", "Score"])

    # Data rows
    for sid, info in active.items():
        ws.append([
            sid,
            info.get("login_time", "-"),
            "Yes" if info["started"] else "No",
            info["start_time"] if info["start_time"] else "-",
            info["score"] if info["score"] is not None else "-"
        ])

    wb.save(RESULT_FILE)
    return send_file(RESULT_FILE, as_attachment=True)


# ------------------ MAIN ------------------

if __name__ == "__main__":
    app.run(debug=True)
