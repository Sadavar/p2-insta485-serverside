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

algorithm = 'sha512'
salt = uuid.uuid4().hex

def get_hashed_password(password):
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string

@insta485.app.route("/accounts/login/")
def show_login():
    return flask.render_template("accounts_login.html")

@insta485.app.route("/accounts/create/")
def show_create():
    return flask.render_template("accounts_create.html")

@insta485.app.route("/accounts/delete/")
def show_delete():
    # Logged-in user's username
    logname = session.get("logname")
    context = {"logname": logname}
    return flask.render_template("accounts_delete.html", **context)

@insta485.app.route("/accounts/edit/")
def show_edit():
    # Logged-in user's username
    logname = session.get("logname")
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT USERNAME, FULLNAME, EMAIL, FILENAME FROM users WHERE USERNAME = ?",
        (logname, )
    )
    profile = cur.fetchone()
    profile["filename"] = "/uploads/" + profile["filename"]
    print(profile, file=sys.stderr)
    context = {"profile": profile, "logname": logname}
    return flask.render_template("accounts_edit.html", **context)

@insta485.app.route("/accounts/password/")
def show_password():
    # Logged-in user's username
    logname = session.get("logname")
    context = {"logname": logname}
    return flask.render_template("accounts_password.html", **context)

@insta485.app.route("/accounts/", methods=["POST"])
def update_accounts():
    print(request.form, file=sys.stderr)
    print("poooooooooooop", file=sys.stderr)
    connection = insta485.model.get_db()
    # Default target to '/' if not provided
    target = request.args.get("target", "/")
    operation = request.form["operation"]



    if operation == "create":
        username = request.form["username"]
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        filename = request.files["file"]
        password_db_string = get_hashed_password(password)

        filename.save(Path.cwd() / "sql" / "uploads" / filename.filename)
        connection.execute(
            "INSERT INTO users (USERNAME, FULLNAME, EMAIL, PASSWORD, FILENAME) VALUES (?, ?, ?, ?, ?)",
            (username, fullname, email, password_db_string, filename.filename)
        )
    elif operation == "login":
        username = request.form["username"]
        password = request.form["password"]
        if username == "" or password == "":
            abort(400)
        password_db_string = get_hashed_password(password)
        user = connection.execute(
            "SELECT * FROM users WHERE USERNAME = ? AND PASSWORD = ?",
            (username, password_db_string)
        ).fetchone()
        if user:
            session["logname"] = username
            return flask.redirect(target)
        else:
            abort(403)
    elif operation == "edit_account":
        fullname = request.form["fullname"]
        email = request.form["email"]
        filename = request.files["file"]

        # Delete the old file
        old_filename = connection.execute(
            "SELECT FILENAME FROM users WHERE USERNAME = ?",
            (logname, )
        ).fetchone()
        old_file_path = Path.cwd() / "sql" / "uploads" / old_filename['filename']
        old_file_path.unlink()
        filename.save(Path.cwd() / "sql" / "uploads" / filename.filename)
        # Update the user's information
        connection.execute(
            "UPDATE users SET FULLNAME = ?, EMAIL = ?, FILENAME = ? WHERE USERNAME = ?",
            (fullname, email, filename.filename, logname)
        )

    return flask.redirect(target)