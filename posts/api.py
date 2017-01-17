import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from posts import app
from .database import session

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
    """Get a list of posts"""
    
    title_like = request.args.get("title_like")
    body_like = request.args.get("body_like")

    posts = session.query(models.Post)
    if title_like and body_like:
        posts = posts.filter(models.Post.title.contains(title_like)).filter(models.Post.body.contains(body_like))
    elif title_like:
        posts = posts.filter(models.Post.title.contains(title_like))
    elif body_like:
        posts = posts.filter(models.Post.body.contains(body_like))
    posts = posts.order_by(models.Post.id)

    #Convert posts to JSON
    data = json.dumps([post.as_dictionary() for post in posts])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
def posts_post():
    """Accepts and adds a post to the database"""
    data = request.json

    post = models.Post(title=data["title"], body=data["body"])
    session.add(post)
    session.commit()

    # Return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the past
    data = json.dumps(post.as_dictionary())
    headers = {"Location": url_for("post_get", id=post.id)}
    return Response(data, 201, headers=headers, mimetype="application/json")

@decorators.accept("application/json")
@app.route("/api/posts/<int:id>", methods=["GET"])
def post_get(id):
    """Get a single post"""
    post = session.query(models.Post).get(id)

    if not post:
        message = "Could not find post with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    data = json.dumps(post.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts/<int:id>", methods=["DELETE"])
def post_delete(id):
    """Delete a single post"""
    post = session.query(models.Post).get(id)
    session.delete(post)
    session.commit()

    message = "{} has been deleted successfully".format(id)
    data = json.dumps({"message": message})

    return Response(data, 200, mimetype="application/json")

# TODO Update to include PUT to add an entry