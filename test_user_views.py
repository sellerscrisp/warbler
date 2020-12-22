"""User routes tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

USER_DATA_1 = {
    'email': 'testuser1@test.com',
    'username': 'testuser1',
    'password': 'HASHED_PASSWORD'
}

USER_DATA_2 = {
    'email': 'testuser2@test.com',
    'username': 'testuser2',
    'password': 'HASHED_PASSWORD2'
}


class UserViewTestCase(TestCase):
    """Testing user routes"""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # self.client = app.test_client()

        user1 = User.signup(**USER_DATA_1, image_url='')
        user2 = User.signup(**USER_DATA_2, image_url='')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

    def test_login(self):
        with app.test_client() as client:
            response = client.post('/login',
                                   data={
                                       'username': USER_DATA_1['username'],
                                       'password': USER_DATA_1['password'],
                                   },
                                   follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'Hello, { USER_DATA_1['username'] }', html)

    def test_logout(self):
        with app.test_client() as client:
            user = User.query.first()
            # Any changes to session should go in here:
            with client.session_transaction() as change_session:
                change_session['curr_user'] = user.id

            response = client.get('/logout', follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('You have been logged out successfully!', html)

    def test_followers_pages_logged_in(self):
        with app.test_client() as client:
            users = User.query.all()
            # Any changes to session should go in here:
            with client.session_transaction() as change_session:
                change_session['curr_user'] = users[0].id

            response = client.get(f'/users/{ users[1].id }/following',
                                  follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'@{ users[1].username }', html)

    def test_following_pages_logged_in(self):
        with app.test_client() as client:
            users = User.query.all()
            # Any changes to session should go in here:
            with client.session_transaction() as change_session:
                change_session['curr_user'] = users[0].id

            response = client.get(f'/users/{ users[1].id }/followers',
                                  follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'@{ users[1].username }', html)

    def test_followers_pages_logged_out(self):
        with app.test_client() as client:
            users = User.query.all()
            response = client.get(f'/users/{ users[1].id }/followers',
                                  follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)

    def test_following_pages_logged_out(self):
        with app.test_client() as client:
            users = User.query.all()
            response = client.get(f'/users/{ users[1].id }/following',
                                  follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)

    def test_post_message_logged_in(self):
        with app.test_client() as client:
            user = User.query.first()
            with client.session_transaction() as change_session:
                change_session['curr_user'] = user.id

            response = client.post('/messages/new',
                                   follow_redirects=True,
                                   data={'text': 'This is a test message.'})
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('This is a test message.', html)

    def test_post_message_logged_out(self):
        with app.test_client() as client:
            response = client.post('/messages/new',
                                   follow_redirects=True,
                                   data={'text': 'This is a test message.'})
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)
