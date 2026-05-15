from flask import Blueprint, jsonify, request, current_app
from models.database import db
from models.scan import Scan
import threading

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/scan', methods=['POST'])
def start_scan():
    from core.scanner import run_scan

    data    = request.get_json()
    target  = data.get('target', '').strip()
    modules = data.get('modules', ['port', 'web', 'ssl'])

    if not target:
        return jsonify({'error': 'Target is required'}), 400

    scan = Scan(target=target, status='pending',
                modules=','.join(modules))
    db.session.add(scan)
    db.session.commit()

    # Run scan in background thread
    app = current_app._get_current_object()
    t = threading.Thread(
        target=run_scan,
        args=(app, scan.id),
        daemon=True
    )
    t.start()

    return jsonify({'message': 'Scan started', 'scan': scan.to_dict()}), 201


@scan_bp.route('/scan/<int:scan_id>', methods=['GET'])
def get_scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    return jsonify(scan.to_dict())


@scan_bp.route('/scans', methods=['GET'])
def list_scans():
    scans = Scan.query.order_by(Scan.started_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])