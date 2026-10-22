# Smart Study Planner

A beginner-friendly student planner using HTML, CSS, JavaScript, FastAPI and SQLite. The website follows the provided workflow: Login → Choose Goal → Academic Details → Generate Plan → Choose Subject → Combined/Unit-wise PYQs.

## Project structure

```text
smart-study-planner/
├── backend/
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── requirements.txt
└── README.md
```

## Run in VS Code (Windows)

1. Install Python 3.10 or newer and VS Code.
2. Open the `smart-study-planner` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

5. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

6. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

7. Start the backend and website from the project root:

   ```powershell
   uvicorn backend.main:app --reload
   ```

8. Open **http://127.0.0.1:8000** in your browser. Keep the terminal running while using the site.
9. Optional: open **http://127.0.0.1:8000/docs** to inspect and test the API endpoints.

## Where is data saved?

On the first run, SQLite automatically creates `study_planner.db` in the project root. It contains:
- `users`: email and demo password
- `study_plans`: chosen goal, academic year, branch, semester and generated plan
- `subjects`: sample subject list
- `subject_content`: sample unit weightage and important questions

The database is created automatically when the backend starts. Do not delete it if you want to keep saved demo data.

## API endpoints

- `POST /api/login` — creates a demo account on first use, or checks the email/password for an existing account.
- `POST /api/plan` — saves the selected goal and academic details, then returns a generated study plan.
- `GET /api/subjects?branch=Computer%20Science&semester=4` — returns sample subjects.
- `GET /api/subjects/1/pyq?mode=combined` — returns questions from all units.
- `GET /api/subjects/1/pyq?mode=unitwise` — returns unit-wise weightage and questions.
- `GET /api/health` — basic server health check.

## Important demo limitation

This is a learning prototype, not a production authentication system. The password is stored as plain text to keep the initial code easy to understand; do not use real or reused passwords. Before real students use it, password hashing, HTTPS, proper session/token handling, and stricter CORS settings would be needed. The PYQs and unit weightages are sample content, not verified official exam material.
