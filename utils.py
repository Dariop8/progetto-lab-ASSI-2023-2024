import re
import string
import secrets
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Mail, Message
from flask import current_app


# La password deve contenere almeno 10 caratteri.
# Deve contenere almeno una lettera maiuscola.
# Deve contenere almeno una lettera minuscola.
# Deve contenere almeno un numero.
# Deve contenere almeno un carattere speciale.



pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+{}:;<>,.?/~])[A-Za-z\d!@#$%^&*()_+{}:;<>,.?/~]{10,}$'

def is_valid_password(password):
    if re.match(pattern, password):
        return True
    return False

#si puo aggiungere un suggeritore di password random
#e che le password siano aggiornate e modificate ogni tot tempo
#cost factor indica la sicurezza. se le macchine sono piu potenti allora lo aumento

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
        password += [secrets.choice(alphabet) for _ in range(8)]
        #shuffle senno i primi 4 caratteri sono quelli che ho messo in password=[...]
        secrets.SystemRandom().shuffle(password)
        password = ''.join(password)
        # Verifichiamo che la password rispetti il pattern
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+{}:;<>,.?/~])[A-Za-z\d!@#$%^&*()_+{}:;<>,.?/~]{10,}$'
        if re.match(pattern, password):
            return password


def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None
    return email

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
        msg.body = f'''Per resettare la tua password, usa il seguente token:
{token}

Se non hai richiesto il reset della password, ignora questa email.
'''
        mail.send(msg)
