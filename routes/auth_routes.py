from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import requests
import config

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            response = requests.post(f"{config.API_URL}/auth/login", json={
                "username": username,
                "password": password
            })

            if response.status_code == 200 and response.json().get("success"):
                session["token"] = response.json()["token"]
                session["username"] = username
                flash("Login exitoso ✅", "success")
                return redirect(url_for("dashboard.index"))
            else:
                flash("Credenciales inválidas ❌", "danger")

        except Exception as e:
            flash(f"Error conectando al backend: {e}", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada 👋", "info")
    return redirect(url_for("auth.login"))
