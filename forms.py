from flask_wtf import FlaskForm, Form
from models import User, db
from wtforms import StringField, IntegerField, SelectField, TextAreaField, BooleanField, PasswordField, FieldList, FormField, RadioField, URLField

from wtforms.validators import InputRequired, Length, NumberRange, URL, Optional, Email, DataRequired


class AddUserForm(FlaskForm):
    """Form for registering new user"""

    username = StringField("Username", validators=[DataRequired(), Length(max=40)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])


class EditUserForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired(), Length(max=40)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])


class LoginForm(FlaskForm):
    """User login form"""

    username = StringField("Username: ", validators=[DataRequired(), Length(max=30)])
    password = PasswordField("Password: ", validators=[DataRequired()])

##########################################################################

# to be implemented later
class CreateBookListForm(FlaskForm):
    """Form for creating playlist"""

    name = StringField("Name Your Booklist", validators=[InputRequired()])



class SearchForm(FlaskForm):
    """Form for searching NYT API"""

    category = SelectField("Search By Category", validators=[InputRequired()])


class AddReviewForm(FlaskForm):
    """Form for creating review for book in database"""

    summary = TextAreaField("Summary", validators=[DataRequired()])
    url = URLField("URL")


class EditReviewForm(FlaskForm):
    """Form for editing review for book in database"""

    summary = TextAreaField("Summary", validators=[DataRequired()])
    url = URLField("URL")


   
