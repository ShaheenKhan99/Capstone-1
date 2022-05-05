import os
import pdb
import requests

from flask import Flask, render_template, request, flash, redirect, session, g, abort, jsonify

from secrets import API_SECRET_KEY


from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, User, Book, Review, Author, BookList, Follow

from forms import AddUserForm, EditUserForm, LoginForm, SearchForm

key = API_SECRET_KEY

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///book_app'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


# db.drop_all()
db.create_all()


API_BASE_URL = 'https://api.nytimes.com/svc/books/v3/'


def get_all_categories():
    """Return all categories from API"""

    res = requests.get(f"{API_BASE_URL}lists/names.json?api-key={key}")

    data = res.json()
    results = data["results"]
    
    categories = [result['list_name_encoded'] for result in results]
    categories = list(dict.fromkeys(categories))
    return categories


def get_book_by_author(author):
    """Return all titles by author from API"""

    res = requests.get(f"{API_BASE_URL}reviews.json?api-key={key}",
                params={'author': author})

    data = res.json()
    results = data["results"]

    return results


def get_books_by_category(category):
    """Return all bestselling titles for specific category from API"""

    res = requests.get(f"{API_BASE_URL}lists/current/{category}.json?api-key={key}")

    data = res.json()
    results = data["results"]
    books = results["books"]

    book_results = []
    for book in books:
        book = {
            "book_title": book["title"],
            "book_author": book["author"],
            "book_image" : book["book_image"]
        }
        book_results.append(book)
    return book_results


def get_book_by_title_author(title, author):
    """Return book with specific title and author from API"""

    res = requests.get(f"{API_BASE_URL}lists/best-sellers/history.json?api-key={key}",
                params={'title': title, 'author': author})

    data = res.json()
    results = data["results"]

    return results


def add_book_to_database(title, author):
    """Add book to database"""  

    results = get_book_by_title_author(title, author)
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    book = results[0]

    try:    
        new_book = Book(
                title = book['title'],
                author = book['author'],
                description = book['description']
        )

        db.session.add(new_book)
        db.session.commit()
    except IntegrityError:
        new_book = new_book

    return new_book


##########################################################################

@app.route('/')
def show_home():
    """Render home page"""

    form = SearchForm()
    categories = get_all_categories()

    form.category.choices = ['select one'] + [category for category in categories]

    return render_template('home.html', form=form, categories=categories)


@app.route('/results', methods=["GET"])
def show_results_from_api():
    """Handle search and return results"""

    category = request.args.get('category')
    
    results = get_books_by_category(category)

    return render_template('results.html', results=results, category=category)


@app.route('/books/<title>/author/<author>', methods=["GET"])  
def show_book_info_from_api(title, author):
    """Show book details"""  

    results = get_book_by_title_author(title, author)
    if len(results) > 1:
        results = results[0]
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")


    return render_template('books/book_details.html', results=results)



@app.route('/books/<title>/author/<author>', methods=["POST"])  
def add_book_to_list(title, author):
    """Check if book is on user booklist. If not, dd book to user booklist"""  

    new_book_for_list = add_book_to_database(title, author)

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

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def show_user_profile(user_id):
    """Show all information on user including books saved and reviews created by user from the database ."""

    user = User.query.get_or_404(user_id)
    
    return render_template('users/show.html', user=user)



@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    follow_id = User.query.get_or_404(follow_id)
    g.user.following.append(follow_id)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    follow_id = User.query.get(follow_id)
    g.user.following.remove(follow_id)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def edit_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
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
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")
    

@app.route('/users/<int:user_id>/books', methods=["GET"])
def show_user_booklist(user_id):
    """Show list of books for this user"""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
   
    return render_template('users/booklist.html', user=user)


###########################################################################
# BOOKS ROUTES

@app.route("/books")
def show_all_books():
    """Show list of all books in database"""

    books = Book.query.all()
    return render_template("books/index.html", books=books)


@app.route("/books/<int:book_id>")
def show_book_details(book_id):
    """return details about a specific book in database"""

    book = Book.query.get_or_404(book_id)
    booklists = BookList.query.filter(BookList.book_id==book_id).all()
    reviews = Review.query.filter(Review.book_id==book_id).all()
   

    return render_template('books/book.html', book=book, booklists=booklists, reviews=reviews)


############################################################################
# BOOKLISTS ROUTES

@app.route("/booklists")
def show_all_booklists():
    """Show list of all booklists in database"""

    booklists = BookList.query.all()
    users = User.query.all()
    return render_template("booklists/index.html", booklists=booklists, users=users)


# Need to implement this route   
@app.route('/booklists/<int:booklist_id>/add/<int:book_id>', methods=["POST"])
def add_book_to_booklist(booklist_id, book_id):
    """Check if user is creator of booklist then add book to booklist"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    book = Book.query.get_or_404(book_id)
    booklist = BookList.query.get_or_404(booklist.book_id)

    if not g.user.id == booklist.user_id:
        flash("Access unauthorized.", "danger")
        return redirect("f/users/{g.user.id}")

    for book in booklist.book_ids:
        if book_id == book.id:
            flash('Book already on this list', 'danger')
            return redirect("f/users/{g.user.id}")
    
    new_book_for_booklist = BookList(
            user_id = g.user.id,
            book_id = book_id)
    db.session.commit()

    return redirect("f/users/{g.user.id}")



@app.route('/booklists/<int:user_id>/delete/<int:book_id>', methods=["POST"])
def remove_book_from_booklist(user_id, book_id):
    """Check if user is creator of booklist then delete book from booklist"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    booklists = BookList.query.filter(BookList.book_id == book_id, BookList.user_id == user_id).all()

    if not g.user.id == user_id:
        flash("Access unauthorized.", "danger")
        return redirect("f/users/{g.user.id}")
    
    for booklist in booklists:
        db.session.delete(booklist)
    db.session.commit()

    flash("Book deleted from your list", "success")

    return redirect("f/users/{g.user.id}")


    
    

