"""
Routes and views for the Flask application.
"""

from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid


imageSourceUrl = (
    "https://"
    + app.config["BLOB_ACCOUNT"]
    + ".blob.core.windows.net/"
    + app.config["BLOB_CONTAINER"]
    + "/"
)


def _redirect_uri():
    """
    Return the Microsoft authentication callback URL.

    HTTPS is forced because Azure App Service terminates TLS before
    forwarding the request to Flask.
    """
    return url_for(
        "authorized",
        _external=True,
        _scheme="https"
    )


@app.route("/")
@app.route("/home")
@login_required
def home():
    User.query.filter_by(
        username=current_user.username
    ).first_or_404()

    posts = Post.query.all()

    return render_template(
        "index.html",
        title="Home Page",
        posts=posts
    )


@app.route("/new_post", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm(request.form)

    if form.validate_on_submit():
        post = Post()

        post.save_changes(
            form,
            request.files["image_path"],
            current_user.id,
            new=True
        )

        return redirect(url_for("home"))

    return render_template(
        "post.html",
        title="Create Post",
        imageSource=imageSourceUrl,
        form=form
    )


@app.route("/post/<int:id>", methods=["GET", "POST"])
@login_required
def post(id):
    post_record = Post.query.get(int(id))

    form = PostForm(
        formdata=request.form,
        obj=post_record
    )

    if form.validate_on_submit():
        post_record.save_changes(
            form,
            request.files["image_path"],
            current_user.id
        )

        return redirect(url_for("home"))

    return render_template(
        "post.html",
        title="Edit Post",
        imageSource=imageSourceUrl,
        form=form
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data
        ).first()

        if user is None or not user.check_password(form.password.data):
            app.logger.warning(
                "Invalid login attempt for username: %s",
                form.username.data
            )

            flash("Invalid username or password")
            return redirect(url_for("login"))

        login_user(
            user,
            remember=form.remember_me.data
        )

        app.logger.info(
            "%s logged in successfully",
            user.username
        )

        next_page = request.args.get("next")

        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")

        return redirect(next_page)

    session["state"] = str(uuid.uuid4())

    auth_url = _build_auth_url(
        scopes=Config.SCOPE,
        state=session["state"]
    )

    return render_template(
        "login.html",
        title="Sign In",
        form=form,
        auth_url=auth_url
    )


@app.route(Config.REDIRECT_PATH)
def authorized():
    if request.args.get("state") != session.get("state"):
        app.logger.warning(
            "Microsoft authentication state validation failed"
        )

        return redirect(url_for("login"))

    if "error" in request.args:
        app.logger.error(
            "Microsoft authentication error: %s",
            request.args.get("error_description", request.args.get("error"))
        )

        return render_template(
            "auth_error.html",
            result=request.args
        )

    if not request.args.get("code"):
        app.logger.warning(
            "Microsoft authentication callback did not contain a code"
        )

        return redirect(url_for("login"))

    cache = _load_cache()
    redirect_uri = _redirect_uri()

    app.logger.info(
        "Microsoft token redirect URI: %s",
        redirect_uri
    )

    result = _build_msal_app(
        cache=cache
    ).acquire_token_by_authorization_code(
        request.args["code"],
        scopes=Config.SCOPE,
        redirect_uri=redirect_uri
    )

    if "error" in result:
        app.logger.error(
            "Microsoft token acquisition error: %s",
            result.get("error_description", result.get("error"))
        )

        return render_template(
            "auth_error.html",
            result=result
        )

    session["user"] = result.get("id_token_claims")

    user = User.query.filter_by(
        username="admin"
    ).first()

    if user is None:
        app.logger.error(
            "Microsoft authentication succeeded, but local admin user was not found"
        )

        flash("The local admin user could not be found.")
        return redirect(url_for("login"))

    login_user(user)
    _save_cache(cache)

    app.logger.info(
        "%s logged in successfully via Microsoft",
        user.username
    )

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    used_microsoft_login = session.get("user") is not None

    logout_user()

    if used_microsoft_login:
        session.clear()

        post_logout_redirect_uri = url_for(
            "login",
            _external=True,
            _scheme="https"
        )

        return redirect(
            Config.AUTHORITY
            + "/oauth2/v2.0/logout"
            + "?post_logout_redirect_uri="
            + post_logout_redirect_uri
        )

    return redirect(url_for("login"))


def _load_cache():
    cache = msal.SerializableTokenCache()

    if session.get("token_cache"):
        cache.deserialize(
            session["token_cache"]
        )

    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        Config.CLIENT_ID,
        authority=authority or Config.AUTHORITY,
        client_credential=Config.CLIENT_SECRET,
        token_cache=cache
    )


def _build_auth_url(authority=None, scopes=None, state=None):
    redirect_uri = _redirect_uri()

    app.logger.info(
        "Microsoft authorization redirect URI: %s",
        redirect_uri
    )

    return _build_msal_app(
        authority=authority
    ).get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=redirect_uri
    )