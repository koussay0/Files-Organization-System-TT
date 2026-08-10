import os
from flask import Flask, redirect, url_for


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        OUTPUT_FOLDER=os.path.join(app.instance_path, "outputs"),
        MAX_CONTENT_LENGTH=1024 * 1024 * 1024,  # 1 GB upload cap
    )

    @app.route('/favicon.ico')
    def favicon():
        return redirect(url_for('static', filename='favicon.svg'))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    from .routes.main import bp as main_bp
    from .routes.single_file import bp as single_file_bp
    from .routes.multi_file import bp as multi_file_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(single_file_bp, url_prefix="/single-file")
    app.register_blueprint(multi_file_bp, url_prefix="/two-files")

    return app
