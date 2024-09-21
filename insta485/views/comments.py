import flask
import insta485
from flask import redirect, url_for, request, abort, session

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/comments/", methods=["POST"])
def update_comments():

    # Extract data from the form
    operation = request.form.get("operation")
    postid = request.form.get("postid")
    commentid = request.form.get("commentid")
    text = request.form.get("text")
    # Default target to '/' if not provided
    target = request.args.get("target", "/")

    LOGGER.debug("operation = %s", operation)
    LOGGER.debug("postid = %s", postid)
    LOGGER.debug("commentid = %s", commentid)
    LOGGER.debug("text = %s", text)

    logname = session.get("logname")

    # Check if the user is logged in
    if logname is None:
        abort(403)

    # Database connection
    connection = insta485.model.get_db()

    if operation == "create":
        # Ensure that the comment text is not empty
        if not text or not text.strip():
            print("Comment text cannot be empty", file=flask.stderr)
            abort(400, "Comment text cannot be empty")

        # Insert the new comment into the database
        LOGGER.debug("Inserting comment: postid%s, text:%s", postid, text)
        connection.execute(
            "INSERT INTO comments (owner, postid, text) VALUES (?, ?, ?)",
            (logname, postid, text)
        )

    elif operation == "delete":
        # Ensure commentid is provided
        if not commentid:
            abort(400)

        # Verify the user owns the comment
        comment = connection.execute(
            "SELECT owner FROM comments WHERE commentid = ?",
            (commentid,)
        ).fetchone()

        if not comment:
            abort(404)  # Comment does not exist

        if comment['owner'] != logname:
            abort(403)

        # Delete the comment from the database
        connection.execute(
            "DELETE FROM comments WHERE commentid = ?",
            (commentid,)
        )

    else:
        abort(400)

    return redirect(target)
