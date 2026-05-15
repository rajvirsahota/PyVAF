from flask import Blueprint, jsonify
from models.scan import Scan
from models.finding import Finding

results_bp = Blueprint('results', __name__)

@results_bp.route('/results/<int:scan_id>', methods=['GET'])
def get_results(scan_id):
    scan     = Scan.query.get_or_404(scan_id)
    findings = Finding.query.filter_by(scan_id=scan_id).all()
    return jsonify({
        'scan':     scan.to_dict(),
        'findings': [f.to_dict() for f in findings],
        'summary': {
            'critical': sum(1 for f in findings if f.severity == 'Critical'),
            'high':     sum(1 for f in findings if f.severity == 'High'),
            'medium':   sum(1 for f in findings if f.severity == 'Medium'),
            'low':      sum(1 for f in findings if f.severity == 'Low'),
            'info':     sum(1 for f in findings if f.severity == 'Info'),
        }
    })