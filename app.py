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
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import secrets
import string
from utils import generate_reset_token, verify_reset_token, send_reset_email, is_valid_password, generate_password
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
import chiavi
from flask import jsonify

from flask import current_app


#CONFIGURAZIONE APP FLASK, DB E MAIL
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = chiavi.config_secret_key

# configuro flask mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = chiavi.email_gmail
app.config['MAIL_PASSWORD'] = chiavi.password_gmail

app.config['CURRENT_SALT'] = os.urandom(16).hex()
print(app.config['CURRENT_SALT'])
app.config['PREVIOUS_SALT'] = None 
app.config['SALT_LAST_ROTATION'] = datetime.now()

mail = Mail(app)
# configuro itsdangerous
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.permanent_session_lifetime = timedelta(minutes=20) #dopo 20 minuti fa automaticamente logout

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.init_app(app)


facebook_blueprint = make_facebook_blueprint(
    client_id='your_facebook_client_id',
    client_secret='your_facebook_client_secret',
    scope=['email', 'public_profile'],  
    redirect_to="facebook_login"
)

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
app.register_blueprint(facebook_blueprint, url_prefix="/facebook_login")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" 



# def generate_reset_token(email):
#     return s.dumps(email, salt='password-reset-salt')

# def verify_reset_token(token, expiration=3600):
#     try:
#         email = s.loads(token, salt='password-reset-salt', max_age=expiration)
#     except (SignatureExpired, BadSignature):
#         return None
#     return email

# def send_reset_email(to_email, token):
#     with app.app_context():
#         msg = Message(
#             'Reset Your Password',
#             sender=chiavi.email_gmail,
#             recipients=[to_email]
#         )
#         msg.body = f'''Per resettare la tua password, usa il seguente token:
# {token}

# Se non hai richiesto il reset della password, ignora questa email.
# '''
#         mail.send(msg)


@app.route('/recupero_password_request', methods=['POST'])
def recupero_password_request():
    email = request.form.get('email_input')

    user = Users.query.filter_by(email=email).first()
    if user:
        try:
            token = generate_reset_token(email)
            send_reset_email(email, token)

            return redirect(url_for('recupera_psw', token_sended=True))
        except Exception as e:
            print(f"Errore durante il reset della password: {str(e)}")
            return jsonify({'success': False, 'message': 'Errore durante l\'invio dell\'email.'}), 500
    else:
        redirect(url_for('recupera_psw'))
        return jsonify({'success': False, 'message': 'Utente non trovato.'}), 404



@app.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        if user:
            try:
                token = generate_reset_token(user.email)
                send_reset_email(user.email, token)

                return jsonify({'success': True, 'message': 'Un token (con validità di 10 minuti) per il reset della password è stato inviato al tuo indirizzo email.'})
            except Exception as e:
                print(f"Errore durante il reset della password: {str(e)}")
                return jsonify({'success': False, 'message': 'Errore durante l\'invio dell\'email.'}), 500
        else:
            return jsonify({'success': False, 'message': 'Utente non trovato.'}), 404
    else:
        return jsonify({'success': False, 'message': 'Non sei autenticato.'}), 403


@app.route('/reset_password', methods=['POST'])
def reset_password():
    token = request.form.get('token')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    email = verify_reset_token(token)
    if email is None:
        flash('Token non valido o scaduto.', 'error')
        return redirect(url_for('login'))
    print(f"LEZGOZGHI")

    user = Users.query.filter_by(email=email).first()
    if user:
        if new_password == confirm_new_password:
            if is_valid_password(new_password):
                hashed_password = bcrypt.generate_password_hash(new_password)
                user.password = hashed_password
                db.session.commit()
                print(f"DAJEE")
                flash('La tua password è stata aggiornata con successo.', 'success')
                return redirect(url_for('account'))
            else:
                print(f"NON VALIDE")
                flash('Le password non coincidono o non sono valide.', 'error')
        else:
            print(f"NON COINCIDONO")
            flash('Le password non coincidono o non sono valide.', 'error')
    else:
        flash('Errore utente.', 'error')

    return redirect(url_for('login'))




class Comments(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(30), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, recipe_id, email, username, comment, rating):
        self.recipe_id = recipe_id
        self.email = email
        self.username = username
        self.comment = comment
        self.rating = rating



