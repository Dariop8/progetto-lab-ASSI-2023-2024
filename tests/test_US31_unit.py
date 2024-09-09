import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import app, db, Users, Comments
from sqlalchemy.exc import IntegrityError
from flask_testing import TestCase
from datetime import datetime
from sqlalchemy import text
from flask import json


class CommentModel_test(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()
            db.session.execute(text('PRAGMA foreign_keys = ON'))  # vincoli di integrità
            db.session.query(Comments).delete() 
            db.session.query(Users).delete()  
            db.session.commit()

            test_user = Users(
                username="Marco",
                password="Marco24063!",
                email="marco@mail.com",
                data_di_nascita=datetime(2000, 1, 1),
                diete=[],
                intolleranze=[],
                attivazione_2fa=False
            )
            db.session.add(test_user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_comment_creation(self):
        with app.app_context():
            comment = Comments(
                recipe_id=1,
                email="marco@mail.com",
                username="Marco",
                comment="Adatta a tutti.",
                rating=5
            )
            db.session.add(comment)
            db.session.commit()

            saved_comment = Comments.query.filter_by(email="marco@mail.com").first()

            self.assertIsNotNone(saved_comment)
            self.assertEqual(saved_comment.recipe_id, 1)
            self.assertEqual(saved_comment.email, "marco@mail.com")
            self.assertEqual(saved_comment.username, "Marco")
            self.assertEqual(saved_comment.comment, "Adatta a tutti.")
            self.assertEqual(saved_comment.rating, 5)

    def test_invalid_email(self):
        with app.app_context():
            invalid_comment = Comments(
                recipe_id=1,
                email="diego2346@mail.com",  
                username="Marco",
                comment="piatto sano e veloce",
                rating=5
            )
            db.session.add(invalid_comment)
            
            with self.assertRaises(IntegrityError):
                db.session.commit()

    def test_invalid_username(self):
        with app.app_context():
            invalid_comment = Comments(
                recipe_id=1,
                email="marco@mail.com",  
                username="user280",  
                comment="piatto sano e veloce",
                rating=5
            )
            db.session.add(invalid_comment)
            
            with self.assertRaises(IntegrityError):
                db.session.commit()

    def test_comment_too_short(self):
            with app.app_context():
                with self.assertRaises(ValueError) as context:
                    short_comment = Comments(
                        recipe_id=1,
                        email="marco@mail.com",
                        username="Marco",
                        comment="ciao",  # Commento troppo corto
                        rating=5
                    )
                
                    db.session.add(short_comment)
                    db.session.commit()

                self.assertEqual(str(context.exception), "Commento deve essere lungo almeno 10 caratteri.")

    def test_rating_out_of_range(self):
        with app.app_context():
            with self.assertRaises(ValueError) as context:
                invalid_rating_comment = Comments(
                    recipe_id=1,
                    email="marco@mail.com",
                    username="Marco",
                    comment="Adatta a tutti.",
                    rating=11  # Rating non tra 1 e 5
                )
            
                db.session.add(invalid_rating_comment)
                db.session.commit()

            self.assertEqual(str(context.exception), "Rating deve essere tra 1 e 5.")

    def test_missing_fields(self):
        with app.app_context():
            missing_fields_comments = [
                Comments(recipe_id=1, email="marco@mail.com", username="Marco", comment=None, rating=5),  # Commento mancante
                Comments(recipe_id=1, email="marco@mail.com", username="Marco", comment="Adatta a tutti.", rating=None),  # rating mancante
                Comments(recipe_id=1, email=None, username="Marco", comment="Adatta a tutti.", rating=5)  # Email mancante
            ]

            for comment in missing_fields_comments:
                db.session.add(comment)
                try:
                    db.session.commit()
                    self.fail("Expected IntegrityError, DataError, or OperationalError not raised")
                except IntegrityError:
                    db.session.rollback()
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    db.session.rollback()
                    raise

    def test_default_values(self):
        with app.app_context():
            comment = Comments(
                recipe_id=1,
                email="marco@mail.com",
                username="Marco",
                comment="Adatta a tutti.",
                rating=5
            )
            db.session.add(comment)
            db.session.commit()

            saved_comment = Comments.query.filter_by(email="marco@mail.com").first()
            self.assertIsNotNone(saved_comment.timestamp)
            self.assertTrue(saved_comment.timestamp <= datetime.now())
            self.assertEqual(saved_comment.segnalazione, 0)



# ------------------------#


class Comments_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()
            db.session.query(Comments).delete() # reset db di test
            db.session.commit()

            user = Users(username='Marco', email='marco@mail.com', password='Marc1234.')
            db.session.add(user)
            db.session.commit()
            self.recipe_id = 1

    def tearDown(self):
        with app.app_context():
            db.session.remove()  
            db.drop_all()  

    def test_submit_comment(self): # route /submit-comment
        with self.client as c:
            with c.session_transaction() as sess:
                sess['id'] = 1
            response = c.post('/submit-comment', data = {
                'recipe_id': self.recipe_id,
                'comment': 'Facile e saporita.',
                'rating': 5})
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, f'/ricetta?id={self.recipe_id}') # reindirizzamento in caso di successo

            comment = Comments.query.filter_by(recipe_id=self.recipe_id, email='marco@mail.com').first() 
            self.assertIsNotNone(comment)
            self.assertEqual(comment.comment, 'Facile e saporita.')

    def test_get_comments(self): # route /get-comments
        with app.app_context():

            comment = Comments(
                recipe_id = self.recipe_id,
                email = 'marco@mail.com',
                username = 'Marco',
                comment = 'Facile e saporita.',
                rating = 5)
            
            db.session.add(comment)
            db.session.commit()
        
        with self.client:
            response = self.client.get(f'/get-comments/{self.recipe_id}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data), 1) 
            self.assertEqual(data[0]['comment'], 'Facile e saporita.')
            self.assertEqual(data[0]['rating'], 5)


class View_comments_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            
            db.create_all()
            if not Users.query.filter_by(email='marco@mail.com').first():
                user = Users(username='Marco', email='marco@mail.com', password='Marc1234.')
                db.session.add(user)
                db.session.commit()
            
            # commento di test
            self.recipe_id = 1

            comment = Comments (
                recipe_id = self.recipe_id,
                email = 'marco@mail.com',
                username = 'Marco',
                comment = 'Facile e saporita.',
                rating = 5)
            
            db.session.add(comment)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()  
            db.drop_all()  

    def test_get_comments_view(self):

        response = self.client.get(f'/get-comments/{self.recipe_id}')
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        
        self.assertEqual(len(data), 1)  
        self.assertEqual(data[0]['comment'], 'Facile e saporita.')
        self.assertEqual(data[0]['rating'], 5)
        self.assertEqual(data[0]['email'], 'marco@mail.com')
        self.assertEqual(data[0]['username'], 'Marco')



# ------------------------#


class Integration_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with self.app.app_context():
            db.create_all()

            if not Users.query.filter_by(email='marco@mail.com').first():
                user = Users(username='Marco', email='marco@mail.com', password= 'Marc1234.')
                db.session.add(user)
                db.session.commit()

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

    def test_submit_and_retrieve_comment(self):
        with self.client.session_transaction() as sess:
            sess['id'] = 1

        response = self.client.post('/submit-comment', data = {
            'recipe_id': self.recipe_id,
            'comment': 'Adatta a tutti.',
            'rating': 4
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, f'/ricetta?id={self.recipe_id}')  # reindirizzamento in caso di successo

        with self.app.app_context():
            comment = Comments.query.filter_by(recipe_id = self.recipe_id, email='marco@mail.com').order_by(Comments.comment_id.desc()).first()
            self.assertIsNotNone(comment)
            self.assertEqual(comment.comment, 'Adatta a tutti.')
            self.assertEqual(comment.rating, 4)

        response = self.client.get(f'/get-comments/{self.recipe_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        data = json.loads(response.data)
        self.assertEqual(len(data), 2)  
        self.assertTrue(any(c['comment'] == 'Adatta a tutti.' for c in data))
        self.assertTrue(any(c['rating'] == 4 for c in data))