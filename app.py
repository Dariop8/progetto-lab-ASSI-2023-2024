from flask import Flask, render_template, url_for, redirect, request, session, jsonify, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user
from datetime import timedelta, datetime
import os
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import secrets
import string
from utils import generate_reset_token, verify_reset_token, send_reset_email, is_valid_password, generate_password
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import pyotp
import chiavi
from flask import jsonify
from flask import current_app
from cryptography.fernet import Fernet
from models import db, Users, Comments, Favourite, ShoppingIngredient, UtentiBloccati, RichiestaSblocco, configure_bcrypt

#CONFIGURAZIONE APP FLASK, DB E MAIL
app = Flask(__name__)
bcrypt = Bcrypt(app)
configure_bcrypt(bcrypt)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = chiavi.config_secret_key

#configuro flask mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = chiavi.email_gmail
app.config['MAIL_PASSWORD'] = chiavi.password_gmail

app.config['CURRENT_SALT'] = os.urandom(16).hex()
app.config['PREVIOUS_SALT'] = None 
app.config['SALT_LAST_ROTATION'] = datetime.now()

mail = Mail(app)
# configuro itsdangerous
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

app.permanent_session_lifetime = timedelta(minutes=20) #dopo 20 minuti fa automaticamente logout

# configuro fernet
cipher_suite = Fernet(chiavi.key_fernet)

# db = SQLAlchemy()

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

   
db.init_app(app)

with app.app_context():
    db.create_all()


@login_manager.user_loader
def loader_user(user_id):
    return db.session.get(Users, user_id)


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

@app.route('/about_us')
def about_us():
    return render_template("about_us.html")

#SIGNUP E LOGIN
@app.route('/registrazione', methods=["GET", "POST"])
def registrazione():
    if request.method == "POST":
        email = request.form.get('email').strip()
        username = request.form.get('username').strip()
        password = request.form.get("password").strip()
        password_verify = request.form.get("password_conf").strip()
        data_di_nascita_str = request.form.get('birthdate')
        attivazione_2fa = request.form.get('attiva-2fa')
        
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
        m = Users.query.filter_by(email=email).first()

        if user or m:
            flash('User already registered.', 'error')
            return render_template("registrazione.html")
        if  not password_ok:
            flash('Password is too weak.', 'error')
            return render_template("registrazione.html")
        if password == password_verify:

            hashed_password = bcrypt.generate_password_hash(password)

            user = Users(username=username, password=hashed_password, email=email, data_di_nascita=data_di_nascita, diete=diete, intolleranze=intolleranze, attivazione_2fa=attivazione_2fa)
            db.session.add(user)
            db.session.commit()

            session.permanent = True
            session['username'] = username
            session['id'] = user.id

            return redirect(url_for("main_route"))
        else:
            flash('Passwords do not match.', 'error')
            return render_template("registrazione.html")
    
    elif 'username' in session and 'password' in session:
        return redirect(url_for("main_route"))
    else:
        return render_template("registrazione.html")