class Favourite(db.Model):
    __tablename__ = 'favourite'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False)
    note = db.Column(db.String(300), nullable=False, default="")

    def __init__(self, recipe_id=None, email=None):
        self.recipe_id = recipe_id
        self.email = email
        self.note=""


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(30), nullable = False, unique = True)    
    password = db.Column(db.String(250), nullable = False) 
    data_di_nascita = db.Column(Date, nullable=True) #non so se Date è valido
    diete = db.Column(JSON, nullable=True) #non so se JSON è valido
    intolleranze = db.Column(JSON, nullable=True)  
    lista_spesa = db.Column(JSON, nullable=True)

    def __init__(self, username=None, password=None, email=None, data_di_nascita=None, diete=None, intolleranze=None, lista_spesa=None):
        self.username = username
        self.password = password
        self.email = email
        self.data_di_nascita = data_di_nascita
        self.diete = diete if diete is not None else []
        self.intolleranze = intolleranze if intolleranze is not None else []
        self.lista_spesa = lista_spesa if lista_spesa is not None else []



    def __repr__(self):
        return (f'<User {self.username}, email {self.email}, data_di_nascita {self.data_di_nascita}, diete {self.diete}, intolleranze {self.intolleranze}>')

    
db.init_app(app)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def loader_user(user_id):
    return db.session.get(Users, user_id)
# def loader_user(user_id):
#     # return Session.get(user_id) 
#     Users.query.get(user_id)


#HOMEPAGE
@app.route("/")
def main_route():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        diet = user.diete
        intolerances = user.intolleranze
    else:
        diet = []
        intolerances = []
    return render_template("index.html", diet=diet, intolerances=intolerances)

#SIGNUP E LOGIN
@app.route('/registrazione', methods=["GET", "POST"])
def registrazione():
    if request.method == "POST":
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get("password")
        password_verify = request.form.get("password_conf")
        data_di_nascita_str = request.form.get('birthdate')
        
        diete = request.form.getlist('diet')
        intolleranze = request.form.getlist('allergies')

        # Si potrebbe evitare sta cose soprattutto se la data non viene usata
        if data_di_nascita_str:
            try:
                data_di_nascita = datetime.strptime(data_di_nascita_str, '%Y-%m-%d').date()
                #qua criptare data di nascita
            except ValueError:
                data_di_nascita = None
        else:
            data_di_nascita = None

        password_ok = is_valid_password(password)
        user = Users.query.filter_by(username=username).first()

        if user:
            flash('Utente già registrato.', 'error')
            return render_template("registrazione.html")
        if  not password_ok:
            flash('Password troppo semplice', 'error')
            return render_template("registrazione.html")
        if password == password_verify:

            hashed_password = bcrypt.generate_password_hash(password)

            user = Users(username=username, password=hashed_password, email=email, data_di_nascita=data_di_nascita, diete=diete, intolleranze=intolleranze)
            db.session.add(user)
            db.session.commit()

            session.permanent = True
            session['username'] = username
            session['id'] = user.id

            return redirect(url_for("main_route"))
        else:
            flash('Le due password non combaciano', 'error')
            return render_template("registrazione.html")
    
    elif 'username' in session and 'password' in session:
        return redirect(url_for("main_route"))
    else:
        return render_template("registrazione.html")

@app.route('/generate_password', methods=['GET'])
def generate_password_route():
    password = generate_password()
    return jsonify({'password': password})


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
            flash('Utente non registrato', 'error')
            return render_template("login.html")
        
        else:
            flash('Password errata', 'error')
            return render_template("login.html")
        
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
    if 'names' in profile:
        username = profile['names'][0]['displayName']

    if email is None:
        return redirect(url_for("login"))

    user = Users.query.filter_by(email=email).first()

    if user is None:
        #password casuale come per github
        # alphabet = string.ascii_letters + string.digits
        # password = ''.join(secrets.choice(alphabet) for i in range(12))

        password = generate_password()
        # print(password)

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
        # alphabet = string.ascii_letters + string.digits
        # password = ''.join(secrets.choice(alphabet) for i in range(12))

        password = generate_password()

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

