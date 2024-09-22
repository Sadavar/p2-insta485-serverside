"""
Insta485 Likes Management.

This module handles the liking and unliking
of posts within the application.

URLs include:
    /likes/
"""
import flask
from flask import redirect, request, abort, session
import insta485
from insta485.utils import get_db_connection

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/likes/", methods=["POST"])
def update_likes():
    """
    Update the like status of a post.

    This function processes like and unlike operations for a post
    based on the logged-in user's action. It checks the user's
    session status and updates the database accordingly.

    Returns:
        Flask Response: A redirect to the target URL or an error response.
    """
    # Extract data from the form
    operation = request.form["operation"]
    postid = request.form["postid"]
    # Default target to '/' if not provided
    target = request.args.get("target", "/")

    LOGGER.debug("operation = %s", operation)
    LOGGER.debug("postid = %s", postid)

    logname = session.get("logname")
    if logname is None:
        abort(403)
    connection = get_db_connection()

    if operation == "like":
        # Check if the user has already liked the post
        existing_like = connection.execute(
            "SELECT * FROM likes WHERE owner = ? AND postid = ?",
            (logname, postid)
        ).fetchone()

        if existing_like:
            abort(409)

        # Insert a new like
        connection.execute(
            "INSERT INTO likes (owner, postid) VALUES (?, ?)",
            (logname, postid)
        )

    elif operation == "unlike":
        # Check if the user has liked the post
        existing_like = connection.execute(
            "SELECT * FROM likes WHERE owner = ? AND postid = ?",
            (logname, postid)
        ).fetchone()

        if not existing_like:
            abort(409)

        # Delete the like
        connection.execute(
            "DELETE FROM likes WHERE owner = ? AND postid = ?",
            (logname, postid)
        )

    else:
        abort(400)

    # Redirect to the target URL
    return redirect(target)
