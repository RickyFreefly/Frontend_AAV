from flask import Blueprint, render_template, session, redirect, url_for, flash

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():
    if "token" in session:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))

@dashboard_bp.route("/dashboard")
def index():
    if "token" not in session:
        flash("Primero inicia sesión", "warning")
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", username=session["username"])
