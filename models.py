import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import  UserMixin
from datetime import datetime, timezone
from sqlalchemy.types import Date
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import CheckConstraint
from utils import validate_comment_length, validate_rating, validate_ruolo
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint
from flask_login import UserMixin
import bcrypt
db = SQLAlchemy()


def configure_bcrypt(bcrypt_instance):
    global bcrypt
    bcrypt = bcrypt_instance

class Comments(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), db.ForeignKey('users.email', ondelete="CASCADE"), nullable=False)
    username = db.Column(db.String(30), db.ForeignKey('users.username', ondelete="CASCADE"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    segnalazione = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint('length(comment) >= 10', name='check_comment_length'),
        CheckConstraint('rating BETWEEN 1 AND 5', name='check_rating_range'),
    )

    def __init__(self, recipe_id, email, username, comment, rating):
        if comment:
            validate_comment_length(comment)
        if rating:
            validate_rating(rating)

        self.recipe_id = recipe_id
        self.email = email
        self.username = username
        self.comment = comment
        self.rating = rating



class Favourite(db.Model):
    __tablename__ = 'favourite'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), db.ForeignKey('users.email', ondelete="CASCADE"), nullable=False)
    username = db.Column(db.String(30), db.ForeignKey('users.username', ondelete="CASCADE"), nullable=False)
    note = db.Column(db.String(300), nullable=False, default="")

    def __init__(self, username=None, recipe_id=None, email=None):
        self.recipe_id = recipe_id
        self.username = username
        self.email = email
        self.note=""

class ShoppingIngredient(db.Model):
    __tablename__ = 'shopping_ingredient'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), db.ForeignKey('users.email', ondelete="CASCADE"), nullable=False)
    username = db.Column(db.String(30), db.ForeignKey('users.username', ondelete="CASCADE"), nullable=False)
    ingredient = db.Column(db.String(300), nullable=False, default="")

    def __init__(self, username=None, email=None, ingredient=None):
        self.email = email
        self.username = username
        self.ingredient=ingredient



class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(30), nullable=False, unique=True)    
    password = db.Column(db.String(250), nullable=False) # rinominato in _password
    data_di_nascita = db.Column(Date, nullable=True)
    diete = db.Column(JSON, nullable=True)
    intolleranze = db.Column(JSON, nullable=True)
    attivazione_2fa = db.Column(db.String(250), nullable=True)
    segreto_otp = db.Column(db.String(16), nullable=True) 
    tentativi_login = db.Column(db.Integer, default=0, nullable=False)  
    ruolo = db.Column(db.Integer, default=1, nullable=False)

    posta = db.relationship('Comments', backref='user', lazy=True, cascade="all, delete", foreign_keys='Comments.email')
    fav = db.relationship('Favourite', backref='user', lazy=True, cascade="all, delete", foreign_keys='Favourite.email')
    agg = db.relationship('ShoppingIngredient', backref='user', lazy=True, cascade="all, delete", foreign_keys='ShoppingIngredient.email')
    effettua = db.relationship('RichiestaSblocco', backref='user', lazy=True, cascade="all, delete", foreign_keys='RichiestaSblocco.email')
    ban = db.relationship('UtentiBloccati', foreign_keys='UtentiBloccati.id_utente', backref='utente_bloccato', lazy=True, cascade="all, delete")

    
    __table_args__ = (
        db.CheckConstraint('ruolo BETWEEN 1 AND 3', name='check_ruolo_range'),
    )
    
    def __init__(self, username=None, password=None, email=None, data_di_nascita=None, diete=None, intolleranze=None, attivazione_2fa=False, segreto_otp=None, tentativi_login=0, ruolo=1):
        if ruolo:
            validate_ruolo(ruolo)
        
        self.username = username
        self.password = password
        self.email = email
        self.data_di_nascita = data_di_nascita
        self.diete = diete if diete is not None else []
        self.intolleranze = intolleranze if intolleranze is not None else []
        self.attivazione_2fa = bcrypt.generate_password_hash('1' if attivazione_2fa else '0').decode('utf-8')
        self.segreto_otp = segreto_otp
        self.tentativi_login = tentativi_login
        self.ruolo = ruolo


class UtentiBloccati(db.Model):
    __tablename__ = 'utenti_bloccati'

    email = db.Column(db.String(120), db.ForeignKey('users.email', ondelete="CASCADE"), primary_key=True)
    username = db.Column(db.String(30), db.ForeignKey('users.username', ondelete="CASCADE"), unique=True, nullable=False)
    id_utente = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)
    id_moderatore = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    commento_offensivo = db.Column(db.Text, nullable=True)
    ricetta_interessata = db.Column(db.Integer, nullable=True)
    data_blocco = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('commento_offensivo', 'ricetta_interessata', 'data_blocco', name='uq_blocco'),
        db.CheckConstraint('id_utente != id_moderatore', name='check_moderatore_diverso'),
    )

    effettua = db.relationship('RichiestaSblocco', backref='utente_bloccato', cascade="all, delete-orphan")


    def __init__(self, email, username, id_utente=None, id_moderatore=None, commento_offensivo=None, ricetta_interessata=None):
        self.email = email
        self.username = username
        self.id_utente = id_utente
        self.id_moderatore = id_moderatore
        self.commento_offensivo = commento_offensivo
        self.ricetta_interessata = ricetta_interessata



class RichiestaSblocco(db.Model):
    __tablename__ = 'richieste_sblocco'
    
    id_utente = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), unique=True, nullable=False)
    email = db.Column(db.String(120), db.ForeignKey('users.email', ondelete="CASCADE"), primary_key=True)   
    commento_offensivo = db.Column(db.Text, nullable=True)
    ricetta_interessata = db.Column(db.Integer, nullable=True)
    data_blocco = db.Column(db.DateTime, nullable=True)  
    testo_richiesta = db.Column(db.Text, nullable=False)
    data_richiesta = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=True)  


    __table_args__ = (
        db.ForeignKeyConstraint(
            ['commento_offensivo', 'ricetta_interessata', 'data_blocco'],
            ['utenti_bloccati.commento_offensivo', 'utenti_bloccati.ricetta_interessata', 'utenti_bloccati.data_blocco'],
            name='fk_richiesta_blocco'
        ),
    )


    def __init__(self, id_utente, email, commento_offensivo, ricetta_interessata, data_blocco, testo_richiesta):
        self.id_utente = id_utente
        self.email = email
        self.commento_offensivo = commento_offensivo
        self.ricetta_interessata = ricetta_interessata
        self.data_blocco = data_blocco
        self.testo_richiesta = testo_richiesta
        self.data_richiesta = datetime.now(timezone.utc) 
 