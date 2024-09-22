"""
Insta485 Following Management.

This module handles the following functionality for
users in the Insta485 application.
It allows users to follow or unfollow other users.

Routes:
    POST /following/ - Updates the following status for a user.
"""
import flask
from flask import redirect, request, abort, session
import insta485

from insta485.utils import get_db_connection

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/following/", methods=["POST"])
def update_following():
    """
    Update the following status for a user.

    This function allows the logged-in user to
    follow or unfollow another user.
    It checks for the user's login status and
    validates the operation before
    performing the database update.

    Args:
        operation (str): The operation to perform,
        either "follow" or "unfollow".
        username (str): The username of the user to follow or unfollow.

    Returns:
        Flask Response: Redirects to the target URL.

    Raises:
        403: If the user is not logged in.
        400: If the operation is invalid.
        409: If trying to follow a user already being followed or unfollow
              a user that is not being followed.
    """
    # Extract data from the form
    operation = request.form["operation"]
    username = request.form.get("username")
    # Default target to '/' if not provided
    target = request.args.get("target", "/")

    LOGGER.debug("operation = %s", operation)
    LOGGER.debug("username = %s", username)

    logname = session.get("logname")
    if logname is None:
        abort(403)
    connection = get_db_connection()

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
