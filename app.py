import os
import pdb
import requests

from flask import Flask, render_template, request, flash, redirect, session, g

from secrets import API_SECRET_KEY


from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, User, Book, Review, BookList, Follows, Rating

from forms import AddUserForm, EditUserForm, LoginForm, SearchForm, AddReviewForm, EditReviewForm

from api_helper import get_all_categories, get_books_by_category


key = API_SECRET_KEY

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.

uri = os.environ.get('DATABASE_URL', 'postgresql:///book_app')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
 

toolbar = DebugToolbarExtension(app)

connect_db(app)

# db.drop_all()
db.create_all()


API_BASE_URL = 'https://api.nytimes.com/svc/books/v3/'



def add_book_to_database(category, title):
    """Check to see if book is already in database. If it is, return the book already in the database. If book not in database, add book to database and then return the book"""  

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    book_results = get_books_by_category(category)
    
    books = [book for book in book_results if book['title']==title]
    book = books[0]

    try:   
        book = Book(
                title = book['title'],
                author = book['author'],
                image = book['image'],
                description = book['description'],
                category = category
            )

        db.session.add(book)
        db.session.commit()
    except IntegrityError:
        flash("Book already in database", "danger")

    return book



##########################################################################

@app.route('/')
def show_home():
    """Render home page including search bar for selecting a category"""

    form = SearchForm()
    categories = get_all_categories()

    form.category.choices = ['Select one'] + [category.title().replace('-', " ") for category in categories]

    return render_template('home.html', form=form, categories=categories)


@app.route('/results', methods=["GET"])
def show_results_from_nyt_api():
    """Handle search form on home page and return results from NYT API"""

    category = request.args.get('category')
    book_results = get_books_by_category(category)

    return render_template('results.html', book_results=book_results, category=category)


@app.route('/results/<category>/books/<book_title>', methods=["GET"])
def show_details_for_book_from_nyt_api(category, book_title):
    """Show details from NYT api for specific book"""

    book_results = get_books_by_category(category)
    
    books = [book for book in book_results if book['title']==book_title]
      
    return render_template('books/book_details.html', books=books, category=category)


@app.route('/results/<category>/books/<book_title>', methods=["POST"])  
def add_new_book_to_list(category, book_title):
    """Check if book is on user booklist. If not, add book to user booklist"""  

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    new_book_for_list = add_book_to_database(category, book_title)

    booklist = BookList.query.filter(BookList.user_id==g.user.id).all()

    curr_books = [book.id for book in booklist]

    if new_book_for_list.id in curr_books:
        flash("This book is already on your list")
        return redirect("f/users/{g.user.id}")

    else:
        new_book_for_list = BookList(
            user_id = g.user.id,
            book_id = new_book_for_list.id
        )

    db.session.add(new_book_for_list)
    db.session.commit()

    flash("Book added to your list", "success")
    return redirect(f"/users/{g.user.id}")



#####################################################################
# User signup, login, logout

@app.before_request
def add_user_to_g():
    """If the user is logged in, add them to Flask global"""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in user"""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user"""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
       

##########################################################################
# USER ROUTES FOR SIGNUP/LOGIN/LOGOUT

@app.route('/signup', methods=["GET", "POST"])
def register():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If there already is a user with that username: flash message
    and re-present form."""

    form = AddUserForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)
        
        do_login(user)

        flash("Signup successful!", 'success')
        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            flash(f"Hello, {user.username}!", "success")
            do_login(user)
            return redirect("/")
        else:
            flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("Logging out, goodbye", "success")
    
    return redirect('/login')


####################################################################
# GENERAL USER ROUTES

@app.route('/users')
def list_users():
    """Page with listing of users.
    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")


    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%".title())).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def show_user_profile(user_id):
    """Show all information on user including books saved and reviews created by user from the database ."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    
    return render_template('users/show.html', user=user)



@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    follow_id = User.query.get_or_404(follow_id)
    g.user.following.append(follow_id)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    follow_id = User.query.get(follow_id)
    g.user.following.remove(follow_id)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def edit_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = g.user
    form = EditUserForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data

            db.session.commit()
            return redirect(f"/users/{user.id}")

        flash("Wrong password, please try again.", 'danger')

    return render_template('users/edit.html', form=form, user_id=user.id)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")
    

@app.route('/users/<int:user_id>/books', methods=["GET"])
def show_user_booklist(user_id):
    """Show list of books for this user"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
   
    return render_template('users/booklist.html', user=user)


