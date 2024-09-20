"""
Insta485 uploadss

URLs include:
/upload
"""

from pathlib import Path
import sys

from flask import Flask, request, abort, send_from_directory, session

import insta485

uploads_path = Path.cwd() / "sql" / "uploads"


@insta485.app.route("/uploads/<filename>/")
def get_upload(filename):
    print(f"filename: {filename}", file=sys.stderr)
    logname = session.get("logname")
    if logname is None:
        abort(403)

    if not filename:  # Route parameter is captured here
        abort(404)

    print(filename)
    print(uploads_path)
    return send_from_directory(uploads_path, filename)
