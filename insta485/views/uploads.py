"""
Insta485 uploadss

URLs include:
/upload
"""

from pathlib import Path
import sys

from flask import Flask, request, abort, send_from_directory

import insta485

uploads_path = Path.cwd() / "sql" / "uploads"


@insta485.app.route("/uploads/")
def get_upload():
    filename = request.args.get("filename")
    print(f"filename: {filename}", file=sys.stderr)
    if not filename:  # Route parameter is captured here
        abort(403)

    print(filename)
    print(uploads_path)
    return send_from_directory(uploads_path, filename)
