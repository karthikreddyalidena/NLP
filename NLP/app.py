"""
Main Application Entry Point (app.py)
This file is provided for environments that specifically look for an `app.py` file.
It behaves exactly like run.py and wsgi.py.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import eventlet
eventlet.monkey_patch()

from app.routes import flask_app, socketio, start_background_stream

# For WSGI servers (like Gunicorn)
application = flask_app

if __name__ == '__main__':
    print("=" * 60)
    print("  Crisis Detection System - Starting via app.py")
    print("=" * 60)
    start_background_stream()
    socketio.run(flask_app, debug=False, host='0.0.0.0', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