@app.route('/generate_password', methods=['GET'])
def generate_password_route():
    password = generate_password()
    return jsonify({'password': password})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get("username_input")
        password_verify = request.form.get("password_input")
        
        user = Users.query.filter((Users.username == username_or_email) | (Users.email == username_or_email)).first()

        if user and bcrypt.check_password_hash(user.password, password_verify):
            session['password'] = password_verify
            session['email'] = user.email
            
            bloccato = db.session.get(UtentiBloccati, user.email)
            if bloccato:
                return redirect(url_for('blocked'))
            
            if bcrypt.check_password_hash(user.attivazione_2fa, '1'):
                if user.segreto_otp is None:
                    segreto_otp = pyotp.random_base32()  # Genero segreto e inserisco nel db
                    segreto_criptato = cipher_suite.encrypt(segreto_otp.encode())
                    user.segreto_otp = segreto_criptato.decode()
                    db.session.commit()

                segreto_decifrato = cipher_suite.decrypt(user.segreto_otp.encode()).decode()
                # Genero otp e invio mail - pyotp gestisce finestra di validità otp
                totp = pyotp.TOTP(segreto_decifrato)
                otp = totp.now()
                user.tentativi_login = 0
                db.session.commit()

                msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[session['email']])
                msg.body = f'Your OTP Code is {otp}. It will be valid for 60 seconds.'
                mail.send(msg)
                return redirect(url_for('verify_otp'))
            else:
                login_user(user)
                session.permanent = True
                session['username'] = user.username
                session['id'] = user.id
                session['email'] = user.email
                return redirect(url_for("main_route"))
                
        elif not user:
            flash('Utente non registrato', 'errore')
            return render_template("login.html")
        else:
            flash('Password errata', 'errore')
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
        # print(f'An error occurred: {e}')
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
    
    bloccato = db.session.get(UtentiBloccati, user.email)
    session['email'] = user.email
    if bloccato:
        return redirect(url_for('blocked'))

    if bcrypt.check_password_hash(user.attivazione_2fa, '1'):
        if user.segreto_otp is None:
            segreto_otp = pyotp.random_base32()  # Genero segreto e inserisco nel db
            segreto_criptato = cipher_suite.encrypt(segreto_otp.encode())
            user.segreto_otp = segreto_criptato.decode()
            db.session.commit()

        segreto_decifrato = cipher_suite.decrypt(user.segreto_otp.encode()).decode()
        # Genero otp e invio mail - pyotp gestisce finestra di validità otp
        totp = pyotp.TOTP(segreto_decifrato)
        otp = totp.now()
        user.tentativi_login = 0
        db.session.commit()

        msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[session['email']])
        msg.body = f'Your OTP Code is {otp}. It will be valid for 60 seconds.'
        mail.send(msg)
        return redirect(url_for("verify_otp"))
    
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

    bloccato = db.session.get(UtentiBloccati, user.email)
    session['email'] = user.email
    if bloccato:
        return redirect(url_for('blocked'))

    if bcrypt.check_password_hash(user.attivazione_2fa, '1'):
        if user.segreto_otp is None:
            segreto_otp = pyotp.random_base32()  # Genero segreto e inserisco nel db
            segreto_criptato = cipher_suite.encrypt(segreto_otp.encode())
            user.segreto_otp = segreto_criptato.decode()
            db.session.commit()

        segreto_decifrato = cipher_suite.decrypt(user.segreto_otp.encode()).decode()
        # Genero otp e invio mail - pyotp gestisce finestra di validità otp
        totp = pyotp.TOTP(segreto_decifrato)
        otp = totp.now()
        user.tentativi_login = 0
        db.session.commit()

        msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[session['email']])
        msg.body = f'Your OTP Code is {otp}. It will be valid for 60 seconds.'
        mail.send(msg)
        return redirect(url_for("verify_otp"))
    
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
        
    bloccato = db.session.get(UtentiBloccati, user.email)
    session['email'] = user.email
    if bloccato:
        return redirect(url_for('blocked'))
 
    if bcrypt.check_password_hash(user.attivazione_2fa, '1'):
        if user.segreto_otp is None:
            user.segreto_otp = pyotp.random_base32()  # Generate OTP secret
            db.session.commit()
        # Generate OTP and send via email
        totp = pyotp.TOTP(user.segreto_otp)
        otp = totp.now()
        # user.scad_otp = datetime.now() + timedelta(minutes=1)  # Set expiry time
        user.tentativi_login = 0
        db.session.commit()

        msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[session['email']])
        msg.body = f'Your OTP Code is {otp}. It will be valid for 60 seconds.'
        mail.send(msg)
        return redirect(url_for("verify_otp"))
    
    session.permanent = True
    session['username'] = user.username
    session['password'] = user.password
    session['id'] = user.id
    return redirect(url_for("main_route"))


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if 'email' in session:

        user = Users.query.filter_by(email=session['email']).first()

        if request.method == 'POST':
            otp = request.form['otp']
            segreto_decifrato = cipher_suite.decrypt(user.segreto_otp.encode()).decode()
            totp = pyotp.TOTP(segreto_decifrato)
            # Verifica OTP e controllo scadenza
            if totp.verify(otp, valid_window=1): #1 minuto finestra
                user.tentativi_login = 0
                db.session.commit()
                login_user(user)
                session.permanent = True
                session['username'] = user.username
                session['id'] = user.id
                return redirect(url_for('main_route'))
            else:
                user.tentativi_login += 1
                db.session.commit()
                if user.tentativi_login > 3:
                    flash('Too many failed attempts. Please try to log in again.', 'errore')
                    user.tentativi_login = 0
                    db.session.commit()
                    return redirect(url_for('login'))
                flash('Invalid or expired OTP, please try again.', 'errore')
        
        return render_template('verify_otp.html')
    
    else:
        return redirect(url_for('login')) # In caso l'utente rimanga sulla pagina e la sessione scada


