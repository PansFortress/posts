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
        session.add_all([postA, postB])
        session.commit()

    def test_get_empty_posts(self):
        response = self.client.get("/api/posts")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data, [])

    def test_created_posts(self):
        self.create_posts()

        response = self.client.get("/api/posts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 2)

        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just the body")

        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Just another body")


if __name__ == "__main__":
    unittest.main()
