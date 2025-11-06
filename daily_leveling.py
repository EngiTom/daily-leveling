# daily_checklist_firestore.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json

# ---------- Firestore setup ----------
firebase_config = json.loads(st.secrets["firebase"])
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------- Helper functions ----------
def get_today():
    return datetime.date.today().isoformat()

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

    today = datetime.date.today()
    streak = 0
    for i in range(len(completed_days) - 1, -1, -1):
        day = datetime.date.fromisoformat(completed_days[i])
        # count backward consecutive days including today if applicable
        if today - day == datetime.timedelta(days=streak):
            streak += 1
        else:
            break
    return streak

# ---------- App ----------
st.title("✅ Daily Checklist (Firestore Edition)")

username = st.text_input("Enter your username:")
if not username:
    st.stop()

today = get_today()
doc_ref = db.collection("tasks").document(username).collection("days").document(today)

# Load or initialize today
doc = doc_ref.get()
if doc.exists:
    user_data = doc.to_dict()
else:
    user_data = {
        "tasks": {"100 Push-ups": False, 
                  "10 mins plank": False, 
                  "100 Squats": False,
                  "Drink 8 Glasses of Water": False,
                  "Read 15 min": False, 
                  "Guitar + Singing": False,
                  "Writing": False,
                  "Draw": False,
                  "Plan tomorrow": False
                  },
        "custom_tasks": []
    }
    doc_ref.set(user_data)

tasks = user_data["tasks"]
custom_tasks = user_data["custom_tasks"]

st.subheader(f"Tasks for {today}")
st.caption(f"🔥 Current streak: {get_streak(username)} day(s)")

# Default tasks
for task in list(tasks.keys()):
    done = st.checkbox(task, value=tasks[task], key=f"{username}_{task}")
    tasks[task] = done

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
            total = len(data.get("tasks", {}))
            done = sum(1 for v in data["tasks"].values() if v)
            history.append((doc.id, done, total))
    history.sort(reverse=True)

    if history:
        for day, done, total in history:
            st.write(f"{day}: {done}/{total} default tasks completed")
    else:
        st.info("No history yet — complete a few days to see your streak!")

