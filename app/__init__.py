import os
from flask import Flask, redirect, request, session, url_for, get_flashed_messages


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        OUTPUT_FOLDER=os.path.join(app.instance_path, "outputs"),
        MAX_CONTENT_LENGTH=None,
        ALLOWED_USERS={
            "admin": "admin123",
            # Replace these values with your real app credentials.
            # Example: "username": "password"
        },
    )

    translations = {
        "en": {
            "app_name": "TT File Processor",
            "tagline": "File clean-up, comparison, merge and export tools in one modern dashboard.",
            "home": "Home",
            "single_file": "Single File",
            "compare_files": "Compare Files",
            "merge_files": "Merge Files",
            "dashboard_title": "Data Cleaning & File Processing",
            "dashboard_subtitle": "Organized tools for processing, comparing and preparing files for reporting.",
            "single_file_card": "Single File",
            "compare_card": "File Comparison",
            "merge_card": "Merge Files",
            "single_file_desc": "Upload a file and process it with sorting, duplicate cleanup, template export, and column transformations.",
            "compare_desc": "Compare two files by row or column and export differences or matching records in multiple formats.",
            "merge_desc": "Select columns from both inputs and combine them into a single result, ready to export.",
            "start": "Start",
            "compare": "Compare",
            "merge": "Merge",
            "whats_new": "What’s new",
            "feature_1": "PDF input support + Excel/Text/CSV upload",
            "feature_2": "Custom template generation and export",
            "feature_3": "Split large files into multiple output files",
            "feature_4": "Modern dashboard layout and improved color theme",
            "footer": "Tunisie Telecom File Processor © 2026 · Built for data cleaning and reporting",
            "language": "Language",
        },
        "fr": {
            "app_name": "TT File Processor",
            "tagline": "Outils de nettoyage, comparaison, fusion et exportation de fichiers dans un tableau de bord moderne.",
            "home": "Accueil",
            "single_file": "Fichier unique",
            "compare_files": "Comparer les fichiers",
            "merge_files": "Fusionner les fichiers",
            "dashboard_title": "Nettoyage de données & traitement de fichiers",
            "dashboard_subtitle": "Des outils organisés pour traiter, comparer et préparer des fichiers pour les rapports.",
            "single_file_card": "Fichier unique",
            "compare_card": "Comparaison de fichiers",
            "merge_card": "Fusion de fichiers",
            "single_file_desc": "Téléchargez un fichier et traitez-le avec tri, suppression des doublons, modèles et transformations de colonnes.",
            "compare_desc": "Comparez deux fichiers par ligne ou par colonne et exportez les différences ou les correspondances.",
            "merge_desc": "Sélectionnez les colonnes des deux fichiers et combinez-les dans un seul résultat prêt à exporter.",
            "start": "Démarrer",
            "compare": "Comparer",
            "merge": "Fusionner",
            "whats_new": "Nouveautés",
            "feature_1": "Support PDF + téléchargement CSV/TXT/Excel",
            "feature_2": "Génération et export de modèles personnalisés",
            "feature_3": "Division des gros fichiers en plusieurs sorties",
            "feature_4": "Mise en page moderne et thème coloré amélioré",
            "footer": "Tunisie Telecom File Processor © 2026 · Conçu pour le nettoyage et le reporting de données",
            "language": "Langue",
        },
    }

    @app.before_request
    def set_language():
        lang = request.args.get("lang") or session.get("lang") or "en"
        if lang not in translations:
            lang = "en"
        session["lang"] = lang

    @app.before_request
    def require_login():
        open_routes = {"main.login", "static", "main.set_language"}
        if request.endpoint in open_routes:
            return None
        if not session.get("authenticated"):
            return redirect(url_for("main.login"))

    @app.context_processor
    def inject_language():
        lang = session.get("lang", "en")
        return {
            "current_lang": lang,
            "translations": translations[lang],
            "lang_options": [
                {"code": "en", "label": "EN"},
                {"code": "fr", "label": "FR"},
            ],
            "flash_messages": [
                {"category": category, "message": message}
                for category, message in get_flashed_messages(with_categories=True)
            ],
        }

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


app = create_app()
