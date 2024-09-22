"""
Insta485 uploads module.

URLs include:
    /uploads/<filename>
"""

from pathlib import Path
import sys

from flask import Flask, request, abort, send_from_directory, session

import insta485


@insta485.app.route("/uploads/<filename>")
def get_upload(filename):
    """
    Serve a file from the upload directory.

    This function checks if the user is logged in before allowing access
    to the requested file. If the user is not logged in, a 403 error is
    raised. If the filename is not provided, a 404 error is raised.

    Args:
        filename (str): The name of the file to retrieve.

    Returns:
        Flask Response: The requested file from the upload directory.

    Raises:
        403: If the user is not logged in.
        404: If the filename is not provided.
    """
    logname = session.get("logname")
    if logname is None:
        abort(403)

    if not filename:
        abort(404)

    return send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)
