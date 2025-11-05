import streamlit as st
import json
import datetime
from pathlib import Path

DATA_FILE = Path("user_tasks.json")

# ---------- helper functions ----------
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_today_key():
    return datetime.date.today().isoformat()

# ---------- app ----------
st.title("✅ Daily Checklist")

username = st.text_input("Enter your username:")
if not username:
    st.stop()

data = load_data()
today = get_today_key()

# Initialize user data
if username not in data:
    data[username] = {}
if today not in data[username]:
    # Default daily tasks
    data[username][today] = {
        "tasks": {
            "Exercise": False,
            "Read for 15 min": False,
            "Plan tomorrow": False,
        },
        "custom_tasks": []
    }
    save_data(data)

user_today = data[username][today]
tasks = user_today["tasks"]
custom_tasks = user_today["custom_tasks"]

st.subheader(f"Tasks for {today}")

# Display default tasks
for task in list(tasks.keys()):
    done = st.checkbox(task, value=tasks[task], key=f"{username}_{task}")
    tasks[task] = done

# Display custom tasks
for i, task in enumerate(list(custom_tasks)):
    done = st.checkbox(task["name"], value=task["done"], key=f"{username}_custom_{i}")
    task["done"] = done
    if st.button(f"Delete '{task['name']}'", key=f"del_{i}"):
        custom_tasks.pop(i)
        save_data(data)
        st.rerun()

st.markdown("---")
new_task = st.text_input("Add a new custom task:")
if st.button("Add Task") and new_task.strip():
    custom_tasks.append({"name": new_task.strip(), "done": False})
    save_data(data)
    st.rerun()

# ---------- save progress ----------
data[username][today]["tasks"] = tasks
data[username][today]["custom_tasks"] = custom_tasks
save_data(data)

st.success("Progress saved automatically!")

# ---------- cleanup old days ----------
if len(data[username]) > 7:
    # keep last 7 days for each user
    all_days = sorted(data[username].keys())
    for old_day in all_days[:-7]:
        del data[username][old_day]
    save_data(data)