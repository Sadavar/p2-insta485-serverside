"""
Insta485 index (main) view.

URLs include:
/
"""

import flask

import insta485


@insta485.app.route("/")
def show_index():
    """Display / route."""

    # Connect to database
    connection = insta485.model.get_db()

    # Get users
    logname = "awdeorio"
    cur = connection.execute(
        "SELECT username, fullname "
        "FROM users "
        "WHERE username != ?",
        (logname,)
    )
    users = cur.fetchall()

    # Get posts
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE owner != ?",
        (logname, )
    )
    posts = cur.fetchall()

    # Add image urls to posts
    for post in posts:
        post["url"] = f"/uploads/{post['filename']}"

    # Add database info to context
    context = {"users": users, "posts": posts}
    return flask.render_template("index.html", **context)
