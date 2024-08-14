import bcrypt
from flask import Flask,render_template, url_for, redirect, request, session, jsonify, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from requests import Session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import timedelta, datetime
import os
from sqlalchemy.types import Date
from sqlalchemy.dialects.postgresql import JSON
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.google import make_google_blueprint, google
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import secrets
import string
import utils
from flask_bcrypt import Bcrypt
import chiavi

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "ASSI2024"


app.permanent_session_lifetime = timedelta(minutes=40)

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.init_app(app)

google_blueprint = make_google_blueprint(
    client_id=chiavi.google_client_id,
    client_secret=chiavi.google_client_secret,
    scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_to="google_login"
)

# configuro il blueprint di GitHub
github_blueprint = make_github_blueprint(
    client_id=chiavi.github_client_id,
    client_secret=chiavi.github_client_secret,
    scope="user:email",
    redirect_to="github_login"
)

#importo blueprint di google e metto il listener in login.js
app.register_blueprint(github_blueprint, url_prefix="/github_login")
app.register_blueprint(google_blueprint, url_prefix="/google_login")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" 

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

        password_ok = utils.is_valid_password(password)
        user = Users.query.filter_by(username=username).first()

        if user:
            return render_template("registrazione.html", user_alive=True)

        if password == password_verify and password_ok:

            hashed_password = bcrypt.generate_password_hash(password)

            user = Users(username=username, password=hashed_password, email=email, data_di_nascita=data_di_nascita, diete=diete, intolleranze=intolleranze)
            db.session.add(user)
            db.session.commit()

            session.permanent = True
            session['username'] = username
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
        
        #cerca per username o email
        user = Users.query.filter((Users.username == username_or_email) | (Users.email == username_or_email)).first()

        if user and bcrypt.check_password_hash(user.password, password_verify):
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

#callback login con google
@app.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    token = google.token['access_token']
    credentials = Credentials(token=token)
    service = build('people', 'v1', credentials=credentials)

    try:
        profile = service.people().get(resourceName='people/me', personFields='names,emailAddresses').execute()
    except Exception as e:
        print(f'An error occurred: {e}')
        return redirect(url_for("login"))

    email = None
    username = None

    if 'emailAddresses' in profile:
        email = profile['emailAddresses'][0]['value']
        print("ENAIL-   ")
    if 'names' in profile:
        print("USERMANE- ")
        username = profile['names'][0]['displayName']

    if email is None:
        return redirect(url_for("login"))

    user = Users.query.filter_by(email=email).first()

    if user is None:
        #password casuale come per github
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(12))

        hashed_password = bcrypt.generate_password_hash(password)

        user = Users(username=username, password=hashed_password, email=email, 
                     data_di_nascita=None, diete=[], intolleranze=[])
        db.session.add(user)
        db.session.commit()

    session.permanent = True
    session['username'] = user.username
    session['password'] = user.password 
    session['id'] = user.id

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

        hashed_password = bcrypt.generate_password_hash(password)


        user = Users(username=username, password=hashed_password, email=email, 
                     data_di_nascita=None, diete=None, intolleranze=None)
        db.session.add(user)
        db.session.commit()

    session.permanent = True
    session['username'] = user.username
    session['password'] = user.password
    session['id'] = user.id

    return redirect(url_for("main_route"))


@app.route("/delete_account", methods=["POST"])
def delete_account():
    if 'id' in session:
        user_id = session['id']
        user = Users.query.get(user_id)
        
        if user:
            db.session.delete(user)
            db.session.commit()
            
            session.clear()
            logout_user()
            
            return redirect(url_for("logout"))
        
        return redirect(url_for("account"))
    
    return redirect(url_for("login"))


@app.route('/<something>')
def goto(something):
    return redirect(url_for('main_route'))

@app.route("/account")
def account():
    if 'id' in session:
        user_id = session['id']
        user = Users.query.get(user_id)
        
        if user:
            return render_template("account.html", username=user.username, email=user.email, data_nascita=user.data_di_nascita.strftime('%Y-%m-%d') if user.data_di_nascita else "N/A", diete=user.diete, intolleranze=user.intolleranze)
    
    return redirect(url_for("login"))

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'id' in session:
        user_id = session['id']
        user = Users.query.get(user_id)

        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if not bcrypt.check_password_hash(user.password, old_password):
            flash('Old password is incorrect', 'error')
            return redirect(url_for('account'))

        if new_password != confirm_new_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('account'))

        if not utils.is_valid_password(new_password):
            flash('New password is too simple', 'error')
            return redirect(url_for('account'))

        hashed_new_password = bcrypt.generate_password_hash(new_password)
        user.password = hashed_new_password
        db.session.commit()

        flash('Password updated successfully', 'success')
        return redirect(url_for('account'))

    flash('You need to log in to update your password', 'error')
    return redirect(url_for('login'))

@app.route('/update_birthdate', methods=['POST'])
def update_birthdate():
    if 'id' in session:
        user_id = session['id']
        user = Users.query.get(user_id)

        new_birthdate_str = request.form.get('birthdate')

        try:
            new_birthdate = datetime.strptime(new_birthdate_str, '%Y-%m-%d').date()
            user.data_di_nascita = new_birthdate
            db.session.commit()
            flash('Data di nascita aggiornata con successo', 'success')
        except ValueError:
            flash('Formato data non valido', 'error')

        return redirect(url_for('account'))

    flash('Devi effettuare il login per aggiornare la data di nascita', 'error')
    return redirect(url_for('login'))

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if 'id' in session:
        user_id = session['id']
        user = Users.query.get(user_id)

        selected_diets = request.form.getlist('diet')
        user.diete = selected_diets

        selected_allergies = request.form.getlist('allergies')
        user.intolleranze = selected_allergies

        db.session.commit()
        return redirect(url_for('account'))

    return redirect(url_for('login'))

@app.route("/ricetta")
def ricetta():
    return render_template("ricetta.html")

@app.route("/idee_rand")
def idee_rand():
    return render_template("idee_rand.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'fav.ico',mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)
