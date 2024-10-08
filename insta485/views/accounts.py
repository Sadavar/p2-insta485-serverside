"""
Insta485 Accounts.

This module handles user account management features including
login, registration, deletion, editing, and password updates.

URLs include:
    /accounts/login/       - Display login page
    /accounts/create/      - Display account creation page
    /accounts/delete/      - Display account deletion page
    /accounts/edit/        - Display account editing page
    /accounts/password/     - Display password update page
"""

import sys
import pathlib
import uuid
import hashlib
import flask
from flask import request, abort, session, redirect

import insta485

from insta485.utils import get_db_connection


def get_hashed_password(password):
    """
    Generate a hashed password.

    This function takes a plain text password and returns a
    hashed password string using SHA-512 with a unique salt.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: A string containing the algorithm, salt, and hashed password.
    """
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def check_password(password, password_db_string):
    """
    Check if the provided password matches the stored hash.

    Args:
        password (str): The plain text password to check.
        password_db_string (str): The stored password hash string.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    algorithm, salt, password_hash = password_db_string.split('$')
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    return password_hash == hash_obj.hexdigest()


@insta485.app.route("/accounts/login/")
def show_login():
    """
    Display the login page.

    Returns:
        Flask Response: The rendered login page or
        redirect to home if logged in.
    """
    logname = session.get("logname")
    if logname is None:
        return flask.render_template("accounts_login.html")

    return flask.redirect("/")


@insta485.app.route("/accounts/create/")
def show_create():
    """
    Display the account creation page.

    Returns:
        Flask Response: The rendered account creation page
        or redirect if logged in.
    """
    logname = session.get("logname")
    if logname is not None:
        return flask.redirect("/accounts/edit/")

    return flask.render_template("accounts_create.html")


@insta485.app.route("/accounts/delete/")
def show_delete():
    """
    Display the account deletion page.

    Returns:
        Flask Response: The rendered account deletion page
        or redirect if not logged in.
    """
    logname = session.get("logname")
    if logname is None:
        return redirect("/accounts/login/")

    context = {"logname": logname}
    return flask.render_template("accounts_delete.html", **context)


@insta485.app.route("/accounts/edit/")
def show_edit():
    """
    Display the account editing page.

    Returns:
        Flask Response: The rendered account editing page
        or redirect if not logged in.
    """
    logname = session.get("logname")
    if logname is None:
        return redirect("/accounts/login/")
    connection = get_db_connection()

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT USERNAME, FULLNAME, EMAIL, FILENAME "
        "FROM users WHERE USERNAME = ?",
        (logname, )
    )
    profile = cur.fetchone()
    profile["filename"] = "/uploads/" + profile["filename"]
    print(profile, file=sys.stderr)
    context = {"profile": profile, "logname": logname}

    return flask.render_template("accounts_edit.html", **context)


@insta485.app.route("/accounts/password/")
def show_password():
    """
    Display the password update page.

    Returns:
        Flask Response: The rendered password update page
        or redirect if not logged in.
    """
    logname = session.get("logname")
    if logname is None:
        return redirect("/accounts/login/")

    context = {"logname": logname}
    return flask.render_template("accounts_password.html", **context)


@insta485.app.route("/accounts/auth/")
def auth():
    """
    Authenticate the user.

    Returns:
        Flask Response: An empty response with
        status code 200 if authenticated.

    Raises:
        403: If the user is not logged in.
    """
    logname = session.get("logname")
    if logname is None:
        abort(403)

    return "", 200


@insta485.app.route("/accounts/logout/", methods=["POST"])
def logout():
    """
    Logout the user.

    Returns:
        Flask Response: Redirects to the login page.
    """
    # logout the user
    session.pop("logname", None)
    return flask.redirect("/accounts/login/")


@insta485.app.route("/accounts/", methods=["POST"])
def update_accounts():
    """
    Update user accounts based on the specified operation.

    This function processes login, account creation, deletion,
    editing, and password updates based on form submission.

    Returns:
        Flask Response: Redirects to the target URL after the operation.
    """
    # Logged-in user's username
    logname = session.get("logname")
    connection = insta485.model.get_db()
    # Default target to '/' if not provided
    target = request.args.get("target", "/")
    operation = request.form["operation"]

    if operation == "login":
        login(logname, connection, target)
    elif operation == "create":
        create(logname, connection, target)
    elif operation == "delete":
        delete(logname, connection, target)
    elif operation == "edit_account":
        edit(logname, connection, target)
    elif operation == "update_password":
        update(logname, connection, target)

    return flask.redirect(target)


def login(logname, connection, target):
    """
    Handle user login.

    Args:
        logname (str): The current logged-in username.
        connection: The database connection object.
        target (str): The URL to redirect after login.

    Returns:
        Flask Response: Redirects to the target URL if successful.

    Raises:
        400: If username or password is missing.
        403: If login fails.
    """
    if logname is not None:
        return flask.redirect(target)

    username = request.form["username"]
    password = request.form["password"]
    print(username, password, file=sys.stderr)
    if not username or not password:
        abort(400)
    password_db_string = connection.execute(
        "SELECT PASSWORD FROM users WHERE USERNAME = ?",
        (username, )
    ).fetchone()
    if not password_db_string:
        abort(403)
    password_db_string = password_db_string["password"]
    if check_password(password, password_db_string):
        session["logname"] = username
        return flask.redirect(target)

    abort(403)


def create(logname, connection, target):
    """
    Handle user account creation.

    Args:
        logname (str): The current logged-in username.
        connection: The database connection object.
        target (str): The URL to redirect after creation.

    Returns:
        Flask Response: Redirects to the target URL if successful.

    Raises:
        400: If required fields are missing.
        409: If the username is already taken.
    """
    if logname is not None:
        return flask.redirect("/accounts/edit/")

    username = request.form["username"]
    fullname = request.form["fullname"]
    email = request.form["email"]
    password = request.form["password"]
    file_obj = request.files["file"]
    password_db_string = get_hashed_password(password)

    if not username or not fullname or not email:
        abort(400)
    if not password or file_obj.filename == '':
        abort(400)

    # Check if the username is already taken
    existing_user = connection.execute(
        "SELECT * FROM users WHERE USERNAME = ?",
        (username, )
    ).fetchone()
    if existing_user:
        abort(409)

    # Save the profile picture
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(file_obj.filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    file_obj.save(path)

    connection.execute(
        "INSERT INTO users "
        "(USERNAME, FULLNAME, EMAIL, PASSWORD, FILENAME) "
        "VALUES (?, ?, ?, ?, ?) ",
        (username, fullname, email, password_db_string, path.name)
    )

    session["logname"] = username
    return flask.redirect(target)


def delete(logname, connection, target):
    """
    Handle user account deletion.

    Args:
        logname (str): The logged-in username.
        connection: The database connection object.
        target (str): The URL to redirect after deletion.

    Returns:
        Flask Response: Redirects to the target URL after deletion.

    Raises:
        403: If the user is not logged in.
    """
    if logname is None:
        abort(403)

    # Delete the user's profile picture
    filename = connection.execute(
        "SELECT FILENAME FROM users WHERE USERNAME = ?",
        (logname, )
    ).fetchone()["filename"]
    pathname = insta485.app.config["UPLOAD_FOLDER"]/filename
    if pathname.exists():
        pathname.unlink()

    # Delete the user's post pictures
    post_filenames = connection.execute(
        "SELECT FILENAME FROM posts WHERE OWNER = ?",
        (logname, )
    ).fetchall()
    for post_filename in post_filenames:
        post_pathname = insta485.app.config["UPLOAD_FOLDER"] / \
            post_filename["filename"]
        if post_pathname.exists():
            post_pathname.unlink()

    # Delete the user
    connection.execute(
        "DELETE FROM users WHERE USERNAME = ?",
        (logname, )
    )
    session.pop("logname", None)
    return flask.redirect(target)


def edit(logname, connection, target):
    """
    Edit account function.

    Args:
        logname (str): The logged-in username.
        connection: The database connection object.
        target (str): The URL to redirect after deletion.

    Returns:
        Flask Response: Redirects to the target URL after deletion.

    Raises:
        403: If the user is not logged in.
    """
    if logname is None:
        abort(403)

    fullname = request.form["fullname"]
    email = request.form["email"]
    file_obj = request.files["file"]

    if not fullname or not email:
        abort(400)

    if file_obj.filename != '':
        # Delete the old profile picture
        filename = connection.execute(
            "SELECT FILENAME FROM users WHERE USERNAME = ?",
            (logname, )
        ).fetchone()
        if filename:
            pathname = insta485.app.config["UPLOAD_FOLDER"] / \
                filename["filename"]
            if pathname.exists():
                pathname.unlink()

        # Save the profile picture
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(file_obj.filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        file_obj.save(path)
        connection.execute(
            "UPDATE users SET FILENAME = ? WHERE USERNAME = ?",
            (path.name, logname)
        )

    connection.execute(
        "UPDATE users SET FULLNAME = ?, EMAIL = ? WHERE USERNAME = ?",
        (fullname, email, logname)
    )

    return flask.redirect(target)


def update(logname, connection, target):
    """
    Update account function.

    Args:
        logname (str): The logged-in username.
        connection: The database connection object.
        target (str): The URL to redirect after deletion.

    Returns:
        Flask Response: Redirects to the target URL after deletion.

    Raises:
        403: If the user is not logged in.
    """
    if logname is None:
        abort(403)

    old_password = request.form["password"]
    new_password = request.form["new_password1"]
    confirm_password = request.form["new_password2"]

    if not old_password or not new_password or not confirm_password:
        abort(400)

    password_db_string = connection.execute(
        "SELECT PASSWORD FROM users WHERE USERNAME = ?",
        (logname, )
    ).fetchone()["password"]
    if not check_password(old_password, password_db_string):
        abort(403)
    if new_password != confirm_password:
        abort(400)

    new_password_db_string = get_hashed_password(new_password)
    connection.execute(
        "UPDATE users SET PASSWORD = ? WHERE USERNAME = ?",
        (new_password_db_string, logname)
    )

    return flask.redirect(target)
