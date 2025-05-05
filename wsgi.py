"""
WSGI configuration for PythonAnywhere deployment.
"""
import sys
import os

# Add the project directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app import app as application  # noqa

# This is the PythonAnywhere WSGI entry point
