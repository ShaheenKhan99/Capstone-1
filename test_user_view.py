"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_view.py


import os
from unittest import TestCase

from models import db, User, Follows, Book, BookList, Rating, Review
from bs4 import BeautifulSoup

# Set an environmental variable to use a different database for tests 

os.environ['DATABASE_URL'] = "postgresql:///book_app-test"


from app import app, CURR_USER_KEY

# Disable WTForms use of CSRF during testing.
app.config['WTF_CSRF_ENABLED'] = False

# Drop all tables and create new tables for each test
db.drop_all()
db.create_all()


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Book.query.delete()
        BookList.query.delete()
        Review.query.delete()
        Follows.query.delete()
        Rating.query.delete()

        self.testuser = User.signup(username="testuser", email="email1@email.com", password="password1")
        
        self.testuser_id = 1234
        self.testuser.id = self.testuser_id
        
        # self.testuser_id = self.testuser.id

        self.u1 = User.signup("abc", "test1@test.com", "password")
        self.u1_id = 456
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password")
        self.u2_id = 789
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password")
        self.u4 = User.signup("testing", "test4@test.com", "password")


        # db.session.add(self.testuser)
        db.session.commit()

        self.client = app.test_client()

        book = Book(title="TestBook", description="TestDescription", author="TestAuthor")

        self.book_id = book.id

        db.session.add(book)
        db.session.commit()


        booklist = BookList(user_id=1234, book_id=self.book_id)
        
        db.session.add(booklist)
        db.session.commit()

        self.booklist_id = booklist.id

        
    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp


    def test_homepage(self):
        """Test if home page is displayed """

        with self.client as c:
            resp = c.get("/")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h3>Looking  for a bestseller?</h3>", str(resp.data))

    def test_signup_page(self):
        """Test if signup page is displayed"""

        with self.client as c:
            resp = c.get("/signup")

        self.assertEqual(resp.status_code, 200) 
        self.assertIn("Register", str(resp.data))   


    def test_books_index(self):
        """Test if all books are displayed"""

        with self.client as c:
            resp = c.get("/books")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Testbook', str(resp.data))

    
    def test_booklists_index(self):
        """Test if  booklist is displayed"""

        with self.client as c:
            resp = c.get("/booklists")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('All Booklists', str(resp.data))        


    def test_users_index(self):
        """Test if list of users is displayed """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get("/users")
            
            self.assertEqual(resp.status_code, 200) 
            self.assertIn("testuser", str(resp.data))


    def test_user_search(self):
        """Test if search returns correct results for user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.get("/users?q=test")

            self.assertIn("testuser", str(resp.data))         
            self.assertNotIn("abc", str(resp.data))
            self.assertNotIn("efg", str(resp.data))
            self.assertNotIn("hij", str(resp.data))


    def test_user_show_page(self):
        """Test if user details are displayed for specific user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id
            resp = c.get(f"/users/{self.testuser_id}")
            
            self.assertEqual(resp.status_code, 200)

            self.assertIn('<h4 class="text-left mt-4" id="username-heading">Username: testuser</h4>', str(resp.data))
            self.assertIn("testuser", str(resp.data))

    
    def setup_followers(self):
        """Set up followers"""

        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()


    def test_user_show_with_follows(self):
        """Test number of followers for a user"""

        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 books
            self.assertIn("0", found[0].text)

            # Test for a count of 0 reviews
            self.assertIn("0", found[1].text)

            # Test for a count of 2 following
            self.assertIn("2", found[2].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[3].text)


    def test_show_following(self):
        """Test number of people user is following"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("abc", str(resp.data))
            self.assertIn("efg", str(resp.data))
            self.assertNotIn("hij", str(resp.data))
            self.assertNotIn("testing", str(resp.data))


    def test_show_followers(self):
        """ Verify followers for a specific user"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("abc", str(resp.data))
            self.assertNotIn("efg", str(resp.data))
            self.assertNotIn("hij", str(resp.data))
            self.assertNotIn("testing", str(resp.data))


    def test_unauthorized_following_page_access(self):
        """Test if unauthorized user trying to access following page"""
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("abc", str(resp.data))
            self.assertIn("Please signup and/or login.", str(resp.data))


    def test_unauthorized_followers_page_access(self):
        """Test if unauthorized user trying to access followers page"""
        
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("abc", str(resp.data))
            self.assertIn("Please signup and/or login.", str(resp.data))


        