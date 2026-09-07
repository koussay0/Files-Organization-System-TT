from flask import Blueprint, redirect, request, session, url_for, render_template, flash, current_app

bp = Blueprint("main", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        allowed_users = current_app.config.get("ALLOWED_USERS", {})

        if username in allowed_users and allowed_users[username] == password:
            session["authenticated"] = True
            session["username"] = username
            flash("Connexion réussie.", "success")
            return redirect(url_for("main.index"))

        flash("Nom d'utilisateur ou mot de passe invalide.", "danger")

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("main.login"))


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in {"en", "fr"}:
        session["lang"] = lang
    return redirect(request.referrer or url_for("main.index"))
