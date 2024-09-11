import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import app, db, Users, Comments, Favourite, RichiestaSblocco, ShoppingIngredient, UtentiBloccati
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
            self.assertEqual(len(fetched_user.posta), 1)
            self.assertEqual(fetched_user.posta[0].comment, "Ricetta facile e saporita.")

    def test_favourites(self):

        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            favourite = Favourite(recipe_id=1, username=user.username, email=user.email)
            db.session.add(favourite)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(len(fetched_user.fav), 1)
            self.assertEqual(fetched_user.fav[0].recipe_id, 1)

    def test_shopping_ingredients(self):
        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            ingredient = ShoppingIngredient(email=user.email, username=user.username, ingredient="Farina")
            db.session.add(ingredient)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(len(fetched_user.agg), 1)
            self.assertEqual(fetched_user.agg[0].ingredient, "Farina")

    def test_banned_user(self):
        with app.app_context():
            mod = Users(username="Giulio", email="giulio@mail.com", password="Pass1234.", ruolo=2)
            db.session.add(mod)
            db.session.commit()

            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            comment = Comments(recipe_id=1, email=user.email, username=user.username, comment="Commento offensivo", rating=1)
            db.session.add(comment)
            db.session.commit()

            ban = UtentiBloccati(email=user.email, username=user.username, id_utente=user.id, id_moderatore=1, commento_offensivo="Commento offensivo", ricetta_interessata=1)
            db.session.add(ban)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(len(fetched_user.ban), 1)
            self.assertEqual(fetched_user.ban[0].commento_offensivo, "Commento offensivo")

    def test_ban_mod_user(self):
        with app.app_context():
            mod = Users(username="Giulio", email="giulio@mail.com", password="Pass1234.", ruolo=2)
            db.session.add(mod)
            db.session.commit()

            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            comment = Comments(recipe_id=1, email=user.email, username=user.username, comment="Commento offensivo", rating=1)
            db.session.add(comment)
            db.session.commit()

            ban = UtentiBloccati(email=user.email, username=user.username, id_utente=user.id, id_moderatore=1, commento_offensivo="Commento offensivo", ricetta_interessata=1)
            db.session.add(ban)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="giulio@mail.com").first()
            self.assertEqual(len(fetched_user.ban_mod), 1)
            self.assertEqual(fetched_user.ban_mod[0].commento_offensivo, "Commento offensivo")

    def test_unlock_request(self):
        with app.app_context():
            mod = Users(username="Giulio", email="giulio@mail.com", password="Pass1234.", ruolo=2)
            db.session.add(mod)
            db.session.commit()

            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            comment = Comments(recipe_id=1, email=user.email, username=user.username, comment="Commento offensivo", rating=1)
            db.session.add(comment)
            db.session.commit()

            banned_user = UtentiBloccati(email=user.email, username=user.username, id_utente=user.id, id_moderatore=1, commento_offensivo="Commento offensivo", ricetta_interessata=1)
            db.session.add(ba