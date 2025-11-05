# daily_checklist_firestore.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json

# --- FIX START ---
firebase_config = st.secrets["firebase"]
if isinstance(firebase_config, str):
    # Streamlit may load as a string literal
    firebase_config = json.loads(firebase_config.replace("'", '"'))
# --- FIX END ---

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Example sanity check
st.write("Firestore initialized ✅")

def get_today():
    return datetime.date.today().isoformat()

# ---------- App ----------
st.title("✅ Daily Checklist (Firestore Edition)")

username = st.text_input("Enter your username:")
if not username:
    st.stop()

today = get_today()
doc_ref = db.collection("tasks").document(username).collection("days").document(today)

# Load or initialize
doc = doc_ref.get()
if doc.exists:
    user_data = doc.to_dict()
else:
    user_data = {
        "tasks": {"Exercise": False, "Read 15 min": False, "Plan tomorrow": False},
        "custom_tasks": []
    }
    doc_ref.set(user_data)

tasks = user_data["tasks"]
custom_tasks = user_data["custom_tasks"]

st.subheader(f"Tasks for {today}")

# Default tasks
for task in list(tasks.keys()):
    done = st.checkbox(task, value=tasks[task], key=f"{username}_{task}")
    tasks[task] = done

# Custom tasks
for i, task in enumerate(list(custom_tasks)):
    done = st.checkbox(task["name"], value=task["done"], key=f"{username}_custom_{i}")
    task["done"] = done
    if st.button(f"Delete '{task['name']}'", key=f"del_{i}"):
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
st.success("Progress saved to Firestore!")

