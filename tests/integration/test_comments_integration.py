import sys
import os
from flask import json
from flask_testing import TestCase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import app, db, Comments, Users

class Integration_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with self.app.app_context():
            db.create_all()

            if not Users.query.filter_by(email='marco@mail.com').first():
                user = Users(username='Marco', email='marco@mail.com', password='marc1234')
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
            comment = Comments.query.filter_by(recipe_id=self.recipe_id, email='marco@mail.com').order_by(Comments.comment_id.desc()).first()
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
