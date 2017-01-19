import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from posts import app
from .database import session

post_schema = {
    "properties":{
        "title": {"type": "string"},
        "body": {"type": "string"}
    },
    "required": ["title", "body"]
}

@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
    """Get a list of posts"""
    
    title_like = request.args.get("title_like")
    body_like = request.args.get("body_like")

    posts = session.query(models.Post)
    if title_like:
        posts = posts.filter(models.Post.title.contains(title_like))
    if body_like:
        posts = posts.filter(models.Post.body.contains(body_like))
    posts = posts.order_by(models.Post.id)

    #Convert posts to JSON
    data = json.dumps([post.as_dictionary() for post in posts])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/posts", methods=["POST"])
@decorators.require("application/json")
def posts_post():
    """Accepts and adds a post to the database"""
    data = request.json

    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")

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

@app.route("/api/posts/<int:id>", methods=["PUT"])
def post_put(id):
    data = request.json

    try:
        validate(data, post_schema)
        post = session.query(models.Post).get(id)
        if not post:
            new_post = models.Post(title=data["title"], body=data["body"], id=id)
            session.add(new_post)
            session.commit()
            
            message = "New post has been added with Title: {}".format(data["title"])
            data = json.dumps({"message": message})

            return Response(data, 201, mimetype="application/json")
        else:
            post.title = data["title"]
            post.body = data["body"]
            session.commit()
            message = "Post has been updated"
            data = json.dumps({"message": message})
            return Response(data, 200, mimetype="application/json")


    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")