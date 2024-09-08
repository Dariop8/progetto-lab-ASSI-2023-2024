import sys
import os
from flask import json
from flask_testing import TestCase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import app, db, Comments, Users  

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

            user = Users(username='Marco', email='marco@mail.com', password='marc1234')
            db.session.add(user)
            db.session.commit()
            self.recipe_id = 1

    def tearDown(self):
        with app.app_context():
            db.session.remove()  
            db.drop_all()  

    def test_submit_comment(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['id'] = 1
            response = c.post('/submit-comment', data = {
                'recipe_id': self.recipe_id,
                'comment': 'Facile e saporita.',
                'rating': 5})
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, f'/ricetta?id={self.recipe_id}') # reindirizzamento in caso di successo

            comment = Comments.query.filter_by(recipe_id=self.recipe_id, email='marco@mail.com').first() # verifica aggiunta
            self.assertIsNotNone(comment)
            self.assertEqual(comment.comment, 'Facile e saporita.')

    def test_get_comments(self):
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