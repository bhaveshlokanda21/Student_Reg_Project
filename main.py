"""A small, self-contained student management system built with Tkinter and SQLite."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


DB_PATH = Path(__file__).with_name("students.db")
BG = "#f4f6fb"
INK = "#20283b"
MUTED = "#718096"
ACCENT = "#5267df"


class StudentDatabase:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                course TEXT NOT NULL,
                year TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        self.connection.commit()

    def all(self, query: str = "") -> list[sqlite3.Row]:
        term = f"%{query.strip()}%"
        return list(self.connection.execute(
            """SELECT * FROM students WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
               OR course LIKE ? OR year LIKE ? ORDER BY name COLLATE NOCASE""",
            (term, term, term, term, term),
        ))

    def save(self, values: tuple[str, ...], student_id: int | None = None) -> None:
        if student_id is None:
            self.connection.execute(
                "INSERT INTO students (name,email,phone,course,year) VALUES (?,?,?,?,?)", values
            )
        else:
            self.connection.execute(
                "UPDATE students SET name=?,email=?,phone=?,course=?,year=? WHERE id=?",
                (*values, student_id),
            )
        self.connection.commit()

    def delete(self, student_id: int) -> None:
        self.connection.execute("DELETE FROM students WHERE id=?", (student_id,))
        self.connection.commit()

    def stats(self) -> tuple[int, int]:
        total = self.connection.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        courses = self.connection.execute("SELECT COUNT(DISTINCT course) FROM students").fetchone()[0]
        return total, courses


class StudentForm(tk.Toplevel):
    def __init__(self, parent: "StudentApp", student: sqlite3.Row | None = None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.student = student
        self.title("Edit student" if student else "Add student")
        self.configure(bg="white")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result: tuple[str, ...] | None = None

        body = tk.Frame(self, bg="white", padx=28, pady=24)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="Student details", bg="white", fg=INK,
                 font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(body, text="Fields marked with * are required", bg="white", fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 16))

        self.vars: dict[str, tk.StringVar] = {}
        fields = [("name", "Full name *"), ("email", "Email address"),
                  ("phone", "Phone number"), ("course", "Course *"), ("year", "Year / class *")]
        for key, label in fields:
            tk.Label(body, text=label, bg="white", fg="#465168",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 4))
            value = str(student[key]) if student else ""
            var = tk.StringVar(value=value)
            self.vars[key] = var
            entry = ttk.Entry(body, textvariable=var, width=38)
            entry.pack(fill="x", ipady=5)
        buttons = tk.Frame(body, bg="white")
        buttons.pack(fill="x", pady=(20, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save student", command=self.submit).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda _event: self.submit())
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.vars["name"]

    def submit(self) -> None:
        values = tuple(self.vars[key].get().strip() for key in ("name", "email", "phone", "course", "year"))
        if not values[0] or not values[3] or not values[4]:
            messagebox.showwarning("Missing details", "Please enter a name, course, and year.", parent=self)
            return
        self.parent.db.save(values, self.student["id"] if self.student else None)
        self.parent.refresh()
        self.destroy()


class StudentApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.db = StudentDatabase()
        self.title("Student management · CampusDesk")
        self.geometry("1120x720")
        self.minsize(860, 580)
        self.configure(bg=BG)
        self._style()
        self._build()
        self.refresh()

    def _style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground=INK,
                        rowheight=42, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#f8f9fc", foreground=MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=(10, 12))
        style.map("Treeview", background=[("selected", "#e8ebff")], foreground=[("selected", INK)])
        style.configure("TEntry", padding=9, font=("Segoe UI", 10))
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.configure("Danger.TButton", padding=(12, 8), font=("Segoe UI", 9, "bold"),
                        foreground="#b42318", background="#fff1f0")
        style.map("Danger.TButton", background=[("active", "#ffe0dc")])

    def _build(self) -> None:
        header = tk.Frame(self, bg="white", padx=30, pady=17)
        header.pack(fill="x")
        tk.Label(header, text="◈", bg="white", fg=ACCENT, font=("Segoe UI", 23, "bold")).pack(side="left")
        brand = tk.Frame(header, bg="white")
        brand.pack(side="left", padx=(10, 0))
        tk.Label(brand, text="CampusDesk", bg="white", fg=INK,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(brand, text="STUDENT MANAGEMENT", bg="white", fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.count_label = tk.Label(header, text="", bg="white", fg=MUTED, font=("Segoe UI", 9))
        self.count_label.pack(side="right")

        main = tk.Frame(self, bg=BG, padx=30, pady=26)
        main.pack(fill="both", expand=True)
        tk.Label(main, text="Students", bg=BG, fg=INK,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(main, text="Keep student records organized in one place.", bg=BG, fg=MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 18))

        cards = tk.Frame(main, bg=BG)
        cards.pack(fill="x", pady=(0, 18))
        self.total_value = self._card(cards, "TOTAL STUDENTS", "0")
        self.course_value = self._card(cards, "COURSES REPRESENTED", "0")
        self.visible_value = self._card(cards, "SHOWING", "0")

        toolbar = tk.Frame(main, bg=BG)
        toolbar.pack(fill="x", pady=(0, 12))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        search = ttk.Entry(toolbar, textvariable=self.search_var, width=34)
        search.pack(side="left", ipady=4)
        search.insert(0, "")
        tk.Label(toolbar, text="Search by name, email, course or year", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=10)
        ttk.Button(toolbar, text="＋  Add student", command=self.add_student).pack(side="right")
        ttk.Button(toolbar, text="Delete selected", style="Danger.TButton",
                   command=self.delete_student).pack(side="right", padx=(0, 8))
        ttk.Button(toolbar, text="Edit selected", command=self.edit_student).pack(side="right", padx=(0, 8))

        panel = tk.Frame(main, bg="white", highlightbackground="#e6e9f1", highlightthickness=1)
        panel.pack(fill="both", expand=True)
        columns = ("name", "email", "phone", "course", "year")
        self.table = ttk.Treeview(panel, columns=columns, show="headings", selectmode="browse")
        for key, title, width in [("name", "STUDENT", 205), ("email", "EMAIL", 235),
                                  ("phone", "PHONE", 145), ("course", "COURSE", 190),
                                  ("year", "YEAR / CLASS", 125)]:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=90, anchor="w")
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=7)
        scrollbar.pack(side="right", fill="y", padx=(0, 7), pady=7)
        self.table.bind("<Double-1>", lambda _event: self.edit_student())
        self.table.bind("<Delete>", lambda _event: self.delete_student())

        footer = tk.Frame(main, bg=BG)
        footer.pack(fill="x", pady=(10, 0))
        tk.Label(footer, text="Tip: double-click a student row to edit it.", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Button(footer, text="Delete", command=self.delete_student).pack(side="right")
        ttk.Button(footer, text="Edit selected", command=self.edit_student).pack(side="right", padx=8)

    @staticmethod
    def _card(parent: tk.Widget, title: str, value: str) -> tk.Label:
        card = tk.Frame(parent, bg="white", padx=17, pady=14,
                        highlightbackground="#e6e9f1", highlightthickness=1)
        card.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(card, text=title, bg="white", fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        label = tk.Label(card, text=value, bg="white", fg=INK,
                         font=("Segoe UI", 20, "bold"))
        label.pack(anchor="w", pady=(5, 0))
        return label

    def refresh(self) -> None:
        rows = self.db.all(self.search_var.get() if hasattr(self, "search_var") else "")
        for item in self.table.get_children():
            self.table.delete(item)
        for row in rows:
            self.table.insert("", "end", iid=str(row["id"]),
                              values=(row["name"], row["email"] or "—", row["phone"] or "—",
                                      row["course"], row["year"]))
        total, courses = self.db.stats()
        self.total_value.config(text=str(total))
        self.course_value.config(text=str(courses))
        self.visible_value.config(text=str(len(rows)))
        self.count_label.config(text=f"{total} student{'s' if total != 1 else ''} in your records")

    def selected_id(self) -> int | None:
        selection = self.table.selection()
        return int(selection[0]) if selection else None

    def add_student(self) -> None:
        StudentForm(self)

    def edit_student(self) -> None:
        student_id = self.selected_id()
        if student_id is None:
            messagebox.showinfo("Select a student", "Choose a student row to edit.", parent=self)
            return
        student = self.db.connection.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        if student:
            StudentForm(self, student)

    def delete_student(self) -> None:
        student_id = self.selected_id()
        if student_id is None:
            messagebox.showinfo("Select a student", "Choose a student row to delete.", parent=self)
            return
        row = self.db.connection.execute("SELECT name FROM students WHERE id=?", (student_id,)).fetchone()
        if row and messagebox.askyesno("Delete student", f"Delete {row['name']} from the records?", parent=self):
            self.db.delete(student_id)
            self.refresh()


if __name__ == "__main__":
    StudentApp().mainloop()
