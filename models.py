"""SQLAlchemy models for BookApp"""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

bcrypt = Bcrypt()

db = SQLAlchemy()


class Follow(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )


class BookList(db.Model):
    """Mapping user to book"""

    __tablename__ = 'booklists'


    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String,
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
        
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey('books.id', ondelete='cascade')
    )

    rating = db.Column(
        db.Integer, 
        nullable=True
    )


    def __repr__(self):
        return f"<BookList {self.id} {self.user_id} {self.book_id}>"

    


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    password = db.Column(
        db.Text,
        nullable=False
    )

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follow.user_being_followed_id == id),
        secondaryjoin=(Follow.user_following_id == id)
    )

    following = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follow.user_following_id == id),
        secondaryjoin=(Follow.user_being_followed_id == id)
    )
   
    booklist = db.relationship('Book', secondary='booklists', backref='users')


    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_user`?"""

        found_user_list = [user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.
        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        try: 
            user = User(
                username=username,
                email=email,
                password=hashed_pwd
            )
            db.session.add(user)
            db.session.commit()
        except exc.IntegrityError:
            user = None
            db.session.rollback()

        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.
        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.
        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Book(db.Model):
    """An individual book."""

    __tablename__ = 'books'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    title = db.Column(
        db.String,
        nullable=False,
        unique=True
    )  

    publication_dt = db.Column(
        db.Date,
        nullable = True
    )

    description = db.Column(
        db.Text,
        nullable = False
    )

    author = db.Column(
        db.String,
        nullable = False,
    )

    category = db.Column(
        db.String,
        nullable = True
    )

    avg_rating = db.Column(
        db.Float,
        nullable = True
    )

    num_of_ratings = db.Column(
      db.Integer,
      nullable = True
    )

    num_of_reviews = db.Column(
      db.Integer,
      nullable = True
    )

    
    



    def __repr__(self):
        return f"<Book {self.id} {self.title} {self.author} {self.description}>"



class Review(db.Model):
    """An individual review"""

    __tablename__ = 'reviews'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable = True
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey('books.id', ondelete='cascade'),
        nullable = False,
    )

    url = db.Column(
        db.String,
        nullable = True
    )

    summary = db.Column(
        db.Text,
        nullable = False
    )

    def __repr__(self):
        return f"<Category {self.id} {self.summary}>"


class Category(db.Model):
    """An individual category"""

    __tablename__ = 'categories'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    category_name = db.Column(
        db.String,
        nullable = False
    )
    
    def __repr__(self):
        return f"<Category {self.id} {self.category_name}>"


class Author(db.Model):
    """An individual author"""

    __tablename__ = 'authors'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    author_name = db.Column(
        db.String,
        nullable = False
    )

    race = db.Column(
        db.String,
        nullable = True,
    )

    gender = db.Column(
        db.String,
        nullable = True,
    )

    def __repr__(self):
        return f"<Author {self.id} {self.author_name}>"



def connect_db(app):
    """Connect this database to provided Flask app.
    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)


