import flask
import insta485
from flask import redirect, url_for, request, abort, session

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/likes/", methods=["POST"])
def update_likes():
    # Extract data from the form
    operation = request.form["operation"]
    postid = request.form["postid"]
    # Default target to '/' if not provided
    target = request.args.get("target", "/")

    LOGGER.debug("operation = %s", operation)
    LOGGER.debug("postid = %s", postid)

    logname = session.get("logname")

    # Check if the user is logged in
    if logname is None:
        abort(403)

    # Database connection
    connection = insta485.model.get_db()

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
