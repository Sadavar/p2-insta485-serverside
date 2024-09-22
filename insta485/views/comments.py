"""
This module handles comment-related operations for the Insta485 application.

It provides a route for creating and deleting comments associated with posts.
Users must be logged in to perform these actions. The module uses Flask's
routing system and connects to the database to execute the required operations.
"""

import flask
import insta485
from flask import redirect, url_for, request, abort, session

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/comments/", methods=["POST"])
def update_comments():
    """
    Handle POST requests to create or delete comments for posts.

    Extracts the form data to determine the operation (create or delete) and
    processes the request accordingly. Only logged-in users can perform these
    actions.

    Methods:
        POST: The form should contain the following fields:
            - operation: "create" or "delete"
            - postid: ID of the post associated with the comment
            - commentid: ID of the comment to be deleted (only for delete)
            - text: Text of the comment (only for create)
            - target: URL to redirect after the operation (default is "/")

    Returns:
        Redirects to the 'target' URL after the operation.

    Raises:
        403: If the user is not logged in or trying to delete a comment they
             do not own.
        400: If required form data is missing or invalid.
        404: If the comment to be deleted does not exist.
    """
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
