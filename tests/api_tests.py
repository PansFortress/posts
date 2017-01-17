import unittest
import os
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Python 2 compatibility

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)
    
    def create_posts(self):
        """Getting posts from a populated database"""
        postA = models.Post(title = "Example Post A", body = "Just the body")
        postB = models.Post(title = "Example Post B", body = "Just another body")
        postC = models.Post(title = "Example whistles C", body = "Post with whiskers")
        session.add_all([postA, postB, postC])
        session.commit()
        return postA.id, postB.id, postC.id

    def test_get_empty_posts(self):
        response = self.client.get("/api/posts", 
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data, [])

    def test_created_posts(self):
        self.create_posts()

        response = self.client.get("/api/posts", 
            headers=[("Accept", "application/json")])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 3)

        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just the body")

        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Just another body")

    def test_get_post(self):
        post_a_id, post_b_id, post_c_id = self.create_posts()

        response = self.client.get("/api/posts/{}".format(post_b_id),
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        post = json.loads(response.data.decode("ascii"))
        self.assertEqual(post["title"], "Example Post B")
        self.assertEqual(post["body"], "Just another body")

    def test_get_non_existent_post(self):
        """Getting a single post which doesn't exist"""
        response = self.client.get("/api/posts/1", 
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Could not find post with id 1")

    def test_unsupported_accept_header(self):
        response = self.client.get("/api/posts", 
            headers=[("Accept", "application/xml")])

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"],
                         "Request must accept application/json data")

    def test_delete_post(self):
        post_a_id, post_b_id, post_c_id = self.create_posts()
        response = self.client.delete("/api/posts/{}".format(post_b_id),
            headers=[("Accept","application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], 
                         "{} has been deleted successfully".format(post_b_id))

    def test_get_post_with_titles(self):
        post_a_id, post_b_id, post_c_id = self.create_posts()
        response = self.client.get("/api/posts?title_like=whistles",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        posts = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(posts), 1)

        post = posts[0]
        self.assertEqual(post["title"], "Example whistles C")

    def test_get_post_with_body(self):
        post_a_id, post_b_id, post_c_id = self.create_posts()
        response = self.client.get("/api/posts?body_like=whiskers",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        posts = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(posts),1)

        post = posts[0]
        self.assertEqual(post["body"], "Post with whiskers")

    def test_get_post_with_body_and_title(self):
        post_a_id, post_b_id, post_c_id = self.create_posts()
        response = self.client.get("/api/posts?body_like=body&title_like=Post",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        posts = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(posts),2)

        postA = posts[0]
        self.assertEqual(postA["title"], "Example Post A")

        postB = posts[1]
        self.assertEqual(postB["title"], "Example Post B")

    def test_post_request(self):
        data = {
            "title": "Example post",
            "body": "Testing the body of an example post"
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/posts/1")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example post")
        self.assertEqual(data["body"], "Testing the body of an example post")

        posts = session.query(models.Post).all()
        self.assertEqual(len(posts),1)

        post = posts[0]
        self.assertEqual(post.title, "Example post")
        self.assertEqual(post.body, "Testing the body of an example post")

    def test_unsupported_mimetype(self):
        data = "<xml></xml>"
        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"],
                         "Request must contain application/json data")

    def test_invalid_data(self):
        data = {
            "title": "Example title",
            "body": 32
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "32 is not of type 'string'")

    def test_missing_data(self):
        data = {
            "title": "Example title"
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "'body' is a required property")

if __name__ == "__main__":
    unittest.main()
