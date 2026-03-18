from flask import Flask, session, redirect
import sqlite3

DB = 'path_to_your_database.db'  # Replace with the actual path to your SQLite database

app = Flask(__name__)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM transactions WHERE id=? AND user_id=?", 
              (id, session['user_id']))

    conn.commit()
    conn.close()

    return redirect('/dashboard')
data = []  # Initialize data with an empty list or fetch it from the database
transactions = data[:10]