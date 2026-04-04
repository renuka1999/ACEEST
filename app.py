"""
ACEest Fitness & Gym — Flask Web Application with Dashboard UI
Version: 2.0.0
"""

from flask import Flask, jsonify, request, render_template
import sqlite3
import os
from datetime import date

app = Flask(__name__)

DB_NAME = os.environ.get("DB_NAME", "aceest_fitness.db")

# ---------- FITNESS PROGRAMS ----------
PROGRAMS = {
    "Fat Loss": {
        "workout": ("Mon: 5x5 Back Squat + AMRAP | Tue: EMOM 20min Cardio | Wed: Bench Press + 21-15-9 | "
        "Thu: Deadlifts/Box Jumps | Fri: Active Recovery"),
        "diet": ("Breakfast: 3 Egg Whites + Oats | Lunch: Grilled Chicken + Brown Rice | "
        "Dinner: Fish + Millet Roti | Target: 2000 kcal"),
        "calories": 2000
    },
    "Muscle Gain": {
        "workout": ("Mon: Squat 5x5 | Tue: Bench 5x5 | Wed: Deadlift 4x6 | Thu: Front Squat 4x8 | "
        "Fri: Incline Press 4x10 | Sat: Rows 4x10"),
        "diet": ("Breakfast: 4 Eggs + PB Oats | Lunch: Chicken Biryani | "
        "Dinner: Mutton Curry + Rice | Target: 3200 kcal"),
        "calories": 3200
    },
    "Beginner": {
        "workout": "Circuit: Air Squats, Ring Rows, Push-ups. Focus on Technique & Form",
        "diet": "Balanced Meals: Idli-Sambar, Rice-Dal, Chapati. Protein: 120g/day",
        "calories": 2500
    }
}

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            age INTEGER,
            weight REAL,
            program TEXT,
            calories INTEGER,
            membership_status TEXT DEFAULT 'Active'
        );
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            week TEXT,
            adherence INTEGER
        );
    """)
    conn.commit()
    conn.close()


# ---------- DASHBOARD UI ----------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ---------- REST API ----------

@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/api/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": list(PROGRAMS.keys()), "details": PROGRAMS}), 200


@app.route("/api/programs/<string:program_name>", methods=["GET"])
def get_program(program_name):
    program = PROGRAMS.get(program_name)
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404
    return jsonify({"program": program_name, "details": program}), 200


@app.route("/api/clients", methods=["GET"])
def get_clients():
    conn = get_db()
    clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify({"clients": [dict(c) for c in clients]}), 200


@app.route("/api/clients", methods=["POST"])
def add_client():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Client name is required"}), 400

    name = data["name"].strip()
    age = data.get("age")
    weight = data.get("weight")
    program = data.get("program")
    calories = PROGRAMS.get(program, {}).get("calories") if program else None
    membership_status = data.get("membership_status", "Active")

    if program and program not in PROGRAMS:
        return jsonify({"error": f"Invalid program. Choose from: {list(PROGRAMS.keys())}"}), 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO clients (name, age, weight, program, calories, membership_status) VALUES (?,?,?,?,?,?)",
            (name, age, weight, program, calories, membership_status)
        )
        conn.commit()
        client = dict(conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone())
        conn.close()
        return jsonify({"message": "Client added successfully", "client": client}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"Client '{name}' already exists"}), 409


@app.route("/api/clients/<string:name>", methods=["GET"])
def get_client(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not client:
        return jsonify({"error": f"Client '{name}' not found"}), 404
    return jsonify({"client": dict(client)}), 200


@app.route("/api/clients/<string:name>", methods=["DELETE"])
def delete_client(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    conn.execute("DELETE FROM clients WHERE name=?", (name,))
    conn.execute("DELETE FROM workouts WHERE client_name=?", (name,))
    conn.execute("DELETE FROM progress WHERE client_name=?", (name,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Client '{name}' deleted successfully"}), 200


@app.route("/api/clients/<string:name>/workout", methods=["POST"])
def add_workout(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({"error": "Workout data is required"}), 400

    workout_type = data.get("workout_type", "General")
    duration_min = data.get("duration_min", 60)
    notes = data.get("notes", "")
    workout_date = data.get("date", date.today().isoformat())

    conn.execute(
        "INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
        (name, workout_date, workout_type, duration_min, notes)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Workout logged successfully"}), 201


@app.route("/api/clients/<string:name>/workouts", methods=["GET"])
def get_workouts(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    workouts = conn.execute(
        "SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (name,)
    ).fetchall()
    conn.close()
    return jsonify({"client": name, "workouts": [dict(w) for w in workouts]}), 200


@app.route("/api/clients/<string:name>/workouts/<int:workout_id>", methods=["DELETE"])
def delete_workout(name, workout_id):
    conn = get_db()
    workout = conn.execute("SELECT * FROM workouts WHERE id=? AND client_name=?", (workout_id, name)).fetchone()
    if not workout:
        conn.close()
        return jsonify({"error": "Workout not found"}), 404
    conn.execute("DELETE FROM workouts WHERE id=?", (workout_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Workout deleted"}), 200


@app.route("/api/clients/<string:name>/progress", methods=["POST"])
def log_progress(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404

    data = request.get_json()
    if not data:
        conn.close()
        return jsonify({"error": "Progress data is required"}), 400

    adherence = data.get("adherence")
    if adherence is None or not (0 <= int(adherence) <= 100):
        conn.close()
        return jsonify({"error": "Adherence must be between 0 and 100"}), 400

    week = data.get("week", date.today().strftime("%Y-W%U"))
    conn.execute(
        "INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)",
        (name, week, adherence)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Progress logged", "week": week, "adherence": adherence}), 201


@app.route("/api/clients/<string:name>/progress", methods=["GET"])
def get_progress(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    if not client:
        conn.close()
        return jsonify({"error": f"Client '{name}' not found"}), 404
    rows = conn.execute(
        "SELECT * FROM progress WHERE client_name=? ORDER BY id", (name,)
    ).fetchall()
    conn.close()
    return jsonify({"client": name, "progress": [dict(r) for r in rows]}), 200


@app.route("/api/clients/<string:name>/bmi", methods=["GET"])
def calculate_bmi(name):
    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not client:
        return jsonify({"error": f"Client '{name}' not found"}), 404

    height_cm = request.args.get("height_cm", type=float)
    if not height_cm:
        return jsonify({"error": "height_cm query parameter is required"}), 400

    weight = client["weight"]
    if not weight:
        return jsonify({"error": f"No weight recorded for '{name}'"}), 400

    height_m = height_cm / 100
    bmi = round(weight / (height_m ** 2), 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return jsonify({"client": name, "weight_kg": weight, "height_cm": height_cm, "bmi": bmi, "category": category}), 200


@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    total_clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    active_clients = conn.execute("SELECT COUNT(*) FROM clients WHERE membership_status='Active'").fetchone()[0]
    total_workouts = conn.execute("SELECT COUNT(*) FROM workouts").fetchone()[0]
    avg_adherence_row = conn.execute("SELECT AVG(adherence) FROM progress").fetchone()[0]
    avg_adherence = round(avg_adherence_row, 1) if avg_adherence_row else 0

    program_counts = conn.execute(
        "SELECT program, COUNT(*) as cnt FROM clients WHERE program IS NOT NULL GROUP BY program"
    ).fetchall()
    conn.close()

    return jsonify({
        "total_clients": total_clients,
        "active_clients": active_clients,
        "total_workouts": total_workouts,
        "avg_adherence": avg_adherence,
        "program_distribution": {row[0]: row[1] for row in program_counts}
    }), 200


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
