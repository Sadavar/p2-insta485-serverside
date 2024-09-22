"""
Insta485 Index (Main) View.

This module handles the main views for the Insta485 application,
including displaying individual posts and updating posts.

URLs include:
    /posts/<postid_url_slug>/ - Display a specific post
    /posts/ - Create or delete a post
"""

import pathlib
import uuid
import flask
from flask import request, abort, redirect, session
import arrow

import insta485

from insta485.utils import get_db_connection


@insta485.app.route("/posts/<postid_url_slug>/")
def show_post(postid_url_slug):
    """
    Display a specific post.

    This function retrieves a post from the database using the provided
    post ID slug, along with its owner, likes, and comments. It renders
    the post details on the post page.

    Args:
        postid_url_slug (str): The slug of the post to display.

    Returns:
        Flask Response: The rendered post page or a 404 error if not found.
    """
    logname = session.get("logname")
    if logname is None:
        return redirect("/accounts/login/")
    connection = get_db_connection()

    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE postid = ? ",
        (postid_url_slug, )
    )
    post = cur.fetchone()
    if post is None:
        return ("", 404)

    # add image urls to post
    post["url"] = f"/uploads/{post['filename']}"

    # get owner of post
    post_owner = post["owner"]
    cur = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (post_owner, )
    )
    owner = cur.fetchone()

    # add image url to owner
    owner["url"] = f"/uploads/{owner['filename']}"

    # Get likes for the post
    cur = connection.execute(
        "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
        (postid_url_slug, )
    )
    likes = cur.fetchone()["like_count"]

    # Get comments for the post
    cur = connection.execute(
        "SELECT * FROM comments WHERE postid = ?",
        (postid_url_slug, )
    )
    comments = cur.fetchall()

    # Check if owner has liked post
    cur = connection.execute(
        "SELECT * FROM likes WHERE postid = ? AND owner = ?",
        (postid_url_slug, logname)
    )
    owner_liked = cur.fetchone()

    # Convert timestamp of post to human readable format
    post["created"] = arrow.get(post["created"]).humanize()

    # Add all information to context
    context = {
        "post": post,
        "owner": owner,
        "likes": likes,
        "comments": comments,
        "logname": logname,
        "owner_liked": owner_liked
    }
    return flask.render_template("post.html", **context)


@insta485.app.route("/posts/", methods=["POST"])
def update_post():
    """
    Create or delete a post.

    This function handles the creation of new posts or the deletion
    of existing posts based on the operation specified in the form.

    Returns:
        Flask Response: Redirects to the target URL after operation.

    Raises:
        403: If the user is not logged in or does not own the post.
        400: If the operation is invalid or the file is empty.
    """
    logname = session.get("logname")
    print("getting logname")
    if logname is None:
        abort(403)
    connection = get_db_connection()

    operation = request.form["operation"]
    target = request.args.get("target", f"/users/{logname}/")

    if operation == "create":
        fileobj = request.files.get("file")
        # Check if the file is empty
        if not fileobj or fileobj.filename == "":
            abort(400)

        filename = fileobj.filename

        # Generate UUID-based filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"

        # Define the file path
        upload_folder = insta485.app.config["UPLOAD_FOLDER"]
        filepath = pathlib.Path(upload_folder) / uuid_basename

        # Save the file to the uploads directory
        fileobj.save(filepath)

        # Insert the post into the database
        connection.execute(
            "INSERT INTO posts (filename, owner) VALUES (?, ?)",
            (uuid_basename, logname)
        )

        # Redirect to target URL
        return redirect(target)

    if operation == "delete":
        postid = request.form.get("postid")

        # Fetch the post details
        post = connection.execute(
            "SELECT filename, owner FROM posts WHERE postid = ?",
            (postid,)
        ).fetchone()

        # Check if the post exists and if the user owns the post
        if post is None or post['owner'] != logname:
            abort(403)

        # Delete the image file from the filesystem
        filepath = pathlib.Path(
            insta485.app.config["UPLOAD_FOLDER"]) / post['filename']
        if filepath.exists():
            filepath.unlink()

        # Delete related entries (comments, likes) in the database
        connection.execute("DELETE FROM comments WHERE postid = ?", (postid,))
        connection.execute("DELETE FROM likes WHERE postid = ?", (postid,))
        connection.execute("DELETE FROM posts WHERE postid = ?", (postid,))

        # Redirect to target URL
        return redirect(target)

    # If operation is not recognized, abort
    abort(400)
