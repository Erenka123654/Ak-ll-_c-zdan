from flask import Flask, render_template_string, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"
DB = "budget.db"

# DB init

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# ================= UI =================
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bütçe App</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { background:#f5f7fb; }
.card { border-radius:15px; }
</style>
</head>
<body>
<div class="container mt-4">
    {{ content|safe }}
</div>
</body>
</html>
"""

LOGIN = """
<div class="row justify-content-center">
<div class="col-md-4">
<div class="card p-4 shadow">
<h3 class="mb-3">Giriş Yap</h3>
<form method='post'>
<input class='form-control mb-2' name='username' placeholder='Kullanıcı adı'>
<input class='form-control mb-2' name='password' type='password' placeholder='Şifre'>
<button class='btn btn-primary w-100'>Giriş</button>
</form>
<a href='/register'>Kayıt Ol</a>
</div>
</div>
</div>
"""

REGISTER = """
<div class="row justify-content-center">
<div class="col-md-4">
<div class="card p-4 shadow">
<h3>Kayıt Ol</h3>
<form method='post'>
<input class='form-control mb-2' name='username'>
<input class='form-control mb-2' name='password' type='password'>
<button class='btn btn-success w-100'>Kayıt</button>
</form>
</div>
</div>
</div>
"""

DASHBOARD = """
<h2 class='mb-4'>📊 Dashboard</h2>
<a href='/logout' class='btn btn-danger mb-3'>Çıkış</a>

<div class='row g-3'>
  <div class='col-md-4'>
    <div class='card p-3 shadow text-center'>
      <h6>Bakiye</h6>
      <h3>{{ balance }} TL</h3>
    </div>
  </div>
  <div class='col-md-4'>
    <div class='card p-3 shadow text-center'>
      <h6>Gelir</h6>
      <h3>{{ income }} TL</h3>
    </div>
  </div>
  <div class='col-md-4'>
    <div class='card p-3 shadow text-center'>
      <h6>Gider</h6>
      <h3>{{ expense }} TL</h3>
    </div>
  </div>
</div>

<div class='row mt-4'>
  <div class='col-md-6'>
    <div class='card p-3 shadow'>
      <h6>Gelir vs Gider</h6>
      <canvas id='pieChart'></canvas>
    </div>
  </div>

  <div class='col-md-6'>
    <div class='card p-3 shadow'>
      <h6>Kategori Bazlı Gider</h6>
      <canvas id='barChart'></canvas>
    </div>
  </div>
</div>

<div class='card mt-4 p-3 shadow'>
<h6>Son İşlemler</h6>
<table class='table'>
<thead><tr><th>Tip</th><th>Tutar</th><th>Kategori</th><th>Tarih</th></tr></thead>
<tbody>
{% for t in transactions %}
<tr>
<td>{{ t[2] }}</td>
<td>{{ t[3] }} TL</td>
<td>{{ t[4] }}</td>
<td>{{ t[5] }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>

<script>
new Chart(document.getElementById('pieChart'), {
    type: 'doughnut',
    data: {
        labels: ['Gelir','Gider'],
        datasets: [{ data: [{{ income }}, {{ expense }}] }]
    }
});

new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: {
        labels: {{ categories|safe }},
        datasets: [{ data: {{ amounts|safe }} }]
    }
});
</script>
"""

# ================= ROUTES =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        user = c.execute("SELECT * FROM users WHERE username=? AND password=?",
                         (request.form['username'], request.form['password'])).fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')

    return render_template_string(BASE_HTML, content=LOGIN)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (request.form['username'], request.form['password']))
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template_string(BASE_HTML, content=REGISTER)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    data = c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC",
                     (session['user_id'],)).fetchall()

    income = sum(t[3] for t in data if t[2]=='income')
    expense = sum(t[3] for t in data if t[2]=='expense')
    balance = income - expense

    # kategori analizi
    cat = {}
    for t in data:
        if t[2]=='expense':
            cat[t[4]] = cat.get(t[4],0) + t[3]

    categories = list(cat.keys())
    amounts = list(cat.values())

    return render_template_string(BASE_HTML,
        content=render_template_string(DASHBOARD,
            balance=balance,
            income=income,
            expense=expense,
            transactions=data[:10],
            categories=categories,
            amounts=amounts))

@app.route('/add/<type>', methods=['POST'])
def add(type):
    if 'user_id' not in session:
        return redirect('/')

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, type, amount, category, date) "
              "VALUES (?, ?, ?, ?, ?)",
              (session['user_id'], type,
               float(request.form['amount']),
               request.form['category'],
               str(datetime.now())))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)