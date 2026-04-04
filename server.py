from __future__ import annotations

import json
import os
from functools import wraps
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data_store.json"

DEFAULT_DATA = {
    "next_user_id": 2,
    "next_student_id": 9,
    "users": [
        {
            "id": 1,
            "full_name": "Admin User",
            "email": "admin@university.edu",
            "password_hash": generate_password_hash("admin123"),
        }
    ],
    "students": [
        {"id": 1, "student_code": "STU001", "full_name": "Arjun Sharma", "email": "arjun@university.edu", "department": "Computer Science", "year_label": "Year 3", "gpa": 1.8, "attendance": 62, "engagement": 45},
        {"id": 2, "student_code": "STU002", "full_name": "Priya Patel", "email": "priya@university.edu", "department": "Electronics", "year_label": "Year 2", "gpa": 2.1, "attendance": 71, "engagement": 58},
        {"id": 3, "student_code": "STU003", "full_name": "Rahul Verma", "email": "rahul@university.edu", "department": "Mechanical", "year_label": "Year 4", "gpa": 3.4, "attendance": 90, "engagement": 82},
        {"id": 4, "student_code": "STU004", "full_name": "Sneha Nair", "email": "sneha@university.edu", "department": "Computer Science", "year_label": "Year 1", "gpa": 2.8, "attendance": 78, "engagement": 61},
        {"id": 5, "student_code": "STU005", "full_name": "Kiran Kumar", "email": "kiran@university.edu", "department": "Civil", "year_label": "Year 2", "gpa": 1.5, "attendance": 55, "engagement": 39},
        {"id": 6, "student_code": "STU006", "full_name": "Ananya Singh", "email": "ananya@university.edu", "department": "Information Technology", "year_label": "Year 3", "gpa": 3.7, "attendance": 95, "engagement": 91},
        {"id": 7, "student_code": "STU007", "full_name": "Rohan Mehta", "email": "rohan@university.edu", "department": "Electronics", "year_label": "Year 4", "gpa": 2.3, "attendance": 68, "engagement": 57},
        {"id": 8, "student_code": "STU008", "full_name": "Divya Rao", "email": "divya@university.edu", "department": "Computer Science", "year_label": "Year 2", "gpa": 3.1, "attendance": 85, "engagement": 74},
    ],
}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "edushield-dev-secret")


def load_data() -> dict:
    if not DATA_PATH.exists():
        save_data(DEFAULT_DATA)
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_data(data: dict) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            flash("Please log in to access the dashboard.", "warning")
            return redirect(url_for("auth"))
        return view(**kwargs)

    return wrapped_view


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    data = load_data()
    return next((user for user in data["users"] if user["id"] == user_id), None)


@app.context_processor
def inject_global_template_data():
    return {"current_user": get_current_user()}


def compute_risk(student: dict) -> dict[str, int | str]:
    gpa_ratio = max(0, min(100, int((4.0 - float(student["gpa"])) / 4.0 * 100)))
    attendance_penalty = max(0, 100 - int(student["attendance"]))
    engagement_penalty = max(0, 100 - int(student["engagement"]))
    risk_score = round(gpa_ratio * 0.45 + attendance_penalty * 0.35 + engagement_penalty * 0.20)

    if risk_score >= 50:
        risk_level = "High"
    elif risk_score >= 25:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {"risk_score": risk_score, "risk_level": risk_level}


def fetch_students(search: str = "", risk_filter: str = "All Risks") -> list[dict]:
    data = load_data()
    students = []
    for row in data["students"]:
        if search:
            token = search.lower()
            haystack = " ".join([row["full_name"], row["student_code"], row["email"], row["department"]]).lower()
            if token not in haystack:
                continue

        student = dict(row)
        student.update(compute_risk(row))
        students.append(student)

    if risk_filter != "All Risks":
        expected_level = risk_filter.replace(" Risk", "")
        students = [student for student in students if student["risk_level"] == expected_level]

    return students


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/auth")
def auth():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("auth.html")


@app.post("/login")
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    data = load_data()
    user = next((item for item in data["users"] if item["email"] == email), None)
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth"))

    session.clear()
    session["user_id"] = user["id"]
    flash("Welcome back. You're now inside the dashboard.", "success")
    return redirect(url_for("dashboard"))


@app.post("/signup")
def signup():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    data = load_data()

    if not full_name or not email or not password:
        flash("Please complete every field to create your account.", "warning")
        return redirect(url_for("auth"))

    if any(user["email"] == email for user in data["users"]):
        flash("An account with that email already exists. Please log in instead.", "warning")
        return redirect(url_for("auth"))

    new_user = {
        "id": data["next_user_id"],
        "full_name": full_name,
        "email": email,
        "password_hash": generate_password_hash(password),
    }
    data["next_user_id"] += 1
    data["users"].append(new_user)
    save_data(data)

    session.clear()
    session["user_id"] = new_user["id"]
    flash("Account created successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    search = request.args.get("search", "").strip()
    risk_filter = request.args.get("risk", "All Risks")
    students = fetch_students(search, risk_filter)
    stats = {
        "total": len(students),
        "high": sum(1 for student in students if student["risk_level"] == "High"),
        "medium": sum(1 for student in students if student["risk_level"] == "Medium"),
        "low": sum(1 for student in students if student["risk_level"] == "Low"),
    }
    return render_template("dashboard.html", students=students, search=search, risk_filter=risk_filter, stats=stats)


@app.route("/students/new", methods=["GET", "POST"])
@login_required
def create_student():
    if request.method == "POST":
        data = load_data()
        data["students"].append(
            {
                "id": data["next_student_id"],
                "student_code": request.form["student_code"].strip(),
                "full_name": request.form["full_name"].strip(),
                "email": request.form["email"].strip(),
                "department": request.form["department"].strip(),
                "year_label": request.form["year_label"].strip(),
                "gpa": float(request.form["gpa"]),
                "attendance": int(request.form["attendance"]),
                "engagement": int(request.form["engagement"]),
            }
        )
        data["next_student_id"] += 1
        save_data(data)
        flash("Student added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("student_form.html", page_title="Add Student", student=None)


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id: int):
    data = load_data()
    student = next((item for item in data["students"] if item["id"] == student_id), None)
    if student is None:
        flash("Student not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        student.update(
            {
                "student_code": request.form["student_code"].strip(),
                "full_name": request.form["full_name"].strip(),
                "email": request.form["email"].strip(),
                "department": request.form["department"].strip(),
                "year_label": request.form["year_label"].strip(),
                "gpa": float(request.form["gpa"]),
                "attendance": int(request.form["attendance"]),
                "engagement": int(request.form["engagement"]),
            }
        )
        save_data(data)
        flash("Student details updated.", "success")
        return redirect(url_for("dashboard"))

    return render_template("student_form.html", page_title="Edit Student", student=student)


@app.post("/students/<int:student_id>/delete")
@login_required
def delete_student(student_id: int):
    data = load_data()
    data["students"] = [student for student in data["students"] if student["id"] != student_id]
    save_data(data)
    flash("Student deleted.", "success")
    return redirect(url_for("dashboard"))


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth"))


if not DATA_PATH.exists():
    save_data(DEFAULT_DATA)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 5000)))
