"""
Entry point — starts Flask + Socket.IO server.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.routes import flask_app, socketio, start_background_stream

if __name__ == '__main__':
    print("=" * 60)
    print("  Crisis Detection System - Starting Up")
    print("=" * 60)
    start_background_stream()
    socketio.run(flask_app, debug=False, host='0.0.0.0', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
