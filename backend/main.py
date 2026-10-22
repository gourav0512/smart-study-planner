from pathlib import Path
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "study_planner.db"
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Smart Study Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For this beginner project only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                branch TEXT NOT NULL,
                semester TEXT NOT NULL,
                plan_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                branch TEXT NOT NULL,
                semester TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subject_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                unit_name TEXT NOT NULL,
                weightage TEXT NOT NULL,
                important_questions TEXT NOT NULL,
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO subjects (name, branch, semester) VALUES (?, ?, ?)",
                ("Database Management System (DBMS)", "Computer Science", "4")
            )
            subject_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            sample_units = [
                ("Unit 1: DBMS Basics", "10-15%", "1. Explain DBMS and its advantages.\n2. Explain the three-schema architecture."),
                ("Unit 2: ER Model and Relational Model", "15-20%", "1. Explain ER diagrams with an example.\n2. Explain primary key and foreign key."),
                ("Unit 3: SQL", "20-25%", "1. Explain DDL, DML and DCL commands.\n2. Write SQL queries using joins and aggregate functions."),
                ("Unit 4: Normalization", "15-20%", "1. Explain 1NF, 2NF and 3NF.\n2. What are functional dependencies?"),
                ("Unit 5: Transactions", "15-20%", "1. Explain ACID properties.\n2. Explain serializability and concurrency control.")
            ]
            conn.executemany(
                "INSERT INTO subject_content (subject_id, unit_name, weightage, important_questions) VALUES (?, ?, ?, ?)",
                [(subject_id, *unit) for unit in sample_units]
            )
        conn.commit()

init_db()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PlanRequest(BaseModel):
    user_id: int
    goal: str
    academic_year: str
    branch: str
    semester: str

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/login")
def login(data: LoginRequest):
    if len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Password must contain at least 4 characters.")
    with get_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (data.email.lower(),)).fetchone()
        if user:
            # Demo-only login: this basic project compares the stored password directly.
            if user["password"] != data.password:
                raise HTTPException(status_code=401, detail="Incorrect password for this email.")
            user_id = user["id"]
        else:
            cursor = conn.execute(
                "INSERT INTO users (email, password, created_at) VALUES (?, ?, ?)",
                (data.email.lower(), data.password, datetime.now().isoformat(timespec="seconds"))
            )
            user_id = cursor.lastrowid
        conn.commit()
    return {"user_id": user_id, "email": data.email.lower(), "message": "Login successful."}

@app.post("/api/plan")
def create_plan(data: PlanRequest):
    if data.goal not in ["Backlogs", "Safe Score", "Good Marks (90%)"]:
        raise HTTPException(status_code=400, detail="Please choose a valid goal.")
    plan_lines = {
        "Backlogs": [
            "Focus first on pending/backlog subjects and their core concepts.",
            "Study 2 focused topics daily, then solve previous-year questions.",
            "Keep the final day of each week for revision and a short test."
        ],
        "Safe Score": [
            "Cover the syllabus evenly, prioritising frequently asked topics.",
            "Study concepts first, then practise important questions and PYQs.",
            "Revise short notes every week and take one timed test."
        ],
        "Good Marks (90%)": [
            "Aim for complete syllabus coverage with detailed concept clarity.",
            "Practise PYQs, numerical problems and long-answer writing regularly.",
            "Take timed mock tests and review every mistake before the exam."
        ],
    }
    plan_text = "\n".join(f"{index + 1}. {line}" for index, line in enumerate(plan_lines[data.goal]))
    with get_connection() as conn:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (data.user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please log in again.")
        cursor = conn.execute("""
            INSERT INTO study_plans
            (user_id, goal, academic_year, branch, semester, plan_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data.user_id, data.goal, data.academic_year, data.branch, data.semester,
              plan_text, datetime.now().isoformat(timespec="seconds")))
        plan_id = cursor.lastrowid
        conn.commit()
    return {"plan_id": plan_id, "plan_text": plan_text, "goal": data.goal,
            "academic_year": data.academic_year, "branch": data.branch, "semester": data.semester}

@app.get("/api/subjects")
def get_subjects(branch: str = "Computer Science", semester: str = "4"):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM subjects WHERE branch = ? AND semester = ? ORDER BY name",
            (branch, semester)
        ).fetchall()
        # Show the sample DBMS subject for any selected branch/semester if no matching sample exists.
        if not rows:
            rows = conn.execute("SELECT id, name FROM subjects ORDER BY name").fetchall()
    return {"subjects": [dict(row) for row in rows]}

@app.get("/api/subjects/{subject_id}/pyq")
def get_subject_content(subject_id: int, mode: str = "combined"):
    if mode not in ["combined", "unitwise"]:
        raise HTTPException(status_code=400, detail="Mode must be combined or unitwise.")
    with get_connection() as conn:
        subject = conn.execute("SELECT id, name FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found.")
        rows = conn.execute(
            "SELECT unit_name, weightage, important_questions FROM subject_content WHERE subject_id = ? ORDER BY id",
            (subject_id,)
        ).fetchall()
    units = [dict(row) for row in rows]
    if mode == "combined":
        questions = []
        for unit in units:
            for question in unit["important_questions"].splitlines():
                questions.append({"unit_name": unit["unit_name"], "question": question})
        return {"subject": dict(subject), "mode": mode, "units": units, "questions": questions}
    return {"subject": dict(subject), "mode": mode, "units": units, "questions": []}

# Serve the frontend from the same local server.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")
