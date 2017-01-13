class DevelopmentConfig(object):
    DATABASE_URI = "postgresql:///posts"
    DEBUG = True

class TestingConfig(object):
    DATABASE_URI = "postgresql:///posts-test"
    DEBUG = True
