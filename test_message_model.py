"""Testing message model """
# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy.exc import InvalidRequestError, IntegrityError
from psycopg2.errors import UniqueViolation
from models import db, User, Message, Follows, Likes

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

MESSAGE_DATA_1 = {"text": "hi", "user_id": None}

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


class MessageModelTestcase(TestCase):
    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()
        user1 = User(**USER_DATA_1)
        user2 = User(**USER_DATA_2)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

    def test_adding_message(self):
        """Testing if a message is being added to the database"""
        user = User.query.first()
        message = Message(text='hi', user_id=user.id)
        db.session.add(message)
        db.session.commit()
        count = Message.query.count()
        self.assertEqual(count, 1)

    def test_like_message(self):
        users = User.query.all()
        message = Message(text='hi', user_id=users[0].id)
        db.session.add(message)
        db.session.commit()
        like = Likes(user_id=users[1].id, message_id=message.id)
        db.session.add(like)
        db.session.commit()

        count = Likes.query.count()
        self.assertEqual(count, 1)

   