#RECUPERO PSW
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
            # print(f"Errore durante il reset della password: {str(e)}")
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
                # print(f"Errore durante il reset della password: {str(e)}")
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
        flash('Token not valid or expired.', 'error')
        if 'id' in session:
            return redirect(url_for('account'))
        return redirect(url_for('recupera_psw', token_sended=True))

    user = Users.query.filter_by(email=email).first()
    if user:
        if not is_valid_password(new_password):
            flash('The password is not strong enough.', 'error')
            if 'id' in session:
                return redirect(url_for('account'))
            return redirect(url_for('recupera_psw', token_sended=True))
        if new_password != confirm_new_password:
            flash('The passwords do not match.', 'error')
            if 'id' in session:
                return redirect(url_for('account'))
            return redirect(url_for('recupera_psw', token_sended=True))
        hashed_password = bcrypt.generate_password_hash(new_password)
        user.password = hashed_password
        db.session.commit()
        flash('Password successfully updated.', 'success')
        return redirect(url_for('account'))
    else:
        flash('User error.', 'error')

    return redirect(url_for('login'))


#IMPOSTAZIONI E MODIFICA ACCOUNT

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'id' in session:

        blocked = user_blocked()
        if blocked:
            return blocked
        
        user_id = session['id']
        user = db.session.get(Users, user_id)
        
        if user:
            return render_template("account.html", username=user.username, email=user.email, data_nascita=user.data_di_nascita.strftime('%Y-%m-%d') if user.data_di_nascita else "N/A", diete=user.diete, intolleranze=user.intolleranze, attivazione_2fa=bcrypt.check_password_hash(user.attivazione_2fa, '1'))
    
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
        
        if not is_valid_password(new_password):
            flash('New password is too simple', 'error')
            return redirect(url_for('account'))

        if new_password != confirm_new_password:
            flash('New passwords do not match', 'error')
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

        selected_diets = request.form.getlist('diet')
        selected_allergies = request.form.getlist('allergies')
        selected_2fa = request.form.get('attiva-2fa') == 'on'
        user = db.session.get(Users, user_id)

        user.diete = selected_diets
        user.intolleranze = selected_allergies
        user.attivazione_2fa = bcrypt.generate_password_hash('1' if selected_2fa else '0').decode('utf-8')

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
        blocked = user_blocked()
        if blocked:
            return blocked
        
        return render_template("ricetta.html")
    
    return redirect(url_for('login'))

#PASSAGGIO RUOLO AL FRONTEND

@app.route('/get-user-info', methods=['GET'])
def get_user_info():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        if user:
            return jsonify({'ruolo_utente': user.ruolo, 'user_email': user.email})
    return jsonify({'ruolo_utente': None, 'user_email': None})


#GESTIONE RICETTE PREFERITE

