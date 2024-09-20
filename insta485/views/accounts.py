"""
Insta485 accounts

URLs include:
"""

import sys
import flask
import arrow
from flask import request, session
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
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    context = {"logname": logname}
    return flask.render_template("accounts_password.html", **context)


@insta485.app.route("/accounts/", methods=["POST"])
def update_accounts():
    connection = insta485.model.get_db()
    # Default target to '/' if not provided
    target = request.args.get("target", "/")

    username = request.form["username"]
    fullname = request.form["fullname"]
    email = request.form["email"]
    password = request.form["password"]
    filename = request.files["file"]
    operation = request.form["operation"]

    password_db_string = get_hashed_password(password)

    if operation == "create":
        filename.save(Path.cwd() / "sql" / "uploads" / filename.filename)
        connection.execute(
            "INSERT INTO users (USERNAME, FULLNAME, EMAIL, PASSWORD, FILENAME) VALUES (?, ?, ?, ?, ?)",
            (username, fullname, email, password_db_string, filename.filename)
        )
    elif operation == "edit_account":
        # Delete the old file
        old_filename = connection.execute(
            "SELECT FILENAME FROM users WHERE USERNAME = ?",
            (logname, )
        ).fetchone()
        old_file_path = Path.cwd() / "sql" / "uploads" / \
            old_filename["FILENAME"]
        old_file_path.delete()
        filename.save(Path.cwd() / "sql" / "uploads" / filename.filename)
        connection.execute(
            "UPDATE users SET FULLNAME = ?, EMAIL = ?, FILENAME = ? WHERE USERNAME = ?",
            (fullname, email, filename.filename, logname)
        )

    return flask.redirect(target)
