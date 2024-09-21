import flask
import insta485
from flask import redirect, url_for, request, abort, session

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/following/", methods=["POST"])
def update_following():

    # Extract data from the form
    operation = request.form["operation"]
    username = request.form.get("username")
    # Default target to '/' if not provided
    target = request.args.get("target", "/")

    LOGGER.debug("operation = %s", operation)
    LOGGER.debug("username = %s", username)

    logname = session.get("logname")

    # Check if the user is logged in
    if logname is None:
        abort(403)

    # Database connection
    connection = insta485.model.get_db()

    if operation == "follow":
        # Check if the user is already following the target user
        existing_follow = connection.execute(
            "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
            (logname, username)
        ).fetchone()

        if existing_follow:
            abort(409)

        # Insert a new follow
        connection.execute(
            "INSERT INTO following (username1, username2) VALUES (?, ?)",
            (logname, username)
        )
    elif operation == "unfollow":
        # Check if the user is following the target user
        existing_follow = connection.execute(
            "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
            (logname, username)
        ).fetchone()

        if not existing_follow:
            abort(409)

        # Delete the follow
        connection.execute(
            "DELETE FROM following WHERE username1 = ? AND username2 = ?",
            (logname, username)
        )
    else:
        abort(400)

    return redirect(target)