@app.route('/add_to_favourites', methods=['POST'])
def add_to_favourites():
    if 'id' in session:

        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        username = db.session.get(Users, user_id).username
        recipe_id = request.json.get('recipe_id')

        if not recipe_id:
            return jsonify({'error': 'Missing recipe_id'}), 400
        
        existing_favourite = Favourite.query.filter_by(recipe_id=recipe_id, email=user_email).first()
        if existing_favourite:
            return jsonify({'error': 'Recipe is already in favourites'}), 409

        favourite = Favourite(username=username, recipe_id=recipe_id, email=user_email)
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
        blocked = user_blocked()
        if blocked:
            return blocked
        
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
        blocked = user_blocked()
        if blocked:
            return blocked
        
        user = db.session.get(Users, user_id)
        items = ShoppingIngredient.query.filter_by(email=user.email).all()
        lista_spesa = [item.ingredient for item in items]

        return render_template("lista_spesa.html", lista=lista_spesa)
    return redirect(url_for('login'))


@app.route('/update_shopping_list', methods=['POST'])
def update_shopping_list():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)

        ingredient = request.form.get('ingredient')

        if ingredient:
            existing_item = ShoppingIngredient.query.filter_by(email=user.email, ingredient=ingredient).first()
            if not existing_item:
                new_item = ShoppingIngredient(username=user.username, email=user.email, ingredient=ingredient)
                db.session.add(new_item)
                db.session.commit()

            return jsonify({'message': f'{ingredient} aggiunto alla lista della spesa!'}), 200

    return redirect(url_for('login'))


@app.route('/get_shopping_list', methods=['GET'])
def get_shopping_list():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)
        if user:
            items = ShoppingIngredient.query.filter_by(email=user.email).all()
            lista_spesa = [item.ingredient for item in items]
            return jsonify({'lista_spesa': lista_spesa}), 200
    return redirect(url_for('login'))

@app.route('/remove_from_shopping_list', methods=['POST'])
def remove_from_shopping_list():
    if 'id' in session:
        user_id = session['id']
        user = db.session.get(Users, user_id)

        data = request.get_json()
        ingredient = data.get('ingredient')

        if ingredient:
            item_to_remove = ShoppingIngredient.query.filter_by(email=user.email, ingredient=ingredient).first()
            if item_to_remove:
                db.session.delete(item_to_remove)
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

        is_in_list = ShoppingIngredient.query.filter_by(email=user.email, ingredient=ingredient).first() is not None
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
    comments_list = []
    
    for c in comments:
        user = Users.query.filter_by(email=c.email).first()
        if user:
            ruolo_autore = user.ruolo
        else:
            ruolo_autore = 1 # Se l'account non esiste più
        
        comments_list.append({
            'comment_id': c.comment_id,
            'email': c.email, 
            'username': c.username,
            'comment': c.comment,
            'rating': c.rating,
            'timestamp': c.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'segnalazione': c.segnalazione,
            'ruolo_autore': ruolo_autore  
        })
    
    return jsonify(comments_list)

@app.route('/submit-comment', methods=['POST'])
def submit_comment():

    if 'id' in session:
        user_id = session['id']
        blocked = user_blocked()
        if blocked:
            return blocked

        user = db.session.get(Users, user_id)
        recipe_id = request.form.get('recipe_id') 
        comment_text = request.form.get('comment')
        rating = request.form.get('rating')

        new_comment = Comments(
            recipe_id=recipe_id,
            email=user.email,
            username=user.username,
            comment=comment_text,
            rating=int(rating)
        )
        
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment successfully posted.', 'riuscito')
        return redirect(url_for('ricetta', id=recipe_id))
    
    else:
        return redirect(url_for('login'))
 

#GESTIONE UTENTI DA PARTE DI MODERATORI E AMMINISTRATORI
@app.route('/elimina_commento/<int:comment_id>', methods=['POST'])
def elimina_commento(comment_id):

    if 'id' in session:
        
        recipe_id = request.form.get('recipe_id')
        user_id = session['id']
        ruolo_utente = db.session.get(Users, user_id).ruolo
        email_utente = db.session.get(Users, user_id).email
        comment = db.session.get(Comments, comment_id)

        blocked = user_blocked()
        if blocked:
            return blocked

        if comment:
            autore_commento = Users.query.filter_by(email=comment.email).first()
            if autore_commento:
                ruolo_autore = autore_commento.ruolo
            else:
                ruolo_autore = 1

            if comment.email != email_utente and ruolo_utente <= ruolo_autore:
                # Se l'utente non ha il ruolo adeguato non può procedere:
                if ruolo_utente < 2:
                    return redirect(url_for('main_route'))
            
            db.session.delete(comment)
            db.session.commit()
            flash('Comment successfully deleted.', 'riuscito')
            return redirect(url_for('ricetta', id=recipe_id))
        
        else:
            flash('Comment no longer available.', 'errore')
            return redirect(url_for('ricetta', id=recipe_id))
        
    return redirect(url_for('login'))



