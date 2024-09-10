import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import app, db, Users, Comments, Favourite
from sqlalchemy.exc import IntegrityError
from flask_testing import TestCase
from sqlalchemy import text
from flask import json



class Usermodel_test(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()
            db.session.execute(text('PRAGMA foreign_keys = ON'))
            db.session.query(Users).delete()  # Resetta il DB di test
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):
        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="pswd1234.")
            db.session.add(user)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertIsNotNone(fetched_user)
            self.assertEqual(fetched_user.username, "Marco")
            self.assertEqual(fetched_user.email, "marco@mail.com")

    def test_unique_email(self):
        with app.app_context():
            user1 = Users(username="utente1", email="utente@mail.com", password="pswd1234.")
            db.session.add(user1)
            db.session.commit()

            user2 = Users(username="utente2", email="utente@mail.com", password="pswd1234.")
            db.session.add(user2)

            with self.assertRaises(IntegrityError):
                db.session.commit()

    def test_unique_username(self):
        with app.app_context():
            user1 = Users(username="utente", email="utente1@mail.com", password="pswd1234.")
            db.session.add(user1)
            db.session.commit()

            user2 = Users(username="utente", email="utente2@mail.com", password="pswd1234.")
            db.session.add(user2)

            with self.assertRaises(IntegrityError):
                db.session.commit()

    def test_missing_fields(self):
        with app.app_context():
            missing_fields_users = [
                Users(username="Marco", password="password123", email=None),  
                Users(username=None, password="password123", email="marco@mail.com")]

            for user in missing_fields_users:
                try:
                    db.session.add(user)
                    db.session.commit()
                    self.fail("Expected IntegrityError not raised")
                except IntegrityError:
                    db.session.rollback()
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    db.session.rollback()
                    raise

    def test_missing_password(self):
        with app.app_context():
            try:
                user = Users(username="Marco", password="", email="marco@mail.com")
                db.session.add(user)
                db.session.commit()
                self.fail(f"Expected IntegrityError not raised")
            except IntegrityError:
                db.session.rollback()  
            except Exception as e:
                print(f"Unexpected exception occurred: {e}")
                db.session.rollback()

    def test_default_values(self):
        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="pswd1234.")
            db.session.add(user)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(fetched_user.tentativi_login, 0)
            self.assertEqual(fetched_user.ruolo, 1)

    def test_invalid_ruolo(self):
        with app.app_context():
            valid_roles = [1, 2, 3]
            for role in valid_roles:
                user = Users(username=f"validuser{role}", email=f"validuser{role}@mail.com", password="pswd1234.", ruolo = role)
                db.session.add(user)
                db.session.commit()
                db.session.delete(user)  

            with self.assertRaises(ValueError) as context:
                user = Users(username="invaliduser", email = f"invaliduser{role}@mail.com", password="pswd1234.", ruolo=5)
                db.session.add(user)
                db.session.commit()
                self.fail(f"Expected IntegrityError for ruolo={role}, but no error was raised")

            self.assertEqual(str(context.exception), "Il ruolo deve essere compreso tra 1 e 3.")

    def test_user_comments(self):
        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="pswd1234.")
            db.session.add(user)
            db.session.commit()

            comment = Comments(recipe_id=1, email=user.email, username=user.username, comment="Ricetta facile e saporita.", rating=5)
            db.session.add(comment)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(len(fetched_user.comments), 1)
            self.assertEqual(fetched_user.comments[0].comment, "Ricetta facile e saporita.")



# ------------------------#


class UserRegistration_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()
            db.session.query(Users).delete()  # reset del database di test
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_registration_successful(self):
        response = self.client.post('/registrazione', data = {
            'email': 'marco@mail.com',
            'username': 'Marco',
            'password': 'a1c12DEF#GHIJ.',
            'password_conf': 'a1c12DEF#GHIJ.',
            'birthdate': '1997-10-01',
            'diet': [],
            'allergies': [],
            'attiva-2fa': 'on'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')
        user = Users.query.filter_by(email='marco@mail.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'Marco')

    def test_existing_user_error(self):
        user = Users(username='DiegoBc', email='diego@mail.com', password='123')
        db.session.add(user)
        db.session.commit()

        response = self.client.post('/registrazione', data = {
            'email': 'diego@mail.com',
            'username': 'DiegoBc',
            'password': 'a1c12DEF#GHIJ.',
            'password_conf': 'a1c12DEF#GHIJ.',
            'birthdate': '1997-10-01',
            'diet': [],
            'allergies': []})

        self.assertEqual(response.status_code, 200)  # resto sulla pagina di registrazione
        self.assertIn(b'User already registered.', response.data)

    def test_password_mismatch(self):
        response = self.client.post('/registrazione', data = {
            'email': 'dario@mail.com',
            'username': 'Dario',
            'password': 'a1c12DEF#GHIJ.',
            'password_conf': '1234',
            'birthdate': '1997-10-01',
            'diet': [],
            'allergies': []})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match.', response.data)

    def test_weak_password(self):
        response = self.client.post('/registrazione', data = {
            'email': 'red@mail.com',
            'username': 'Red24',
            'password': '123',
            'password_conf': '123',
            'birthdate': '1997-10-01',
            'diet': [],
            'allergies': []})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password is too weak.', response.data)

    def test_registration_get(self):
        response = self.client.get('/registrazione')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign Up', response.data)  

    def test_password_json(self):
        response = self.client.get('/generate_password')
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data)
        self.assertIn('password', data)

    def test_generate_password(self):
        response = self.client.get('/generate_password')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        password = data['password']

        self.assertGreaterEqual(len(password), 8)

        self.assertRegex(password, r'[A-Z]')

        self.assertRegex(password, r'[a-z]')

        self.assertRegex(password, r'[0-9]')

        self.assertRegex(password, r'[!@#$%^&*(),.?":{}|<>]')

    def test_generate_uniquepassword(self):
        response1 = self.client.get('/generate_password')
        response2 = self.client.get('/generate_password')

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        self.assertNotEqual(data1['password'], data2['password'])