@app.route("/facebook_login")
def facebook_login():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))

    resp = facebook.get("/me?fields=id,email,name")
    assert resp.ok, resp.text
    info = resp.json()

    username = info.get("name")  
    email = info.get("email")    

    if email is None:
        return redirect(url_for("login"))  
    
    print("User:", username, "con email:", email)
    
    user = Users.query.filter_by(email=email).first()
    
    if user is None:
        # alphabet = string.ascii_letters + string.digits
        # password = ''.join(secrets.choice(alphabet) for i in range(12))

        password = generate_password()

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



#IMPOSTAZIONI E MODIFICA ACCOUNT

@app.route("/account")
def account():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        
        if user:
            return render_template("account.html", username=user.username, email=user.email, data_nascita=user.data_di_nascita.strftime('%Y-%m-%d') if user.data_di_nascita else "N/A", diete=user.diete, intolleranze=user.intolleranze)
    
    return redirect(url_for("login"))

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        
        if user:
            db.session.delete(user)
            db.session.commit()
            
            session.clear()
            logout_user()
            
            return redirect(url_for("logout"))
        
        return redirect(url_for("account"))
    
    return redirect(url_for("login"))

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)

        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if not bcrypt.check_password_hash(user.password, old_password):
            flash('Old password is incorrect', 'error')
            return redirect(url_for('account'))

        if new_password != confirm_new_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('account'))

        if not is_valid_password(new_password):
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
        user = db.session.get(Users, user_id)

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
        user = db.session.get(Users, user_id)

        selected_diets = request.form.getlist('diet')
        user.diete = selected_diets

        selected_allergies = request.form.getlist('allergies')
        user.intolleranze = selected_allergies

        db.session.commit()
        return redirect(url_for('account'))

    return redirect(url_for('login'))

@app.route("/recupera_psw")
def recupera_psw():
    return render_template("recupera_psw.html")

#PAGINA RICETTA

@app.route("/ricetta")
def ricetta():
    if 'id' in session:
        return render_template("ricetta.html")
    return redirect(url_for('login'))


#GESTIONE RICETTE PREFERITE

@app.route('/add_to_favourites', methods=['POST'])
def add_to_favourites():
    if 'id' in session:

        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        recipe_id = request.json.get('recipe_id')

        if not recipe_id:
            return jsonify({'error': 'Missing recipe_id'}), 400
        
        existing_favourite = Favourite.query.filter_by(recipe_id=recipe_id, email=user_email).first()
        if existing_favourite:
            return jsonify({'error': 'Recipe is already in favourites'}), 409

        favourite = Favourite(recipe_id=recipe_id, email=user_email)
        db.session.add(favourite)
        db.session.commit()

        return jsonify({'success': 'Recipe added to favourites'}), 200
    return redirect(url_for('login'))

@app.route('/remove_from_favourites', methods=['POST'])
def remove_from_favourites():
    if 'id' in session:
        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        recipe_id = request.json.get('recipe_id')

        if not recipe_id:
            return jsonify({'error': 'Missing recipe_id'}), 400

        existing_favourite = Favourite.query.filter_by(recipe_id=recipe_id, email=user_email).first()
        if existing_favourite:
            db.session.delete(existing_favourite)
            db.session.commit()
            return jsonify({'success': 'Recipe removed from favourites'}), 200
        else:
            return jsonify({'error': 'Recipe not found in favourites'}), 404

    return redirect(url_for('login'))


@app.route('/check_favourite', methods=['GET'])
def check_favourite():
    if 'id' in session:
        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        recipe_id = request.args.get('recipe_id')

        if not recipe_id:
            return jsonify({'error': 'Missing recipe_id'}), 400

        favourite = Favourite.query.filter_by(recipe_id=recipe_id, email=user_email).first()

        return jsonify({'is_favourite': favourite is not None})

    return jsonify({'is_favourite': False})


@app.route("/fav")
def fav():
    if 'id' in session:
        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        favourites = Favourite.query.filter_by(email=user_email).all()
        recipe_ids = [fav.recipe_id for fav in favourites]
        return render_template("fav.html", lista=recipe_ids)
    return redirect(url_for('login'))

