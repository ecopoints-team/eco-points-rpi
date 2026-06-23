"""
Main routes file - registers all blueprints
"""
from flask import current_app as app, jsonify


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'EcoPoints API Server',
        'version': '1.0.0',
        'endpoints': {
            'web': '/api/web',
            'rpi': '/api/rpi'
        }
    }), 200


@app.route('/health')
def health():
    """Global health check"""
    return jsonify({
        'status': 'healthy',
        'message': 'EcoPoints API is running'
    }), 200
