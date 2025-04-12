import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar, DateEntry
from datetime import datetime, timedelta
import json
import os
from plyer import notification
from playsound import playsound
import threading
import time
import uuid

TASKS_FILE = "tasks.json"

class SmartTodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title(" Smart To-Do Planner")
        self.root.geometry("750x600")
        self.dark_mode = False

        self.tasks = []

        self.setup_styles()
        self.build_ui()
        self.load_tasks()
        self.start_reminder_thread()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))

    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(pady=10)

        tk.Label(top, text="Task:").grid(row=0, column=0, padx=5)
        self.task_entry = tk.Entry(top, width=30)
        self.task_entry.grid(row=0, column=1, padx=5)

        tk.Label(top, text="Category:").grid(row=0, column=2, padx=5)
        self.category_cb = ttk.Combobox(top, values=["Work", "Personal", "Health", "Other"])
        self.category_cb.grid(row=0, column=3, padx=5)

        tk.Label(top, text="Date:").grid(row=1, column=0)
        self.date_entry = DateEntry(top, date_pattern='dd-mm-yyyy')
        self.date_entry.grid(row=1, column=1)

        tk.Label(top, text="Time (HH:MM AM/PM):").grid(row=1, column=2)
        self.time_entry = tk.Entry(top, width=15)
        self.time_entry.grid(row=1, column=3)

        tk.Label(top, text="Repeat:").grid(row=2, column=0)
        self.repeat_cb = ttk.Combobox(top, values=["None", "Daily", "Hourly"])
        self.repeat_cb.grid(row=2, column=1)
        self.repeat_cb.set("None")

        tk.Button(top, text="Add Task", bg="#81c784", fg="white", command=self.add_task).grid(row=2, column=3)
        tk.Button(top, text="Update Task", bg="#64b5f6", fg="white", command=self.update_task).grid(row=2, column=2)
        tk.Button(top, text="Toggle Dark Mode", command=self.toggle_dark_mode).grid(row=2, column=4)

        self.tree = ttk.Treeview(self.root, columns=("ID", "Task", "Category", "Date", "Time", "Repeat"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=0, stretch=False)
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tk.Button(self.root, text="Delete Selected", bg="#e57373", fg="white", command=self.delete_task).pack(pady=5)

    def add_task(self):
        task = self.task_entry.get().strip()
        cat = self.category_cb.get().strip() or "Other"
        date = self.date_entry.get_date()
        time_str = self.time_entry.get().strip()
        repeat = self.repeat_cb.get()

        if not task or not time_str:
            messagebox.showwarning("Missing Data", "Enter task and time.")
            return

        try:
            full_dt = datetime.strptime(f"{date.strftime('%d-%m-%Y')} {time_str}", "%d-%m-%Y %I:%M %p")
        except:
            messagebox.showerror("Invalid Time", "Time format: HH:MM AM/PM")
            return

        task_id = str(uuid.uuid4())
        self.tasks.append({"id": task_id, "task": task, "category": cat, "datetime": full_dt.strftime("%Y-%m-%d %H:%M"), "repeat": repeat})
        self.tree.insert("", "end", values=(task_id, task, cat, full_dt.strftime('%d-%m-%Y'), full_dt.strftime('%I:%M %p'), repeat))
        self.save_tasks()

        notification.notify(title="Task Added", message=f"{task} at {full_dt.strftime('%I:%M %p')} [{repeat}]", timeout=2)

        self.task_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)

    def update_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a task to update.")
            return

        task_id = self.tree.item(selected[0])['values'][0]
        task = self.task_entry.get().strip()
        cat = self.category_cb.get().strip() or "Other"
        date = self.date_entry.get_date()
        time_str = self.time_entry.get().strip()
        repeat = self.repeat_cb.get()

        if not task or not time_str:
            messagebox.showwarning("Missing Data", "Enter task and time.")
            return

        try:
            full_dt = datetime.strptime(f"{date.strftime('%d-%m-%Y')} {time_str}", "%d-%m-%Y %I:%M %p")
        except:
            messagebox.showerror("Invalid Time", "Time format: HH:MM AM/PM")
            return

        for index, t in enumerate(self.tasks):
            if t["id"] == task_id:
                self.tasks[index] = {
                    "id": task_id,
                    "task": task,
                    "category": cat,
                    "datetime": full_dt.strftime("%Y-%m-%d %H:%M"),
                    "repeat": repeat
                }
                break

        self.tree.item(selected[0], values=(task_id, task, cat, full_dt.strftime('%d-%m-%Y'), full_dt.strftime('%I:%M %p'), repeat))
        self.save_tasks()

        notification.notify(title="Task Updated", message=f"{task} at {full_dt.strftime('%I:%M %p')} [{repeat}]", timeout=2)

    def delete_task(self):
        selected = self.tree.selection()
        for item in selected:
            task_id = self.tree.item(item)['values'][0]
            self.tasks = [t for t in self.tasks if t["id"] != task_id]
            self.tree.delete(item)
        self.save_tasks()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        bg = "#212121" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"
        self.root.config(bg=bg)
        for widget in self.root.winfo_children():
            try:
                widget.config(bg=bg, fg=fg)
            except:
                pass

    def save_tasks(self):
        with open(TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f)

    def load_tasks(self):
        if not os.path.exists(TASKS_FILE): return
        with open(TASKS_FILE, 'r') as f:
            self.tasks = json.load(f)

        for t in self.tasks:
            if "id" not in t:
                t["id"] = str(uuid.uuid4())

        self.save_tasks()

        for t in self.tasks:
            dt = datetime.strptime(t["datetime"], "%Y-%m-%d %H:%M")
            self.tree.insert("", "end", values=(t["id"], t["task"], t["category"], dt.strftime('%d-%m-%Y'), dt.strftime('%I:%M %p'), t["repeat"]))

    def start_reminder_thread(self):
        threading.Thread(target=self.check_reminders, daemon=True).start()

    def check_reminders(self):
        while True:
            now = datetime.now().replace(second=0, microsecond=0)
            for i, task in enumerate(list(self.tasks)):
                task_time = datetime.strptime(task["datetime"], "%Y-%m-%d %H:%M")
                if task_time == now:
                    notification.notify(title="⏰ Reminder", message=f"{task['task']} ({task['category']})", timeout=10)
                    try:
                        playsound("alarm.mp3")
                    except:
                        pass
                    if task["repeat"] == "Daily":
                        task_time += timedelta(days=1)
                        task["datetime"] = task_time.strftime("%Y-%m-%d %H:%M")
                    elif task["repeat"] == "Hourly":
                        task_time += timedelta(hours=1)
                        task["datetime"] = task_time.strftime("%Y-%m-%d %H:%M")
                    else:
                        self.tasks.remove(task)
                    self.save_tasks()
            time.sleep(30)

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartTodoApp(root)
    root.mainloop()
