from models.finding import Finding
from models.scan import Scan
from models.database import db

def analyze_scan(app, scan_id: int) -> dict:
    """Deduplicate findings, calculate risk score, return summary."""
    with app.app_context():
        findings = Finding.query.filter_by(scan_id=scan_id).all()

        if not findings:
            return {'total': 0, 'risk_score': 0, 'summary': {}}

        # Deduplicate by title
        seen_titles = set()
        duplicates  = []

        for f in findings:
            if f.title in seen_titles:
                duplicates.append(f.id)
            else:
                seen_titles.add(f.title)

        # Remove duplicates from DB
        if duplicates:
            Finding.query.filter(
                Finding.id.in_(duplicates)).delete(
                synchronize_session=False)
            db.session.commit()
            findings = Finding.query.filter_by(scan_id=scan_id).all()

        # Count by severity
        summary = {
            'Critical': 0, 'High': 0,
            'Medium':   0, 'Low':  0, 'Info': 0
        }
        for f in findings:
            if f.severity in summary:
                summary[f.severity] += 1

        # Calculate overall risk score (weighted)
        weights = {
            'Critical': 10.0, 'High': 7.0,
            'Medium':   4.0,  'Low':  1.0, 'Info': 0.0
        }
        total_weight = sum(
            weights.get(f.severity, 0) for f in findings)
        max_possible = len(findings) * 10.0
        risk_score   = round(
            (total_weight / max_possible) * 10, 1
        ) if max_possible > 0 else 0.0

        # Risk label
        if risk_score >= 8:
            risk_label = 'Critical Risk'
        elif risk_score >= 6:
            risk_label = 'High Risk'
        elif risk_score >= 4:
            risk_label = 'Medium Risk'
        elif risk_score >= 2:
            risk_label = 'Low Risk'
        else:
            risk_label = 'Minimal Risk'

        # Update scan record
        scan = Scan.query.get(scan_id)
        if scan:
            scan.status = 'complete'
            db.session.commit()

        return {
            'total':      len(findings),
            'risk_score': risk_score,
            'risk_label': risk_label,
            'summary':    summary,
            'duplicates_removed': len(duplicates),
        }


def get_global_stats(app) -> dict:
    """Get overall stats across all scans for the dashboard."""
    with app.app_context():
        total_scans    = Scan.query.count()
        complete_scans = Scan.query.filter_by(status='complete').count()
        total_findings = Finding.query.count()

        critical = Finding.query.filter_by(severity='Critical').count()
        high     = Finding.query.filter_by(severity='High').count()
        medium   = Finding.query.filter_by(severity='Medium').count()
        low      = Finding.query.filter_by(severity='Low').count()

        return {
            'total_scans':    total_scans,
            'complete_scans': complete_scans,
            'total_findings': total_findings,
            'critical':       critical,
            'high':           high,
            'medium':         medium,
            'low':            low,
        }