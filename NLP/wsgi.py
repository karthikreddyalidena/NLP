"""
WSGI Entry Point for Production Servers (Gunicorn)
"""

import eventlet
eventlet.monkey_patch()

from app.routes import flask_app, start_background_stream

# Start the background background threads that fetch real-time data
start_background_stream()

# Expose the flask_app as 'application' which Gunicorn looks for
application = flask_app
