# daily_checklist_firestore.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
from zoneinfo import ZoneInfo

# ---------- Firestore setup ----------
firebase_config = json.loads(st.secrets["firebase"])
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()
pacific = ZoneInfo("America/Los_Angeles")

# ---------- Helper functions ----------
def get_today():
    return datetime.now(pacific).date().isoformat()

def get_streak(username):
    """Compute consecutive streak of days where all default tasks were completed."""
    days_ref = db.collection("tasks").document(username).collection("days")
    docs = days_ref.stream()
    completed_days = []
    for doc in docs:
        data = doc.to_dict()
        if data and all(data.get("tasks", {}).values()):
            completed_days.append(doc.id)

    completed_days = sorted(completed_days)
    if not completed_days:
        return 0

    today = datetime.now(pacific).date()
    streak = 0
    for i in range(len(completed_days) - 1, -1, -1):
        day = datetime.date.fromisoformat(completed_days[i])
        # count backward consecutive days including today if applicable
        if today - day == datetime.timedelta(days=streak):
            streak += 1
        else:
            break
    return streak

def calc_score(data):
    total = len(data.get("tasks", {}))
    done = 0
    for val in data['tasks'].values():
        if isinstance(val, bool) and val:
            done += 1 
        elif isinstance(val, (tuple, list)) and val[0] >= val[1]:
            done += 1
    return done, total

def calc_grade(data):
    done, total = calc_score(data)
    score = float(done) / float(total)
    if score < 0.7:
        return "D"
    if score < 0.8:
        return "C"
    if score < 0.9:
        return "B"
    if score < 0.95:
        return "A"
    if score <= 1.0: 
        return "S"
    return "S+"

# ---------- App ----------
st.title("✅ Daily Leveling")

username = st.text_input("Enter your username:")
if not username:
    st.stop()

today = get_today()
doc_ref = db.collection("tasks").document(username).collection("days").document(today)

# Load or initialize today
if "last_saved" not in st.session_state:
    doc = doc_ref.get()
    if doc.exists:
        user_data = doc.to_dict()
        st.session_state.last_saved = doc.to_dict()
    else:
        st.session_state.last_saved = {} # empty

user_data = {
    "tasks": {
        "100 Push-ups": (0, 100), 
        "10 mins plank": (0, 10), 
        "100 Squats": (0, 100),
        "Drink 8 Glasses of Water": (0, 8),
        "Read 15 min": False, 
        "Guitar + Singing": False,
        "Writing": False,
        "Draw": False,
        },
    "custom_tasks": []
}
    
new_user_data = {**user_data, **st.session_state.last_saved}
tasks = new_user_data["tasks"]
custom_tasks = new_user_data["custom_tasks"]
grade = calc_grade(new_user_data)
st.subheader(f"Tasks for {today}, Grade: {grade}")
st.caption(f"🔥 Current streak: {get_streak(username)} day(s)")

# Default tasks
for task, old_value in tasks.items():
    if isinstance(tasks[task], bool):
        done = st.checkbox(task, value=tasks[task], key=f"{username}_{task}")
        tasks[task] = done
    elif isinstance(tasks[task], (tuple, list)):
        max_value = old_value[1]
        old_value = old_value[0]
        new_value = st.number_input(task, value=int(old_value), min_value=0, max_value=max_value, step=1, key=f"{username}_{task}")
        if new_value != old_value:
            # Update local state and Firestore
            tasks[task] = (new_value, max_value)
            new_user_data['tasks'] = tasks
            doc_ref.set(new_user_data)
            st.session_state.last_saved = new_user_data

# Custom tasks (side-by-side layout)
st.markdown("### Custom Tasks")
for i, task in enumerate(list(custom_tasks)):
    col1, col2 = st.columns([8, 1])
    with col1:
        done = st.checkbox(task["name"], value=task["done"], key=f"{username}_custom_{i}")
        task["done"] = done
    with col2:
        if st.button("🗑️", key=f"del_{i}", help="Delete this task"):
            custom_tasks.pop(i)
            doc_ref.set({"tasks": tasks, "custom_tasks": custom_tasks})
            st.rerun()

st.markdown("---")
new_task = st.text_input("Add a new custom task:")
if st.button("Add Task") and new_task.strip():
    custom_tasks.append({"name": new_task.strip(), "done": False})
    doc_ref.set({"tasks": tasks, "custom_tasks": custom_tasks})
    st.rerun()

# Save progress automatically
doc_ref.set({"tasks": tasks, "custom_tasks": custom_tasks})

# ---------- History viewer ----------
with st.expander("📆 View task history"):
    days_ref = db.collection("tasks").document(username).collection("days")
    docs = days_ref.stream()
    history = []
    for doc in docs:
        data = doc.to_dict()
        if data:
            done, total = calc_score(data)
            history.append((doc.id, done, total))
    history.sort(reverse=True)

    if history:
        for day, done, total in history:
            grade = calc_grade(data)
            st.write(f"{day}: {grade}: {done}/{total} default tasks completed")
    else:
        st.info("No history yet — complete a few days to see your streak!")

