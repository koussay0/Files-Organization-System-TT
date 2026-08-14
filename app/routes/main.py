from flask import Blueprint, redirect, request, session, url_for, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in {"en", "fr"}:
        session["lang"] = lang
    return redirect(request.referrer or url_for("main.index"))
