from flask import Blueprint, jsonify
from core.analyzer import get_global_stats
from flask import current_app

status_bp = Blueprint('status', __name__)

@status_bp.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'ok', 'message': 'PyVAF API running'})

@status_bp.route('/stats', methods=['GET'])
def stats():
    app    = current_app._get_current_object()
    result = get_global_stats(app)
    return jsonify(result)