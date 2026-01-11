import uuid
import datetime
import json
from db import get_db


def handle_message(user_id, message, image_path=None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM user_state WHERE phone=?", (user_id,))
    state = cur.fetchone()

    # First interaction
    if state is None:
        cur.execute(
            "INSERT INTO user_state VALUES (?, ?, ?)",
            (user_id, "START", "")
        )
        conn.commit()
        return welcome_message()

    step = state["step"]
    temp_data = state["temp_data"]

    # ---------- IMAGE RECEIVED FIRST ----------
    if message == "[IMAGE]" and image_path:
        data = {"image_path": image_path}
        update_state(user_id, "DESCRIPTION", json.dumps(data))
        return "Image received ✅\nPlease describe your grievance:"

    # ---------- START MENU ----------
    if step == "START":
        if message.strip() == "1":
            update_state(user_id, "CATEGORY")
            return category_message()
        elif message.strip() == "2":
            update_state(user_id, "TRACK")
            return "Please enter your Grievance ID:"
        else:
            return welcome_message()

    # ---------- CATEGORY ----------
    if step == "CATEGORY":
        data = {"category": message.strip()}

        if temp_data:
            data.update(json.loads(temp_data))

        if image_path:
            data["image_path"] = image_path

        update_state(user_id, "DESCRIPTION", json.dumps(data))
        return "Please describe your grievance:"

    # ---------- DESCRIPTION ----------
    if step == "DESCRIPTION":
        data = json.loads(temp_data)
        data["description"] = message.strip()
        update_state(user_id, "ANON", json.dumps(data))
        return "Submit anonymously?\n1. Yes\n2. No"

    # ---------- ANONYMOUS ----------
    if step == "ANON":
        data = json.loads(temp_data)

        if message.strip() == "1":
            grievance_id = save_grievance(
                user_id,
                data.get("category", "General"),
                data.get("description", ""),
                image_path=data.get("image_path"),
                anonymous=True
            )
            clear_state(user_id)
            return f"Grievance Registered ✅\nID: {grievance_id}"

        elif message.strip() == "2":
            update_state(user_id, "NAME", temp_data)
            return "Please enter your name:"

    # ---------- NAME ----------
    if step == "NAME":
        data = json.loads(temp_data)
        grievance_id = save_grievance(
            user_id,
            data.get("category", "General"),
            data.get("description", ""),
            image_path=data.get("image_path"),
            anonymous=False,
            name=message.strip()
        )
        clear_state(user_id)
        return f"Grievance Registered ✅\nID: {grievance_id}"

    # ---------- TRACK STATUS ----------
    if step == "TRACK":
        cur.execute(
            "SELECT status FROM grievances WHERE grievance_id=?",
            (message.strip(),)
        )
        row = cur.fetchone()
        clear_state(user_id)

        if row:
            return f"Status of {message}: {row['status']}"
        else:
            return "Invalid Grievance ID ❌"

    return welcome_message()


# ---------- Helper Functions ----------

def welcome_message():
    return (
        "Welcome to Grievance Redressal System\n"
        "1. Register Grievance\n"
        "2. Track Status"
    )


def category_message():
    return (
        "Select Category:\n"
        "Academic\n"
        "Hostel\n"
        "Faculty\n"
        "Infrastructure"
    )


def update_state(user_id, step, temp=""):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE user_state SET step=?, temp_data=? WHERE phone=?",
        (step, temp, user_id)
    )
    conn.commit()


def save_grievance(user_id, category, description, image_path=None, anonymous=False, name=""):
    conn = get_db()
    cur = conn.cursor()

    grievance_id = "GRV-" + str(uuid.uuid4())[:8]
    created_at = datetime.datetime.now().isoformat()

    cur.execute("""
        INSERT INTO grievances
        (grievance_id, phone, category, description, image_path, anonymous, name, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        grievance_id,
        user_id,
        category,
        description,
        image_path,
        1 if anonymous else 0,
        name,
        "Pending",
        created_at
    ))

    conn.commit()
    return grievance_id


def clear_state(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_state WHERE phone=?", (user_id,))
    conn.commit()