@app.route('/users/<int:user_id>/reviews', methods=["GET"])
def show_user_reviews(user_id):
    """Show list of reviews for this user"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter(Review.user_id==user_id).all()
    
   
    return render_template('users/reviews.html', user=user, reviews=reviews)


###########################################################################
# BOOKS ROUTES

@app.route("/books")
def show_all_books():
    """Show list of all books in database"""

    books = Book.query.order_by(Book.title).all()
    return render_template("books/index.html", books=books)


@app.route("/books/<int:book_id>")
def show_book_details(book_id):
    """Display details about a specific book in database including reviews, users and ratings"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = g.user
    book = Book.query.get_or_404(book_id)
    booklists = BookList.query.filter(BookList.book_id==book_id).all()
    reviews = Review.query.filter(Review.book_id==book_id).all()
    rating = Rating.query.filter(Rating.book_id==book_id).all()
   
    # Get average rating of movie
    rating_scores = [rating.score for rating in book.ratings]
    if len(rating_scores) > 0:
        avg_rating = float(sum(rating_scores)) / len(rating_scores)
    else:
        avg_rating = "Not rated yet"

    return render_template('books/book.html', book=book, booklists=booklists, reviews=reviews, user=user, rating=rating, avg_rating=avg_rating)


@app.route('/books/<int:book_id>', methods=["POST"])
def rate_book(book_id):
    """Post rating for individual book"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

   
    new_score = request.form.get("book-rating")
    book = Book.query.get_or_404(book_id)
    user_id = g.user.id

    rating = Rating.query.filter(Rating.user_id==user_id, Rating.book_id==book_id).first()

    if not rating:
        rating = Rating(score=new_score, user_id=user_id, book_id=book_id)

    else: 
        rating.score = new_score

    db.session.add(rating)
    db.session.commit()

    return redirect(f"/books/{book.id}")


############################################################################
# BOOKLISTS ROUTES

@app.route("/booklists")
def show_all_booklists():
    """Show list of all booklists in database"""

    booklists = BookList.query.all()
    users = User.query.all()
    return render_template("booklists/index.html", booklists=booklists, users=users)

    
@app.route('/booklists/<int:user_id>/add/<int:book_id>', methods=["POST"])
def add_saved_book_to_booklist(user_id, book_id):
    """Check if book in database is on user booklist. If not, add book to user booklist"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    new_book_for_list = Book.query.get_or_404(book_id)

    booklist = BookList.query.filter(BookList.user_id==g.user.id).all()

    
    curr_books = [book.id for book in booklist]

    if new_book_for_list.id in curr_books:
        flash("This book is already on your list", "danger")
        return redirect(f"/users/{g.user.id}")

    else:
        new_book_for_list = BookList(
        user_id = g.user.id,
        book_id = new_book_for_list.id
        )

    db.session.add(new_book_for_list)
    db.session.commit()

    flash("Book added to your list", "success")
    return redirect(f"/users/{g.user.id}")
 

@app.route('/booklists/<int:user_id>/delete/<int:book_id>', methods=["POST"])
def remove_book_from_booklist(user_id, book_id):
    """Check if user is owner of booklist then delete book from booklist"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")


    if not g.user.id == user_id:
        flash("Access unauthorized.", "danger")
        return redirect(f"/users/{g.user.id}")
    
    booklist = BookList.query.filter(BookList.user_id==user_id, BookList.book_id==book_id).first()

    user = User.query.get_or_404(user_id)

    db.session.delete(booklist)
    db.session.commit()
    flash("Book deleted from your list", "success")

    return redirect(f"/users/{g.user.id}")

##########################################################################
# REVIEWS ROUTE

@app.route("/books/<book_id>/reviews/add", methods=["GET", "POST"])
def add_review(book_id):
    """Display and handle form submission for adding a review for a specific book"""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")

    user = g.user
    book = Book.query.get_or_404(book_id)
    
    reviews = Review.query.filter(Review.user_id==g.user.id).all()

    user_reviews = [review.user_id for review in book.reviews]

    if user.id in user_reviews:
        flash("You have already submitted a review for this book!", "danger")
        return redirect(f"/books/{book.id}")


    form = AddReviewForm()

    if form.validate_on_submit():
        summary = form.summary.data
        url = form.url.data

        new_review = Review(summary=summary, url=url, user_id=g.user.id, book_id=book.id)

        db.session.add(new_review)
        db.session.commit()

        flash ("Review created successfully", "success")
        return redirect(f"/users/{g.user.id}")

    return render_template('reviews/new.html', form=form, book=book, user=user, reviews=reviews)



@app.route('/reviews/<review_id>/edit', methods=["GET", "POST"])
def edit_review(review_id):
    """Edit review if user created review."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")


    review = Review.query.get_or_404(review_id)

    if review.user_id != g.user.id:
        flash("Access unauthorized", "danger")
        return redirect(f"/users/{g.user.id}")
    

    form = EditReviewForm(obj=review)

    if form.validate_on_submit():
        review.summary = form.summary.data
        review.url = form.url.data

        db.session.commit()
        flash("Review updated", "success")
        return redirect(f"/users/{g.user.id}")    

    return render_template('reviews/edit.html', form=form, review=review)



@app.route('/reviews/<review_id>/delete', methods=["POST"])
def delete_review(review_id):
    """Delete review if user created review."""

    if not g.user:
        flash("Please signup and/or login.", "danger")
        return redirect("/")


    review = Review.query.get_or_404(review_id)

    if  g.user.id != review.user_id:
        flash("Access unauthorized", "danger")
        return redirect(f"/users/{g.user.id}")
    
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted", "success")
    
    return redirect(f"/users/{g.user.id}")    

 ##########################################################################
 

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404

