"""
Insta485 index (main) view.

URLs include:
/
"""

import flask
import arrow

import insta485


@insta485.app.route("/posts/<postid_url_slug>/")
def show_post(postid_url_slug):
    """Display /posts/<post> route."""

    # Connect to database
    connection = insta485.model.get_db()

    # get post from database
    logname = "awdeorio"
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
        "logname": "awdeorio",
        "owner_liked": owner_liked
    }
    return flask.render_template("post.html", **context)
