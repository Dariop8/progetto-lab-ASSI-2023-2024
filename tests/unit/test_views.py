import sys
import os
from flask import json
from flask_testing import TestCase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import app, db, Comments, Users  

class View_test(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()

            if not Users.query.filter_by(email='marco@mail.com').first():
                user = Users(username='Marco', email='marco@mail.com', password='marc1234')
                db.session.add(user)
                db.session.commit()
            
            # commento di test
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