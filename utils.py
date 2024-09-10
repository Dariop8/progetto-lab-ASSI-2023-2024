import re
import string
import secrets
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
from flask import current_app
from datetime import timedelta, datetime
import os




pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+{}:;<>,.?/~])[A-Za-z\d!@#$%^&*()_+{}:;<>,.?/~]{10,}$'

def is_valid_password(password):
    if re.match(pattern, password):
        return True
    return False

def validate_comment_length(comment_text):
    if len(comment_text) < 10:
        raise ValueError("Commento deve essere lungo almeno 10 caratteri.")

def validate_rating(rating_value):
    if not (1 <= rating_value <= 5):
        raise ValueError("Rating deve essere tra 1 e 5.")
    
def validate_ruolo(ruolo_value):
    if not (1 <= ruolo_value <= 3):
        raise ValueError("Il ruolo deve essere compreso tra 1 e 3.")

def generate_password():
    while True:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+{}:;<>,.?/~"
        
        #caratteri obbligatori nella psw
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*()_+{}:;<>,.?/~")
        ]
        #lunga 12
        password += [secrets.choice(alphabet) for _ in range(14)]
        #shuffle senno i primi 4 caratteri sono quelli che ho messo in password=[...]
        secrets.SystemRandom().shuffle(password)
        password = ''.join(password)
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+{}:;<>,.?/~])[A-Za-z\d!@#$%^&*()_+{}:;<>,.?/~]{10,}$'
        if re.match(pattern, password):
            return password

# per cambiare i salts ogni 6 ore
def rotate_salts():
    now = datetime.now()
    last_rotation = current_app.config.get('SALT_LAST_ROTATION')
    
    if last_rotation is None or now - last_rotation > timedelta(hours=1):
        current_app.config['PREVIOUS_SALT'] = current_app.config['CURRENT_SALT']
        current_app.config['CURRENT_SALT'] = os.urandom(16).hex()
        current_app.config['SALT_LAST_ROTATION'] = now

def generate_reset_token(email):
    rotate_salts()
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    current_salt = current_app.config['CURRENT_SALT']
    print(current_app.config['CURRENT_SALT'])
    return s.dumps(email, salt=current_salt)


def verify_reset_token(token, expiration=600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    current_salt = current_app.config['CURRENT_SALT']
    previous_salt = current_app.config.get('PREVIOUS_SALT')
    
    try:
        # tento di verificare con il salt attuale
        email = s.loads(token, salt=current_salt, max_age=expiration)
        print(current_app.config['CURRENT_SALT'])
        return email
    except SignatureExpired:
        return 
    except BadSignature:
        # se il token non è valido con il salt attuale, tento con il salt precedente
        if previous_salt:
            try:
                email = s.loads(token, salt=previous_salt, max_age=expiration)
                print(current_app.config['PREVIOUS_SALT'])
                return email
            except SignatureExpired:
                return 
            except BadSignature:
                return 
        else:
            return 

def send_reset_email(to_email, token):
    with current_app.app_context():
        mail = current_app.extensions.get('mail')
        if not mail:
            raise RuntimeError('Mail instance not found in current app context')

        msg = Message(
            'Reset Your Password',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[to_email]
        )
        msg.body = f'''To reset your password, use the following token (valid for 10 minutes):
{token}

If you did not request a password reset, please ignore this email.
'''
        mail.send(msg)


