# API endpoints package

from flask import Flask
from app.api.main import app

__all__ = ['app']

def create_app():
    
    return app 