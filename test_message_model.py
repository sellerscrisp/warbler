""" Message model tests."""

# run these tests like:
#
#  FLASK_ENV=production python -m unittest test_message_model.py


from app import app, InvalidRequestError, IntegrityError
import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u = User(
            email='test@test.com',
            username='testuser',
            password='HASHED_PASSWORD'
        )

        db.session.add(u)
        db.session.commit()

        msg = Message(
            text='Some random text',
        )

        u.messages.append(msg)

        db.session.commit()

        self.u = u
        self.msg = msg

        # Put user id and msg id on self

        self.client = app.test_client()

    def tearDown(self):
        """ Clean up test database """

        db.session.rollback()

    def test_msg_repr(self):
        """ Test that the message is being represented correctly """

        self.assertEqual(
            repr(self.msg), f'<Message #{self.msg.id} @{self.msg.timestamp}>')

    def test_msg_relationship(self):
        """ Test that the relationship between message and user is
            correctly established
        """

        self.assertEqual(self.u, self.msg.user)
        self.assertEqual(len(self.u.messages), 1)

        msg2 = Message(
            text='Some random text again',
        )

        self.u.messages.append(msg2)
        db.session.commit()

        # Can you test that self.u.messages is a list containing self.msg and msg2?
        self.assertEqual(len(self.u.messages), 2)
        self.assertIn(self.msg, self.u.messages)
        self.assertIn(msg2, self.u.messages)
