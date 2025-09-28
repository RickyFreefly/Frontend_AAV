from flask import Blueprint, render_template, session, redirect, url_for, flash
import requests
import config

usuarios_bp = Blueprint("usuarios", __name__)

@usuarios_bp.route("/usuarios")
def listar_usuarios():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.get(f"{config.API_URL}/usuarios", headers=headers)

        if response.status_code == 200:
            usuarios = response.json()
            return render_template("usuarios.html", usuarios=usuarios)
        else:
            flash("Error al obtener usuarios", "danger")
            return redirect(url_for("dashboard.index"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("dashboard.index"))
