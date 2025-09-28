from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import requests
import config

egresos_bp = Blueprint("egresos", __name__)

# ================== LISTAR EGRESOS ==================
@egresos_bp.route("/egresos")
def listar_egresos():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.get(f"{config.API_URL}/egresos", headers=headers)

        if response.status_code == 200:
            egresos = response.json()
            return render_template("egresos.html", egresos=egresos)
        else:
            flash("Error al obtener egresos", "danger")
            return redirect(url_for("dashboard.index"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("dashboard.index"))

# ================== CREAR EGRESO ==================
@egresos_bp.route("/egresos/nuevo", methods=["POST"])
def crear_egreso():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    data = {
        "fecha": request.form["fecha"],
        "concepto": request.form["concepto"],
        "proveedor": request.form["proveedor"],
        "valor": request.form["valor"],
        "metodopago": request.form["metodopago"],
        "observacion": request.form.get("observacion"),
        "idusuario": 1  # ⚠️ Aquí podrías usar session["idusuario"] si lo guardas en login
    }

    try:
        headers = {"Authorization": f"Bearer {session['token']}", "Content-Type": "application/json"}
        response = requests.post(f"{config.API_URL}/egresos", headers=headers, json=data)

        if response.status_code == 200 or response.status_code == 201:
            flash("Egreso creado ✅", "success")
        else:
            flash("Error al crear egreso ❌", "danger")
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return redirect(url_for("egresos.listar_egresos"))

# ================== OBTENER EGRESO POR ID ==================
@egresos_bp.route("/egresos/<int:id>")
def detalle_egreso(id):
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.get(f"{config.API_URL}/egresos/{id}", headers=headers)

        if response.status_code == 200:
            egreso = response.json()
            return render_template("egreso_detalle.html", egreso=egreso)
        else:
            flash("Egreso no encontrado ❌", "danger")
            return redirect(url_for("egresos.listar_egresos"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("egresos.listar_egresos"))

# ================== ACTUALIZAR ESTADO ==================
@egresos_bp.route("/egresos/<int:id>/estado", methods=["POST"])
def actualizar_estado(id):
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    estado = request.form["estado"]

    try:
        headers = {"Authorization": f"Bearer {session['token']}", "Content-Type": "application/json"}
        response = requests.patch(f"{config.API_URL}/egresos/{id}/estado", headers=headers, json={"estado": estado})

        if response.status_code == 200:
            flash("Estado actualizado ✅", "success")
        else:
            flash("Error al actualizar estado ❌", "danger")
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return redirect(url_for("egresos.listar_egresos"))
