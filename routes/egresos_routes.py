from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import requests
import config
from datetime import datetime

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
            # ✅ Fecha actual para mostrar en el formulario (readonly)
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            return render_template("egresos.html", egresos=egresos, fecha_actual=fecha_actual)
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

    # ✅ Generar fecha automáticamente
    fecha_actual = datetime.now().strftime("%Y-%m-%d")

    data = {
        "fecha": fecha_actual,
        "concepto": request.form["concepto"],
        "proveedor": request.form["proveedor"],
        "valor": request.form["valor"],
        "metodopago": request.form["metodopago"],
        "observacion": request.form.get("observacion", ""),
        "estado": "PAGADO",  # Estado fijo
        "idusuario": 5  # ⚙️ Ajustar si tienes session["idusuario"]
    }

    try:
        headers = {
            "Authorization": f"Bearer {session['token']}",
            "Content-Type": "application/json"
        }
        response = requests.post(f"{config.API_URL}/egresos", headers=headers, json=data)

        if response.status_code in (200, 201):
            flash("✅ Egreso creado correctamente (estado: PAGADO)", "success")
        else:
            flash("❌ Error al crear egreso", "danger")
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return redirect(url_for("egresos.listar_egresos"))


# ================== DETALLE DE EGRESO ==================
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
            flash("❌ Egreso no encontrado", "danger")
            return redirect(url_for("egresos.listar_egresos"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("egresos.listar_egresos"))
