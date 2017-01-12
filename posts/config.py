class DevelopmentConfig(object):
    DATABASE_URI = "postgresql:///posts"
    DEBUG = True

class TestingConfig(object):
    DATABASE_URI = "postgresql://localhost:5432/posts-test"
    DEBUG = True