@app.route('/blocca_utente/<int:comment_id>', methods=['POST'])
def blocca_utente(comment_id):

    if 'id' in session:
        recipe_id = request.form.get('recipe_id')
        user_id = session['id']
        user_email = db.session.get(Users, user_id).email
        ruolo_utente = db.session.get(Users, user_id).ruolo

        blocked = user_blocked()
        if blocked:
            return blocked

        # Se l'utente non ha il ruolo adeguato non può procedere:
        if ruolo_utente < 2:
            return redirect(url_for('main_route'))
        
        else:
            comment = Comments.query.filter_by(comment_id=comment_id).first()

            if comment:
                if user_email != comment.email:

                    autore_commento = Users.query.filter_by(email=comment.email).first()
                    if autore_commento:
                        ruolo_autore = autore_commento.ruolo
                    else:
                        ruolo_autore = 1

                    # Gli utenti dello stesso ruolo non si possono bloccare fra loro e
                    # i moderatori non possono bloccare gli amministratori
                    if ruolo_autore >= ruolo_utente:
                        return redirect(url_for('main_route'))
                    
                    email = comment.email
                    username = comment.username
                    commento_offensivo = comment.comment
                    
                    # Elimino il commento e blocco utente responsabile se non è già bloccato
                    db.session.delete(comment)
                    db.session.commit()
                    giàAggiunto = UtentiBloccati.query.filter_by(email=email).first()

                    if(giàAggiunto is None):
                        if autore_commento:

                            id_utente = autore_commento.id
                            # Invio notifica
                            msg = Message('TastyClick Account blocked', sender=app.config['MAIL_USERNAME'], recipients=[email])
                            msg.body = f"Hello {comment.username},\nWe inform you that your account has been blocked for "\
                                       "violating the platform's policy. You can view the details of the block and submit a reactivation "\
                                       "request on the page that will be shown to you at your next login.\n\nTastyClick Team"
                            mail.send(msg)
                        
                        else:
                            # Potrebbe succedere che l'utente abbia cancellato il proprio account 
                            # dopo aver lasciato i commenti e prima di essere bloccato
                            id_utente = None 

                        utente_bloccato = UtentiBloccati(
                            id_utente=id_utente,
                            id_moderatore=user_id,  # Moderatore che esegue il blocco
                            username=username,
                            email=email,
                            commento_offensivo=commento_offensivo,
                            ricetta_interessata=recipe_id
                        )

                        db.session.add(utente_bloccato)
                        db.session.commit()
                        flash('The user has been successfully blocked.', 'riuscito')
                    else:
                        flash('The user is already blocked. Comment successfully deleted.', 'riuscito')
                    return redirect(url_for('ricetta', id=recipe_id))
                    
                else:
                    return redirect(url_for('ricetta', id=recipe_id))
            else:
                flash('Comment no longer available.', 'errore')
                return redirect(url_for('ricetta', id=recipe_id))  

    return redirect(url_for('login'))  



