import sys
import os
from flask_testing import TestCase
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import app, db, Comments, Users, Favourite
from sqlalchemy.exc import IntegrityError


class Comment_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        with self.app.app_context():
            db.create_all()
            self.recipe_id = 1

            comment = Comments(
                recipe_id = self.recipe_id,
                email = 'marco@mail.com',
                username = 'Marco',
                comment = 'Facile e saporita.',
                rating = 5)
            
            db.session.add(comment)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_comment_creation(self):
        comment = Comments.query.filter_by(recipe_id=self.recipe_id, email='marco@mail.com').first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.recipe_id, 1)
        self.assertEqual(comment.email, 'marco@mail.com')
        self.assertEqual(comment.username, 'Marco')
        self.assertEqual(comment.comment, 'Facile e saporita.')
        self.assertEqual(comment.rating, 5)

class User_test(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):

        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertIsNotNone(fetched_user)
            self.assertEqual(fetched_user.username, "Marco")
            self.assertEqual(fetched_user.email, "marco@mail.com")

    def test_unique_email(self):

        with app.app_context():
            user1 = Users(username="user1", email="user@mail.com", password="Pass1234.")
            db.session.add(user1)
            db.session.commit()

            user2 = Users(username="user2", email="user@mail.com", password="Pass1234.")
            db.session.add(user2)

            with self.assertRaises(IntegrityError):
                db.session.commit()

    def test_unique_username(self):

        with app.app_context():
            user1 = Users(username="utente24", email="user1@example.com", password="Pass1234.")
            db.session.add(user1)
            db.session.commit()

            user2 = Users(username="utente24", email="user2@example.com", password="Pass1234.")
            db.session.add(user2)

            with self.assertRaises(IntegrityError):
                db.session.commit()

    def test_password(self):

        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            
            self.assertNotEqual(fetched_user.password, "Pass1234.")
            self.assertTrue(fetched_user.password.startswith("$2b$"))

    def test_comments(self):

        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            comment = Comments(recipe_id=1, email=user.email, username=user.username, comment="Ricetta gustosa", rating=5)
            db.session.add(comment)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(len(fetched_user.comments), 1)
            self.assertEqual(fetched_user.comments[0].comment, "Ricetta gustosa")

    def test_favourites(self):

        with app.app_context():
            user = Users(username="Marco", email="marco@mail.com", password="Pass1234.")
            db.session.add(user)
            db.session.commit()

            favourite = Favourite(recipe_id=1, email=user.email)
            db.session.add(favourite)
            db.session.commit()

            fetched_user = Users.query.filter_by(email="marco@mail.com").first()
            self.assertEqual(len(fetched_user.favourites), 1)
            self.assertEqual(fetched_user.favourites[0].recipe_id, 1)