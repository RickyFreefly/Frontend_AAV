from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import requests
import config

facturas_bp = Blueprint("facturas", __name__)

# ================== LISTAR FACTURAS ==================
@facturas_bp.route("/facturas")
def listar_facturas():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.get(f"{config.API_URL}/facturas", headers=headers)

        if response.status_code == 200:
            facturas = response.json()
            return render_template("facturas.html", facturas=facturas)
        else:
            flash("Error al obtener facturas ❌", "danger")
            return redirect(url_for("dashboard.index"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("dashboard.index"))


# ================== CREAR FACTURA ==================
@facturas_bp.route("/facturas/nueva", methods=["GET", "POST"])
def crear_factura():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        data = {
            "idcliente": request.form["idcliente"],
            "idusuario": 1,  # ⚠️ opcionalmente usar session["idusuario"]
            "observaciones": request.form.get("observaciones"),
            "detalles": [],
            "pagos": []
        }

        # Procesar detalles dinámicos
        for key in request.form:
            if key.startswith("detalles["):
                # ejemplo: detalles[0][idproducto]
                parts = key.split("[")
                index = int(parts[1].replace("]", ""))
                field = parts[2].replace("]", "")
                while len(data["detalles"]) <= index:
                    data["detalles"].append({})
                data["detalles"][index][field] = request.form[key]

        # Procesar pagos dinámicos
        for key in request.form:
            if key.startswith("pagos["):
                parts = key.split("[")
                index = int(parts[1].replace("]", ""))
                field = parts[2].replace("]", "")
                while len(data["pagos"]) <= index:
                    data["pagos"].append({})
                data["pagos"][index][field] = request.form[key]

        try:
            headers = {
                "Authorization": f"Bearer {session['token']}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{config.API_URL}/facturas", headers=headers, json=data)

            if response.status_code in [200, 201]:
                flash("Factura creada ✅", "success")
                return redirect(url_for("facturas.listar_facturas"))
            else:
                flash("Error al crear factura ❌", "danger")
        except Exception as e:
            flash(f"Error conectando al backend: {e}", "danger")

    return render_template("crear_factura.html")


# ================== DETALLE FACTURA ==================
@facturas_bp.route("/facturas/<int:id>")
def detalle_factura(id):
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        response = requests.get(f"{config.API_URL}/facturas/{id}", headers=headers)

        if response.status_code == 200:
            factura = response.json()
            return render_template("detalle_factura.html", factura=factura)
        else:
            flash("Factura no encontrada ❌", "danger")
            return redirect(url_for("facturas.listar_facturas"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("facturas.listar_facturas"))
