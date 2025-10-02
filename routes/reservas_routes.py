from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
import requests
import config

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")

# ================== GET: Listar Reservas ==================
@reservas_bp.route("/", methods=["GET"])
def listar_reservas():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    reservas, medios, productos = [], [], []

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        params = {}
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin

        # ✅ Reservas
        response = requests.get(f"{config.API_URL}/reservas", headers=headers, params=params)
        if response.status_code == 200:
            reservas = response.json()

        # ✅ Medios de pago
        medios_resp = requests.get(f"{config.API_URL}/medios", headers=headers)
        if medios_resp.status_code == 200:
            medios = medios_resp.json()

        # ✅ Productos
        productos_resp = requests.get(f"{config.API_URL}/productos", headers=headers)
        if productos_resp.status_code == 200:
            productos = productos_resp.json()

    except Exception as e:
        flash(f"❌ Error consultando backend: {e}", "danger")

    return render_template(
        "reservas.html",
        reservas=reservas,
        medios=medios,
        productos=productos,
        request=request
    )


# ================== POST: Crear Reserva ==================
@reservas_bp.route("/crear", methods=["POST"])
def crear_reserva():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}", "Content-Type": "application/json"}
        idcliente = request.form.get("idcliente")
        identificacion = request.form.get("identificacion")

        if not idcliente:
            # fallback: buscar por identificación
            cliente_resp = requests.get(f"{config.API_URL}/clientes", headers=headers, params={"identificacion": identificacion})
            cliente_data = cliente_resp.json()
            if not cliente_data:
                flash("⚠️ Cliente no encontrado", "warning")
                return redirect(url_for("reservas.listar_reservas"))
            idcliente = cliente_data[0]["idcliente"]

        data = {
            "idcliente": idcliente,
            "idproducto": request.form["idproducto"],
            "valorreserva": request.form["valor"],
            "idmedio": request.form["idmedio"],
            "idusuario": 1,  # 👉 luego puedes usar session["idusuario"]
            "observaciones": request.form.get("observaciones", "")
        }

        response = requests.post(f"{config.API_URL}/reservas", headers=headers, json=data)
        if response.status_code in [200, 201]:
            flash("Reserva creada ✅", "success")
        else:
            flash("Error creando reserva ❌", "danger")

    except Exception as e:
        flash(f"❌ Error creando reserva: {e}", "danger")

    return redirect(url_for("reservas.listar_reservas"))


# ================== GET: Buscar clientes (proxy) ==================
@reservas_bp.route("/clientes", methods=["GET"])
def buscar_clientes():
    if "token" not in session:
        return jsonify([]), 401

    identificacion = request.args.get("identificacion", "")
    clientes = []
    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        params = {}
        if identificacion:
            params["identificacion"] = identificacion
        resp = requests.get(f"{config.API_URL}/clientes", headers=headers, params=params)
        if resp.status_code == 200:
            clientes = resp.json()
    except Exception as e:
        print("❌ Error consultando backend clientes:", e)

    return jsonify(clientes)
