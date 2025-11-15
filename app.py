from flask import Flask, render_template
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from config import Development, Production
from filters import register_template_filters
from models import db
from routes import register_blueprints
from utils import limiter

import logging
import os

load_dotenv()

jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    env = os.getenv('FLASK_ENV', 'development')
    config_class = Development if env == 'development' else Production
    app.config.from_object(config_class)

    db.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    CORS(
        app,
        resources={
            r"/api/*": {"origins": "*"},
            r"/client": {"origins": "*"},
            r"/test_session": {"origins": "*"},
        },
        supports_credentials=True,
    )

    _configure_logging(app)
    register_template_filters(app)
    register_blueprints(app)
    _register_error_handlers(app)

    return app


def _configure_logging(app):
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=os.path.join(log_dir, 'admin_access.log'),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return render_template('404.html'), 404


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
