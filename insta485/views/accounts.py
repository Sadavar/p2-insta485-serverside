"""
Insta485 accounts

URLs include:
"""

import sys
import flask
import arrow
from flask import request, abort, session
from pathlib import Path
import uuid
import hashlib

import insta485


def get_hashed_password(password):
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def check_password(password, password_db_string):
    algorithm, salt, password_hash = password_db_string.split('$')
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    return password_hash == hash_obj.hexdigest()


@insta485.app.route("/accounts/login/")
def show_login():
    logname = session.get("logname")
    if logname is not None:
        return flask.redirect("/")

    return flask.render_template("accounts_login.html")


@insta485.app.route("/accounts/create/")
def show_create():
    logname = session.get("logname")
    if logname is not None:
        return flask.redirect("/accounts/edit/")

    return flask.render_template("accounts_create.html")


@insta485.app.route("/accounts/delete/")
def show_delete():
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    context = {"logname": logname}
    return flask.render_template("accounts_delete.html", **context)


@insta485.app.route("/accounts/edit/")
def show_edit():
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

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
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    context = {"logname": logname}
    return flask.render_template("accounts_password.html", **context)


@insta485.app.route("/accounts/auth/")
def auth():
    logname = session.get("logname")
    if logname is None:
        abort(403)
    else:
        return "", 200
        #


@insta485.app.route("/accounts/logout/", methods=["POST"])
def logout():
    # logout the user
    session.pop("logname", None)
    return flask.redirect("/accounts/login/")


@insta485.app.route("/accounts/", methods=["POST"])
def update_accounts():
    # Logged-in user's username
    logname = session.get("logname")
    connection = insta485.model.get_db()
    # Default target to '/' if not provided
    target = request.args.get("target", "/")
    operation = request.form["operation"]

    if operation == "login":
        login(logname, connection, target, request)
    elif operation == "create":
        create(logname, connection, target, request)
    elif operation == "delete":
        delete(logname, connection, target, request)
    elif operation == "edit_account":
        edit(logname, connection, target, request)
    elif operation == "update_password":
        update(logname, connection, target, request)

    return flask.redirect(target)


def login(logname, connection, target, request):
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
    else:
        abort(403)


def create(logname, connection, target, request):
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
    suffix = Path(file_obj.filename).suffix.lower()
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


def delete(logname, connection, target, request):
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


def edit(logname, connection, target, request):
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
        suffix = Path(file_obj.filename).suffix.lower()
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


def update(logname, connection, target, request):
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
