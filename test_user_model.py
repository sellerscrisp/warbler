"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy.exc import InvalidRequestError, IntegrityError
from psycopg2.errors import UniqueViolation
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

USER_DATA_1 = {
    'email': "testuser1@test.com",
    'username': "testuser1",
    'password': "HASHED_PASSWORD"
}

USER_DATA_2 = {
    'email': "testuser2@@test.com",
    'username': "testuser2",
    'password': "HASHED_PASSWORD"
}


class UserModelTestCase(TestCase):
    """Test views for messages."""
    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        user1 = User.signup(**USER_DATA_1, image_url="")
        db.session.add(user1)
        user2 = User.signup(**USER_DATA_2, image_url="")
        db.session.add(user2)
        db.session.commit()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(email="test@test.com",
                 username="testuser",
                 password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr_method(self):
        """Test __repr__ mehthod"""

        u = User.query.first()

        self.assertEqual(u.__repr__(),
                         f"<User #{u.id}: {u.username}, {u.email}>")

    def test_is_following(self):
        """Test is_following method"""

        users = User.query.all()
        follow = Follows(user_being_followed_id=users[0].id,
                         user_following_id=users[1].id)
        db.session.add(follow)
        db.session.commit()

        self.assertTrue(users[1].is_following(users[0]))
        self.assertFalse(users[0].is_following(users[1]))

    def test_is_followed_by(self):
        """Test is_followed_by method"""

        users = User.query.all()
        follow = Follows(user_being_followed_id=users[0].id,
                         user_following_id=users[1].id)
        db.session.add(follow)
        db.session.commit()

        self.assertTrue(users[0].is_followed_by(users[1]))
        self.assertFalse(users[1].is_followed_by(users[0]))

    def test_signup(self):
        """Test if new user is successfully created."""

        user_data = {
            "email": "testuser3@test.com",
            "username": "testuser3",
            "password": "HASHED_PASSWORD",
            "image_url": "/static/images/default-pic.png"
        }
        user = User.signup(**user_data)
        db.session.commit()

        count = User.query.filter(
            User.username == user_data["username"]).count()
        self.assertEqual(count, 1)

    def test_signup_fail(self):
        """Test if user signup fails with invalid credentials."""

        with self.assertRaises(IntegrityError) as cm:
            user = User.signup(**USER_DATA_1, image_url="")
            db.session.commit()
        db.session.rollback()
        count = User.query.filter(
                User.username == USER_DATA_1["username"]).count()
        self.assertEqual(count, 1)

    def test_return_user(self):
        """Testing if user authenticate returns correct user"""
        user = User.query.first()
        user_test = User.authenticate('testuser1', 'HASHED_PASSWORD')
        self.assertEqual(user, user_test)

    def test_authentification_fail(self):
        user = User.query.first()
        user_test = User.authenticate('testuser2', 'HASHED_PASSWORD')
        self.assertNotEqual(user, user_test)

    def test_password_fail(self):
        user = User.query.first()
        user_test = User.authenticate('testuser1', 'HASHED_ORD')
        self.assertNotEqual(user, user_test)
