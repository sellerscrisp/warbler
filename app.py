import os

from flask import Flask, render_template, request, flash, redirect, session, g, abort, jsonify, url_for

from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm, DeleteOrLogoutForm
from models import db, connect_db, User, Message

from functools import wraps

CURR_USER_KEY = 'curr_user'

app = Flask(__name__)


# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler2'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ohs0secr3t')
toolbar = DebugToolbarExtension(app)

connect_db(app)

##############################################################################
# Custom 404 route


@app.errorhandler(404)
def show_custom_404_page(error):
    """Error 404."""

    return render_template('404.html')

##############################################################################
# User signup/login/logout


def login_required(f):
    """Require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash('Access unauthorized.', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
        g.delete_or_logout_form = DeleteOrLogoutForm()
        g.message_form = MessageForm()

    else:
        g.user = None
        g.delete_or_logout_form = None
        g.message_form = MessageForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as err:

            db.session.rollback()

            # TODO: Consider refactoring to helper, this code is used in edit user profile route
            searched_username_user = User.query.filter_by(
                username=form.username.data).first()
            if searched_username_user and searched_username_user is not g.user:
                form.username.errors = ['Username is taken.']

            searched_email_user = User.query.filter_by(
                email=form.email.data).first()
            if searched_email_user and searched_email_user is not g.user:
                form.email.errors = ['Email is taken.']

            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect('/')

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f'Hello, {user.username}!', 'success')
            return redirect('/')

        flash('Bad login.', 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle logout of user."""

    form = g.delete_or_logout_form

    if form.validate_on_submit():

        do_logout()

        flash('Successfully Logged Out', 'success')

        return redirect('/')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f'%{search}%')).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    if g.user:
        liked_message_ids = {msg.id for msg in g.user.liked_messages}
        return render_template('users/show.html', user=user, liked_message_ids=liked_message_ids)

    return render_template('users/show.html', user=user)


@app.route('/users/<int:user_id>/following')
@login_required
def show_user_following(user_id):
    """Show list of people this user is following."""

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
@login_required
def show_user_followers(user_id):
    """Show list of followers of this user."""

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
@login_required
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if g.user.id == follow_id:
        flash('You cannot follow yourself.', 'danger')
        return redirect(request.referrer)

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    flash(f'Successfully followed user: {followed_user.username}', 'success')

    return redirect(request.referrer)


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
@login_required
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if g.user.id == follow_id:
        flash('You cannot unfollow yourself.', 'danger')
        return redirect(request.referrer)

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    flash(f'Successfully unfollowed user: {followed_user.username}', 'success')

    return redirect(request.referrer)


@app.route('/users/<int:user_id>/likes')
@login_required
def show_user_likes(user_id):
    """ Show a detail page of current logged in user's liked messages """

    liked_message_ids = {msg.id for msg in g.user.liked_messages}
    return render_template('users/likes.html', user=g.user, liked_message_ids=liked_message_ids)


@app.route('/users/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Update profile for current user.

    When username or email taken, renders template again with errors shown.
    When password incorrect, also show errors on re -rendered template 
    Otherwise, successfully edits user profile and redirects to user detail page
    """

    form = UserEditForm(obj=g.user)

    searched_username_user = User.query.filter_by(
        username=form.username.data).first()
    if searched_username_user and searched_username_user is not g.user:
        form.username.errors = ['Username is taken.']

    searched_email_user = User.query.filter_by(email=form.email.data).first()
    if searched_email_user and searched_email_user is not g.user:
        form.email.errors = ['Email is taken.']

    if form.email.errors or form.username.errors:
        form.password.data = None
        return render_template('users/edit.html', form=form)

    if form.validate_on_submit():
        if not User.authenticate(
                username=g.user.username,
                password=form.password.data):
            form.password.data = None
            form.password.errors = ['Password is incorrect.']
            return render_template('users/edit.html', form=form)

        form.password.data = g.user.password
        form.populate_obj(g.user)
        db.session.commit()

        flash(f'Successfully updated: {g.user.username}', 'success')
        return redirect(url_for('show_user', user_id=g.user.id))
    else:
        form.password.data = None
        return render_template('users/edit.html', form=form)


@app.route('/users/delete', methods=['POST'])
@login_required
def delete_user():
    """Delete user."""

    delete_user_form = g.delete_or_logout_form

    if delete_user_form.validate_on_submit():

        do_logout()

        db.session.delete(g.user)
        db.session.commit()

        flash('User has been deleted successfully', 'success')

        return redirect(url_for('signup'))


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=['GET', 'POST'])
@login_required
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(url_for('show_user', user_id=g.user.id))

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=['GET'])
@login_required
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get_or_404(message_id)
    liked_message_ids = {message.id for message in g.user.liked_messages}
    return render_template('messages/show.html', message=msg, liked_message_ids=liked_message_ids)


@app.route('/messages/<int:message_id>/like', methods=['POST'])
@login_required
def messages_like(message_id):
    """ Like the message if user logged in and message not written by user """

    form = g.delete_or_logout_form

    if form.validate_on_submit():

        msg = Message.query.get_or_404(message_id)
        g.user.liked_messages.append(msg)

        db.session.commit()

        flash('Successfully liked message!', 'success')
        # Be careful with referrer, it can be spoofed, may be better to redirect to a route
        return redirect(request.referrer)


@app.route('/messages/<int:message_id>/unlike', methods=['POST'])
@login_required
def messages_unlike(message_id):
    """ Unlike the message if user logged in and message not written by user """

    form = g.delete_or_logout_form

    if form.validate_on_submit():

        msg = Message.query.get_or_404(message_id)
        g.user.liked_messages.remove(msg)

        db.session.commit()

        flash('Successfully unliked message!', 'success')
        return redirect(request.referrer)


@app.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def messages_destroy(message_id):
    """Delete a message."""

    # Check that the message was written by you so that you can delete
    form = g.delete_or_logout_form

    if form.validate_on_submit():

        msg = Message.query.get_or_404(message_id)
        if msg.user_id != g.user.id:
            abort(401)

        db.session.delete(msg)
        db.session.commit()

        return redirect(url_for('show_user', user_id=g.user.id))


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        following_ids = [user.id for user in g.user.following] + [g.user.id]

        messages = (Message
                    .query
                    .filter((Message.user_id.in_(following_ids)))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        liked_message_ids = {msg.id for msg in g.user.liked_messages}
        return render_template('home.html', messages=messages, liked_message_ids=liked_message_ids)

    else:
        return render_template('home-anon.html')


##############################################################################
# API Routes for Likes

@app.route('/api/messages/<int:message_id>/toggle_like', methods=['POST'])
def messages_like_api(message_id):
    """ Like the message through AJAX if user logged in and message not
        written by user """

    # This one does not use login decorator because of custom API json message
    if not g.user:
        message = 'Access Unauthorized.'
        return (jsonify(message=message), 401)

    msg = Message.query.get(message_id)

    is_liked = msg in g.user.liked_messages

    if msg:

        if is_liked:
            g.user.liked_messages.remove(msg)
            message = 'Successfully unliked!'
        else:
            g.user.liked_messages.append(msg)
            message = 'Successfully liked!'

        db.session.commit()
    else:
        message = 'There is no message'

    return jsonify(message=message)


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
