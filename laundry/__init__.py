"""Laundry Tracker — aplikasi web pencatat & pelacak order laundry."""
import os

from flask import Flask

from . import db
from .routes import bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-ganti-di-produksi"),
        DATABASE=os.path.join(app.instance_path, "laundry.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(bp)

    @app.template_filter("rupiah")
    def rupiah(value: int | float) -> str:
        return "Rp" + f"{int(value):,}".replace(",", ".")

    return app
