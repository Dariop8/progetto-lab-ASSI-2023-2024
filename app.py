from flask import Flask,render_template, url_for, redirect, request, session, jsonify, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from requests import Session
from sqlalchemy import func, desc, or_
from flask_login import LoginManager, UserMixin, login_user, logout_user
from datetime import timedelta, datetime
import os
from sqlalchemy.types import Date
from sqlalchemy.dialects.postgresql import JSON

from flask_dance.contrib.github import make_github_blueprint, github
import secrets
import string

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "ASSI2024"


app.permanent_session_lifetime = timedelta(minutes=40)

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.init_app(app)

# configuro il blueprint di GitHub
github_blueprint = make_github_blueprint(
    client_id="Ov23liBdiIHtl6sEma1M",
    client_secret="95e77207bb3717a810dcbc478caab519a5a8131a",
    scope="user:email",
    redirect_to="github_login"
)
app.register_blueprint(github_blueprint, url_prefix="/github_login")

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(30), nullable = False, unique = True)    
    password = db.Column(db.String(250), nullable = False) 
    data_di_nascita = db.Column(Date, nullable=True) #non so se Date è valido
    diete = db.Column(JSON, nullable=True) #non so se JSON è valido
    intolleranze = db.Column(JSON, nullable=True)  

    def __init__(self, username=None, password=None, email=None, data_di_nascita=None, diete=None, intolleranze=None):
        self.username = username
        self.password = password
        self.email = email
        self.data_di_nascita = data_di_nascita
        self.diete = diete if diete is not None else []
        self.intolleranze = intolleranze if intolleranze is not None else []


    def __repr__(self):
        return (f'<User {self.username}, email {self.email}, data_di_nascita {self.data_di_nascita}, diete {self.diete}, intolleranze {self.intolleranze}>')

    
db.init_app(app)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def loader_user(user_id):
    # return Session.get(user_id) 
    Users.query.get(user_id)


@app.route("/")
def main_route():
    return render_template("index.html")

@app.route('/registrazione', methods=["GET", "POST"])
def registrazione():
    if request.method == "POST":
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get("password")
        password_verify = request.form.get("password_conf")
        data_di_nascita_str = request.form.get('birthdate')
        
        diete = request.form.getlist('diete')  
        intolleranze = request.form.getlist('intolleranze')  

        # Si potrebbe evitare sta cose soprattutto se la data non viene usata
        if data_di_nascita_str:
            try:
                data_di_nascita = datetime.strptime(data_di_nascita_str, '%Y-%m-%d').date()
            except ValueError:
                data_di_nascita = None
        else:
            data_di_nascita = None

        password_ok = True  # Implementare qualcosa con regex per vedere se psw è complessa
        user = Users.query.filter_by(username=username).first()

        if user:
            return render_template("registrazione.html", user_alive=True)

        if password == password_verify and password_ok:
            user = Users(username=username, password=password, email=email, 
                         data_di_nascita=data_di_nascita, diete=diete, intolleranze=intolleranze)
            db.session.add(user)
            db.session.commit()

            session.permanent = True
            
            session['username'] = username
            session['password'] = password
            session['id'] = user.id

            return redirect(url_for("main_route"))
        else:
            return render_template("registrazione.html", password_ok=password_ok, password=password, password_verify=password_verify)
    
    elif 'username' in session and 'password' in session:
        return redirect(url_for("main_route"))
    else:
        return render_template("registrazione.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username_input")
        password_verify = request.form.get("password_input")
        
        # Cerca per username o email
        user = Users.query.filter((Users.username == username_or_email) | (Users.email == username_or_email)).first()

        if user and user.password == password_verify:
            login_user(user)
            session.permanent = True
            session['username'] = user.username
            session['password'] = password_verify
            session['id'] = user.id
            
            return redirect(url_for("main_route"))
        
        elif not user:
            return render_template("login.html", something_failed=True, user_not_found=True)
        
        else:
            return render_template("login.html", something_failed=True, user_not_found=False)
        
    elif 'username' in session and 'password' in session and 'id' in session:
        return redirect(url_for("main_route"))
    
    else:
        return render_template("login.html", something_failed=False)

@app.route("/logout")
def logout():
    logout_user()
    session.clear()

    return redirect(url_for("main_route"))

# route per gestire il callback del login di GitHub
@app.route("/github_login")
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))

    resp = github.get("/user")
    assert resp.ok, resp.text
    info = resp.json()
    
    username = info["login"]
    # se l'email è pubblica viene recuperata in questo modo
    email = info.get("email")

    if email is None:
        # se il metodo precedente è fallito passiamo al secondo
        resp_email = github.get("/user/emails")
        if resp_email.status_code == 404:
            print("problema con l'endpoint per l'email")
            return redirect(url_for("login"))

        assert resp_email.ok, resp_email.text
        emails = resp_email.json()
        for email_info in emails:
            if email_info["primary"] and email_info["verified"]:
                email = email_info["email"]
                break

    if email is None:
        return redirect(url_for("login"))  
    print("User:", username, "con email:", email)
    
    user = Users.query.filter_by(email=email).first()
    
    if user is None:
        # genero una password casuale
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(12))

        user = Users(username=username, password=password, email=email, 
                     data_di_nascita=None, diete=None, intolleranze=None)
        db.session.add(user)
        db.session.commit()

    session.permanent = True
    session['username'] = username
    session['password'] = password
    session['id'] = user.id

    return redirect(url_for("main_route"))

# @app.route('/<something>')
# def goto(something):
#     return redirect(url_for('main_route'))

@app.route("/account")
def account():
    return render_template("account.html")

@app.route("/ricetta")
def ricetta():
    return render_template("ricetta.html")

@app.route("/idee_rand")
def idee_rand():
    return render_template("idee_rand.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico',mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)



