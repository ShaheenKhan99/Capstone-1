"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Follows, Book, BookList, Rating, Review

# Set an environmental variable to use a different database for tests 

os.environ['DATABASE_URL'] = "postgresql:///book_app-test"


from app import app

# Create tables here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Disable WTForms use of CSRF during testing.
app.config['WTF_CSRF_ENABLED'] = False

class UserModelTestCase(TestCase):
    """Test user model"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup(
            "test1", 
            "email1@email.com", 
            "password"
            )

        userid1 = 1111
        user1.id = userid1

        user2 = User.signup(
            "test2", 
            "email2@email.com", 
            "password"
            )

        userid2 = 2222
        user2.id = userid2

        db.session.commit()

        u1 = User.query.get(userid1)
        u2 = User.query.get(userid2)

        self.u1 = u1
        self.uid1 = userid1

        self.u2 = u2
        self.uid2 = userid2

        self.client = app.test_client()


    def tearDown(self):
        """Rollback any failed transactions """
        
        res = super().tearDown()
        db.session.rollback()
        return res  

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD"
        )
         
        db.session.add(u)
        db.session.commit()

        # User should have no followers, booklist, reviews or ratings
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.booklist), 0)
        self.assertEqual(len(u.reviews), 0)
        self.assertEqual(len(u.ratings), 0)

    def test_repr(self):
        """Test the string representation of the User instance"""

        self.assertEqual(f"{self.u1}", f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>")

    #### Following tests ############################################

    def test_user_follows(self):
        """Is the number of users following is correct?"""
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)


    def test_is_following(self):
        """ Does is_following detect if user1 is following user2"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        """Does is_follewed detect if user2 is followed by user1"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    #### Signup tests ########################################

    def test_valid_signup(self):
        """ Does signup successfully create a new user with given valid credentials"""

        u_test = User.signup("tester", "testing@test.com", "password")
        uid = 99999
        u_test.id = uid
        db.session.commit()

        u_test = User.query.get(uid)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "tester")
        self.assertEqual(u_test.email, "testing@test.com")
        self.assertNotEqual(u_test.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))


    def test_invalid_username_signup(self):
        """Test when there is no/invalid username at signup"""

        with self.assertRaises(TypeError):
            User.signup()
            db.session.commit()


    def test_invalid_email_signup(self):
        """ Test when there is no/invalid email at signup"""

        with self.assertRaises(TypeError):
            User.signup()
            db.session.commit()


    def test_invalid_password_signup(self):
        """ Test when there is no/invalid password at signup"""

        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", "")
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None)


############ Authentication testing ######################

    def test_valid_authentication(self):
        """Test if authentication returns a valid user when given valid name and password"""

        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        """Test for authentication when username is invalid"""

        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        """Test for authentication when password is invalid"""
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
    


    