@app.route('/update_note', methods=['POST'])
def update_note():
    if 'id' in session:
        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        recipe_id = request.form.get('recipe_id')
        note = request.form.get('note')
        
        favourite = Favourite.query.filter_by(email=user_email, recipe_id=recipe_id).first()
        if favourite:
            favourite.note = note
            db.session.commit()
            return jsonify({"message": "Note updated successfully!"}), 200
        return jsonify({"message": "Favourite not found!"}), 404
    return redirect(url_for('login'))


@app.route('/get_note', methods=['POST'])
def get_note():
    if 'id' in session:
        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        recipe_id = request.json.get('recipe_id')

        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400

        favourite = Favourite.query.filter_by(email=user_email, recipe_id=recipe_id).first()
        note = favourite.note if favourite and favourite.note else ""
        return jsonify({"recipe_id": recipe_id, "note": note}), 200
    return redirect(url_for('login'))


#GESTIONE LISTA DELLA SPESA

@app.route("/lista_spesa")
def lista_spesa():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)

        user.lista_spesa
        return render_template("lista_spesa.html", lista=user.lista_spesa)
    return redirect(url_for('login'))


@app.route('/update_shopping_list', methods=['POST'])
def update_shopping_list():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)

        ingredient = request.form.get('ingredient')

        if ingredient:
            updated_lista_spesa = user.lista_spesa.copy() if user.lista_spesa else []
            if ingredient not in updated_lista_spesa:
                updated_lista_spesa.append(ingredient)
                user.lista_spesa = updated_lista_spesa
                db.session.commit()

            return jsonify({'message': f'{ingredient} aggiunto alla lista della spesa!'}), 200

    return redirect(url_for('login'))


@app.route('/get_shopping_list', methods=['GET'])
def get_shopping_list():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        if user:
            return jsonify({'lista_spesa': user.lista_spesa}), 200
    return redirect(url_for('login'))

@app.route('/remove_from_shopping_list', methods=['POST'])
def remove_from_shopping_list():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)

        data = request.get_json()
        ingredient = data.get('ingredient')

        if ingredient and ingredient in user.lista_spesa:
            updated_lista_spesa = user.lista_spesa.copy()
            updated_lista_spesa.remove(ingredient)
            user.lista_spesa = updated_lista_spesa
            db.session.commit()

            return jsonify({'message': 'success'}), 200

    return jsonify({'message': 'error'}), 400

@app.route('/check_lista', methods=['GET'])
def check_lista():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        ingredient = request.args.get('ingredient')

        if not ingredient:
            return jsonify({'error': 'Missing ingredient'}), 400
        is_in_list = ingredient in user.lista_spesa if user.lista_spesa else False
        return jsonify({'in_in_list': is_in_list}), 200

    return jsonify({'in_in_list': False})


#IDEE RANDOM

@app.route("/idee_rand")
def idee_rand():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        diet = user.diete
        intolerances = user.intolleranze
    else:
        diet = []
        intolerances = []
    return render_template("idee_rand.html", diet=diet, intolerances=intolerances)


#SEZIONE COMMENTI

@app.route('/get-comments/<int:recipe_id>', methods=['GET'])
def get_comments(recipe_id):
    comments = Comments.query.filter_by(recipe_id=recipe_id).all()
    comments_list = [
        {
            'username': c.username,
            'comment': c.comment,
            'rating': c.rating, 
            'timestamp': c.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for c in comments
    ]
    return jsonify(comments_list)

@app.route('/submit-comment', methods=['POST'])
def submit_comment():

    if 'id' in session:
        user_id = session['id']
        user = Users.query.get(user_id)

        recipe_id = request.form.get('recipe_id') 
        comment_text = request.form.get('comment')
        rating = request.form.get('rating')
        
        if not recipe_id or not comment_text:
            return jsonify({'status': 'error', 'message': 'Dati mancanti'}), 400
        
        new_comment = Comments(
            recipe_id=recipe_id,
            email=user.email,
            username=user.username,
            comment=comment_text,
            rating=int(rating)
        )
        
        db.session.add(new_comment)
        db.session.commit()
    
    return redirect(url_for('ricetta', id=recipe_id))


@app.route('/<something>')
def goto(something):
    return redirect(url_for('main_route'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'fav.ico',mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)