#Gestione pagina per utenti bloccati
@app.route('/blocked', methods=['GET', 'POST'])
def blocked():
    
    if 'email' in session:

        bloccato = UtentiBloccati.query.filter_by(email=session['email']).first()
        if not bloccato:
            return redirect(url_for('login'))

        richiesta = RichiestaSblocco.query.filter_by(email=session['email']) 
        if richiesta is None:
            richiesta_effettuata = 0
        else:
            richiesta_effettuata = 1
        # print(richiesta_effettuata)

        if request.method == 'POST':

            testo_richiesta = request.form.get('testo_richiesta')
            if richiesta_effettuata == 0:
                return redirect(url_for('blocked'))

            nuova_richiesta = RichiestaSblocco(
                id_utente=bloccato.id_utente,
                email=session['email'],
                commento_offensivo=bloccato.commento_offensivo,
                ricetta_interessata=bloccato.ricetta_interessata,
                data_blocco=bloccato.data_blocco,
                testo_richiesta=testo_richiesta
            )

            db.session.add(nuova_richiesta)
            db.session.commit()
            return redirect(url_for('blocked'))

        return render_template('blocked.html')
    
    else:
        return redirect(url_for('login'))



@app.route('/get_block_info', methods=['GET'])
def get_block_info():
    if 'email' in session:
        email = session['email']
        if not email:
            return jsonify({'error': 'Email non trovata nella sessione'}), 400

        bloccato = UtentiBloccati.query.filter_by(email=email).first()

        if not bloccato:
            return jsonify({'error': 'Utente non trovato'}), 404

        richiesta_effettuata = RichiestaSblocco.query.filter_by(email=email).first() is not None

        data = {
            'email': bloccato.email,
            'username': bloccato.username,
            'commento_offensivo': bloccato.commento_offensivo,
            'ricetta_interessata': bloccato.ricetta_interessata,
            'data_blocco': bloccato.data_blocco.strftime('%Y-%m-%d %H:%M:%S'),  
            'richiesta_effettuata': richiesta_effettuata
        }
        return jsonify(data)
    
    else:
        return redirect(url_for('login'))


# Gestione admin-tools
from sqlalchemy.sql import func
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'id' in session:

        ruolo_utente = db.session.get(Users, session['id']).ruolo
        
        if ruolo_utente < 3:
            return redirect(url_for('main_route'))
        
        
        num_users = db.session.query(func.count(Users.id)).scalar()
        num_banned = db.session.query(func.count(UtentiBloccati.email)).scalar()
        
        avg_comments = db.session.query(func.round(func.count(Comments.comment_id) / func.count(func.distinct(Users.email)), 3)).join(Users, Comments.email == Users.email).scalar()

        
        users = db.session.query(Users, UtentiBloccati.email.label('banned'))\
                        .outerjoin(UtentiBloccati, Users.email == UtentiBloccati.email)\
                        .all()

        return render_template('admin.html',
                                num_users=num_users, 
                                num_banned=num_banned, 
                                avg_comments=avg_comments, 
                                users=users)
    else:
        return redirect(url_for('login'))

@app.route('/change_role', methods=['POST'])
def change_role():
    email = request.form.get('email')
    new_role = request.form.get('new_role')

    user = Users.query.filter_by(email=email).first()
    if user:
        if user.ruolo == 3 and int(new_role) < 3: 
            flash(f"You cannot demote another administrator.", 'error')
        else:
            user.ruolo = int(new_role)
            db.session.commit()
            flash(f"Role for {email} changed successfully.", 'success')
    else:
        flash(f"User with email {email} not found.", 'error')

    return redirect(url_for('admin'))


# Gestione richieste riammissione
@app.route('/sban', methods=['GET', 'POST'])
def sban():
    if 'id' in session:
        blocked = user_blocked()
        if blocked:
            return blocked

        ruolo_utente = db.session.get(Users, session['id']).ruolo
        # Se l'utente non ha il ruolo adeguato non può procedere:
        if ruolo_utente < 2:
            return redirect(url_for('main_route'))
        
        if request.method == 'POST':
            email = request.form.get('email')

            bloccato = UtentiBloccati.query.filter_by(email=email).first()
            if bloccato:
                db.session.delete(bloccato)
            
            richiesta = RichiestaSblocco.query.filter_by(email=email).first()
            if richiesta:
                db.session.delete(richiesta)
            
            db.session.commit()

            utente_bannato = Users.query.filter_by(email=email).first()
            if not utente_bannato:

                flash("This user's account could not be found in the database.", 'errore')
                return redirect(url_for('sban'))
            
            else:

                # Invio notifica
                msg = Message('TastyClick Account Reactivation', sender=app.config['MAIL_USERNAME'], recipients=[email])
                msg.body = f"Hello {utente_bannato.username},\nWe inform you that your reactivation request has been accepted "\
                           "and your TastyClick account has been successfully reactivated!!\n You can now access the platform again."\
                           "\n\nSee you soon,\nTastyClick Team"
                mail.send(msg)
                flash(f"The User with email {email} has been successfully unlocked and a notification has been sent to his address.", 'riuscito')
                return redirect(url_for('sban'))

        return render_template('sban.html')
    
    else:
        return redirect(url_for('login'))



