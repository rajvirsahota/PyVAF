from flask import Blueprint, jsonify, current_app
import threading

report_bp = Blueprint('report', __name__)

@report_bp.route('/report/<int:scan_id>', methods=['POST'])
def generate_report(scan_id):
    from core.reporter import generate_report as gen
    app = current_app._get_current_object()

    try:
        filename = gen(app, scan_id)
        return jsonify({
            'message': 'Report generated',
            'file':    filename,
            'scan_id': scan_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@report_bp.route('/reports', methods=['GET'])
def list_reports():
    import os
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        return jsonify([])

    files = []
    for f in os.listdir(reports_dir):
        if f.endswith('.pdf'):
            path = os.path.join(reports_dir, f)
            files.append({
                'filename': f,
                'path':     path,
                'size':     os.path.getsize(path),
                'created':  os.path.getmtime(path),
            })

    files.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(files)