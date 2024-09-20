"""
Insta485 accounts

URLs include:
"""

import sys
import flask
import arrow

import insta485

# Logged-in user's username
logname = "awdeorio"

@insta485.app.route("/accounts/login/")
def show_login():
    return flask.render_template("accounts_login.html")

@insta485.app.route("/accounts/create/")
def show_create():
    return flask.render_template("accounts_create.html")

@insta485.app.route("/accounts/delete/")
def show_delete():
    context = {"logname": logname}
    return flask.render_template("accounts_delete.html", **context)

@insta485.app.route("/accounts/edit/")
def show_edit():
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
    context = {"logname": logname}
    return flask.render_template("accounts_password.html", **context)