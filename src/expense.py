import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import matplotlib.pyplot as plt

# DB setup
conn = sqlite3.connect("expenses.db")
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')
cur.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        category TEXT,
        amount REAL,
        date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
conn.commit()

# GUI Setup
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("650x600")

frame_login = tk.Frame(root)
frame_main = tk.Frame(root)
for frame in (frame_login, frame_main):
    frame.grid(row=0, column=0, sticky='nsew')

# Global state
current_user = None

# Frame switch
def show_frame(frame):
    frame.tkraise()

# Login/Register UI
tk.Label(frame_login, text="Login or Register", font=("Arial", 16)).pack(pady=20)
tk.Label(frame_login, text="Username").pack()
username_entry = tk.Entry(frame_login)
username_entry.pack()
tk.Label(frame_login, text="Password").pack()
password_entry = tk.Entry(frame_login, show="*")
password_entry.pack()

def login():
    global current_user
    u, p = username_entry.get(), password_entry.get()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user = cur.fetchone()
    if user:
        current_user = user
        load_data()
        show_frame(frame_main)
    else:
        messagebox.showerror("Error", "Invalid credentials")

def register():
    u, p = username_entry.get(), password_entry.get()
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
        conn.commit()
        messagebox.showinfo("Success", "Account created. You can log in.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists")

tk.Button(frame_login, text="Login", command=login).pack(pady=5)
tk.Button(frame_login, text="Register", command=register).pack(pady=5)

# Main Dashboard
tk.Label(frame_main, text="Welcome!", font=("Arial", 16)).pack(pady=10)

# Treeview for transaction list
tree = ttk.Treeview(frame_main, columns=("Type", "Category", "Amount", "Date"), show='headings')
for col in ("Type", "Category", "Amount", "Date"):
    tree.heading(col, text=col)
tree.pack()

# Input fields for transaction
tk.Label(frame_main, text="Type (Income/Expense)").pack()
type_entry = tk.Entry(frame_main)
type_entry.pack()
tk.Label(frame_main, text="Category").pack()
cat_entry = tk.Entry(frame_main)
cat_entry.pack()
tk.Label(frame_main, text="Amount").pack()
amt_entry = tk.Entry(frame_main)
amt_entry.pack()
tk.Label(frame_main, text="Date (YYYY-MM-DD)").pack()
date_entry = tk.Entry(frame_main)
date_entry.pack()

def add_transaction():
    t, c, a, d = type_entry.get(), cat_entry.get(), amt_entry.get(), date_entry.get()
    try:
        a = float(a)
    except:
        messagebox.showerror("Error", "Amount must be a number")
        return
    if not d:
        messagebox.showerror("Error", "Please enter a date")
        return
    cur.execute("INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)",
                (current_user[0], t, c, a, d))
    conn.commit()
    load_data()
    if t.lower() == "expense":
        check_overspending()

tk.Button(frame_main, text="Add", command=add_transaction).pack(pady=5)

def delete_selected():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No selection", "Select a row to delete")
        return
    item = tree.item(selected[0])['values']
    cur.execute("DELETE FROM transactions WHERE user_id=? AND type=? AND category=? AND amount=? AND date=?",
                (current_user[0], *item))
    conn.commit()
    load_data()

tk.Button(frame_main, text="Delete Selected", command=delete_selected).pack(pady=5)

# Month and Year selection for chart
months = [f"{i:02}" for i in range(1, 13)]
years = ["2024", "2025"]
month_var = tk.StringVar(value="01")
year_var = tk.StringVar(value="2025")

tk.Label(frame_main, text="Select Month & Year for Chart").pack()
ttk.Combobox(frame_main, textvariable=month_var, values=months, width=5).pack()
ttk.Combobox(frame_main, textvariable=year_var, values=years, width=5).pack()

def show_chart():
    m, y = month_var.get(), year_var.get()
    date_prefix = f"{y}-{m}"
    cur.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE user_id=? AND type='Expense' AND date LIKE ?
        GROUP BY category
    """, (current_user[0], f"{date_prefix}-%"))
    data = cur.fetchall()
    if not data:
        messagebox.showinfo("No data", f"No expenses for {m}/{y}.")
        return
    labels, sizes = zip(*data)
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title(f"Expense Distribution - {m}/{y}")
    plt.show()

tk.Button(frame_main, text="Show Chart", command=show_chart).pack(pady=5)

def check_overspending():
    cur.execute("SELECT SUM(amount) FROM transactions WHERE user_id=? AND type='Income'", (current_user[0],))
    income = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(amount) FROM transactions WHERE user_id=? AND type='Expense'", (current_user[0],))
    expense = cur.fetchone()[0] or 0
    if expense > income:
        messagebox.showwarning("Overspending!", "You are spending more than your income!")

def load_data():
    for row in tree.get_children():
        tree.delete(row)
    cur.execute("SELECT type, category, amount, date FROM transactions WHERE user_id=?", (current_user[0],))
    for row in cur.fetchall():
        tree.insert('', 'end', values=row)

# Start on login screen
show_frame(frame_login)
root.mainloop()
