# CampusDesk Student Management

A desktop student records app built with Python's standard library. It uses Tkinter for the interface and SQLite for local storage; no package installation is needed.

## Run

```powershell
python main.py
```

The app creates `students.db` in the same folder the first time it runs. Add students with a name, course, and year/class. Email and phone are optional. Search checks the name, email, phone, course, and year fields. Double-click a row or use **Edit selected** to update it; select a row and press **Delete** (or use the button) to remove it.

Python must include Tk support. On Windows, the standard python.org installer includes it.
