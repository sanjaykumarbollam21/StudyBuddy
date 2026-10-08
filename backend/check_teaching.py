import sqlite3

con = sqlite3.connect("study_buddy.db")
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]
print("Tables in study_buddy.db:", tables)

for t in ["users", "documents", "document_chunks", "learning_progress", "student_mastery"]:
    if t in tables:
        cursor.execute(f"SELECT count(*) FROM {t};")
        print(f"Row count {t}: {cursor.fetchone()[0]}")
