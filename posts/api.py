import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from posts import app
from .database import session

@app.route("/api/posts", methods=["GET"])
def posts_get():
    """Get a list of posts"""
    posts = session.query(models.Post).order_by(models.Post.id)

    #Convert posts to JSON
    data = json.dumps([post.as_dictionary() for post in posts])
    return Response(data, 200, mimetype="application/json")