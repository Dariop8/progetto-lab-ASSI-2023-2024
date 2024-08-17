import re
import bcrypt
import base64

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

#inserire real time indicatore mentre scrivo che dice se la psw è debole, sicura ecc (5 livelli)
#si puo aggiungere un suggeritore di password random
#e che le password siano aggiornate e modificate ogni tot tempo
#cost factor indica la sicurezza. se le macchine sono piu potenti allora lo aumento
#meglio usare Argon2 o scrypt che spostano la complessità sulla memoria e no CPU (ram costa piu di cpu)
