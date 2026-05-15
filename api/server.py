from flask import Flask
from models.database import init_db
from api.routes.status import status_bp
from api.routes.scan import scan_bp
from api.routes.results import results_bp
from api.routes.report import report_bp

def create_app():
    app = Flask(__name__)

    # Register all blueprints
    app.register_blueprint(status_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(report_bp)

    # Init database
    init_db(app)

    return app