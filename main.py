# 🚀 FULL SAAS - MODERN UI VERSION

from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'

# Extensions

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ================= MODELS =================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    type = db.Column(db.String(10))
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= UI TEMPLATE =================
def layout(content):
    return f"""
    <html>
    <head>
    <title>Budget SaaS</title>
    <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    <style>
    body {{background:#f4f6f9;}}
    .sidebar {{height:100vh;background:#111;color:white;padding:20px;}}
    .card {{border-radius:15px;}}
    </style>
    </head>
    <body>
    <div class='container-fluid'>
        <div class='row'>
            <div class='col-2 sidebar'>
                <h4>💰 Budget</h4>
                <a href='/dashboard' class='text-white d-block mt-3'>Dashboard</a>
                <a href='/logout' class='text-white d-block mt-2'>Çıkış</a>
            </div>
            <div class='col-10 p-4'>
                {content}
            </div>
        </div>
    </div>
    </body>
    </html>
    """

# ================= ROUTES =================
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/dashboard')

    return layout("""
    <div class='col-md-4 offset-md-4 mt-5'>
    <div class='card p-4 shadow'>
    <h3>Giriş</h3>
    <form method='post'>
    <input class='form-control mb-2' name='username' placeholder='Kullanıcı'>
    <input class='form-control mb-2' name='password' type='password' placeholder='Şifre'>
    <button class='btn btn-primary w-100'>Giriş</button>
    </form>
    <a href='/register'>Kayıt Ol</a>
    </div>
    </div>
    """)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        hashed = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=request.form['username'], password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect('/')

    return layout("""
    <div class='col-md-4 offset-md-4 mt-5'>
    <div class='card p-4 shadow'>
    <h3>Kayıt</h3>
    <form method='post'>
    <input class='form-control mb-2' name='username'>
    <input class='form-control mb-2' name='password' type='password'>
    <button class='btn btn-success w-100'>Kayıt</button>
    </form>
    </div>
    </div>
    """)

@app.route('/dashboard')
@login_required
def dashboard():
    data = Transaction.query.filter_by(user_id=current_user.id).all()

    income = sum(t.amount for t in data if t.type=='income')
    expense = sum(t.amount for t in data if t.type=='expense')
    balance = income - expense

    html = f"""
    <h2>Dashboard</h2>

    <div class='row'>
        <div class='col-md-4'><div class='card p-3 shadow'><h6>Bakiye</h6><h3>{balance}</h3></div></div>
        <div class='col-md-4'><div class='card p-3 shadow'><h6>Gelir</h6><h3>{income}</h3></div></div>
        <div class='col-md-4'><div class='card p-3 shadow'><h6>Gider</h6><h3>{expense}</h3></div></div>
    </div>

    <div class='row mt-4'>
        <div class='col-md-6'>
            <canvas id='chart'></canvas>
        </div>

        <div class='col-md-6'>
            <form method='post' action='/add/income'>
            <input class='form-control mb-2' name='amount' placeholder='Gelir'>
            <input class='form-control mb-2' name='category' placeholder='Kategori'>
            <button class='btn btn-success w-100'>Gelir Ekle</button>
            </form>

            <form method='post' action='/add/expense' class='mt-3'>
            <input class='form-control mb-2' name='amount' placeholder='Gider'>
            <input class='form-control mb-2' name='category' placeholder='Kategori'>
            <button class='btn btn-danger w-100'>Gider Ekle</button>
            </form>
        </div>
    </div>

    <table class='table mt-4'>
    <tr><th>Tip</th><th>Tutar</th><th>İşlem</th></tr>
    {''.join([f"<tr><td>{t.type}</td><td>{t.amount}</td><td><a href='/delete/{t.id}' class='btn btn-sm btn-danger'>Sil</a></td></tr>" for t in data])}
    </table>

    <script>
    new Chart(document.getElementById('chart'), {{
        type:'doughnut',
        data:{{labels:['Gelir','Gider'],datasets:[{{data:[{income},{expense}]}}]}}
    }});
    </script>
    """

    return layout(html)

@app.route('/add/<type>', methods=['POST'])
@login_required
def add(type):
    t = Transaction(user_id=current_user.id,
                    type=type,
                    amount=float(request.form['amount']),
                    category=request.form['category'])
    db.session.add(t)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    t = Transaction.query.get(id)
    if t.user_id == current_user.id:
        db.session.delete(t)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)