@app.route('/get-requests', methods=['GET'])
def get_requests():
    richieste = RichiestaSblocco.query.all()
    richieste_list = [
        {
            'id_utente': r.id_utente,
            'email': r.email,
            'commento_offensivo': r.commento_offensivo,
            'ricetta_interessata': r.ricetta_interessata,
            'data_blocco': r.data_blocco,
            'testo_richiesta': r.testo_richiesta
        } for r in richieste
    ]
    return jsonify(richieste_list)



#Gestione invio email segnalazione 
@app.route('/invia_segnalazione/<int:comment_id>', methods=['POST'])
def invia_segnalazione(comment_id):
    if 'id' in session:
        user_id = session['id']
        recipe_id = request.form.get('recipe_id')
        ruolo_utente = db.session.get(Users, user_id).ruolo

        blocked = user_blocked()
        if blocked:
            return blocked

        # Se l'utente non ha il ruolo adeguato non può procedere:
        if ruolo_utente < 2:
            return redirect(url_for('main_route'))

        comment = Comments.query.filter_by(comment_id=comment_id).first()
        if not comment:
            flash('Comment no longer available.', 'errore')
            return redirect(url_for('ricetta', id=recipe_id))
        
        autore_commento = Users.query.filter_by(email=comment.email).first()
        if autore_commento:
            ruolo_autore = autore_commento.ruolo
        else:
            ruolo_autore = 1

        if ruolo_autore >= ruolo_utente:
            return redirect(url_for('main_route'))
        
        # Se una segnalazione è già stata mandata per quel commento
        if comment.segnalazione == 1:
            return redirect(url_for('ricetta', id=recipe_id))

        msg = Message('Report of inappropriate behavior', sender=app.config['MAIL_USERNAME'], recipients=[comment.email])
        msg.body = f"Hello {comment.username},\nA moderator has noticed that one of your comments may be offensive or inappropriate for the platform."\
                   "We encourage you to be more careful and to moderate your language in the future.\n\n"\
                    f"Comment details:\n"\
                    f"Comment: {comment.comment}\n"\
                    f"Rating: {comment.rating}\n"\
                    f"Id recipe: {comment.recipe_id}\n"\
                    f"Date: {comment.timestamp}\n"\
                    "\nThank you for your understanding,\nTastyClick Team"
                   
        mail.send(msg)
        comment.segnalazione = 1
        db.session.commit()
        flash('Report successfully sent.', 'riuscito')
        return redirect(url_for('ricetta', id=recipe_id))
    
    else:
        return redirect(url_for('login'))
    


#Per controllare se l'utente attuale sia stato bloccato mentre è loggato
#e impedire ulteriori danni
def user_blocked():
    if 'id' in session:
        user_id = session['id']
        bloccato = UtentiBloccati.query.filter_by(id_utente=user_id).first()
        if bloccato is not None:
            session.pop('id', None)
            session.pop('username', None)
            session.pop('email', None)
            session.pop('password', None)
            return redirect(url_for('login'))
    return None  


@app.route('/api/keys', methods=['GET'])
def get_keys():
    return jsonify({'rapid_api_key': chiavi.rapid_api_key, 'rapid_api_host': chiavi.rapid_api_host})


@app.route('/<something>')
def goto(something):
    return redirect(url_for('main_route'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'fav.ico',mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(debug=True)
