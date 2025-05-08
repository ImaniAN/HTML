import os
from datetime import timedelta

class Config:
    #Security
    SECRET_KEY = os.urandom(32)

    #Database
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'cafe_admin',
        'password': 'admin@123',
        'datbase': 'cafe_db'
    }

    #Print Server
    PRINT_SERVER = {
        'host': 'localhost',
        'port': 631,
        'admin': 'print_admin',
        'password': 'print@123'
    }

    #proxy setting
    PROXY_CONFIG = {
        'port': 3128, 
        'cache_dir': '/var/spool/squid',
        'cache_size': 1000,
        'allowed_domains': ['com', 'edu', 'gov', 'org'],
        'blocked_domains': ['twitter.com', 'instagram.com', 'tiktok.com']
    }

    #Billing
    BILLING_RATES = {
        'internet': {
            'per_minute': 0.05,
            'per_hour': 2.50,
            'per_day': 15.00
        },
        'printing': {
            'black_white': 0.10,
            'color': 0.25
        }
    }

    #Session/Cookie settings
    SESSION_COOKIE_SECURE =True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    #Rate limiting
    RATELIMIT_DEFAULT = "100 per day"
    RATELIMIT_STORAGE_URL = "memory://"
   
    #Database
    SQLALCHEMY_DATABASE_URL = 'mysql://cafe_admin:admin123@localhost/cafe_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #Email settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'admin@gmail.com'
    MAIL_PASSWORD = 'admin@123'
