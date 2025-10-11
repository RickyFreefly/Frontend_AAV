from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
import requests
import config

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")


# ================== GET: Formulario Crear Reserva ==================
@reservas_bp.route("/crear", methods=["GET"])
def crear_reserva_form():
    """
    Muestra el formulario para crear una reserva.
    Puede recibir ?idCliente=xx&identificacion=xxxx desde el listado de clientes.
    """
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    id_cliente = request.args.get("idCliente")
    identificacion = request.args.get("identificacion")

    cliente = None
    productos, medios = [], []

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}

        # 🔹 Buscar datos del cliente si se pasó idCliente
        if id_cliente:
            r_cliente = requests.get(f"{config.API_URL}/clientes/{id_cliente}", headers=headers)
            if r_cliente.status_code == 200:
                cliente = r_cliente.json()

        # 🔹 Productos y medios de pago
        r_prod = requests.get(f"{config.API_URL}/productos", headers=headers)
        if r_prod.status_code == 200:
            productos = r_prod.json()

        r_medios = requests.get(f"{config.API_URL}/medios", headers=headers)
        if r_medios.status_code == 200:
            medios = r_medios.json()

    except Exception as e:
        flash(f"❌ Error conectando al backend: {e}", "danger")

    # 🔹 Renderiza el mismo template general (reservas.html)
    return render_template(
        "reservas.html",
        cliente=cliente,
        idCliente=id_cliente,
        identificacion=identificacion,
        productos=productos,
        medios=medios,
        reservas=[],          # para evitar errores en el bloque de listado
        total_pages=1,
        page=1,
        request=request
    )


# ================== GET: Listar Reservas ==================
@reservas_bp.route("/", methods=["GET"])
def listar_reservas():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    page = int(request.args.get("page", 1))
    per_page = 10

    reservas, medios, productos = [], [], []
    total_pages = 1

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        params = {}
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin

        # 🔹 Reservas
        resp = requests.get(f"{config.API_URL}/reservas", headers=headers, params=params)
        if resp.status_code == 200:
            reservas = resp.json()

        # 🔹 Paginación local
        total = len(reservas)
        start = (page - 1) * per_page
        end = start + per_page
        reservas_pag = reservas[start:end]
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        # 🔹 Catálogos
        medios_resp = requests.get(f"{config.API_URL}/medios", headers=headers)
        if medios_resp.status_code == 200:
            medios = medios_resp.json()

        productos_resp = requests.get(f"{config.API_URL}/productos", headers=headers)
        if productos_resp.status_code == 200:
            productos = productos_resp.json()

    except Exception as e:
        flash(f"❌ Error consultando backend: {e}", "danger")

    return render_template(
        "reservas.html",
        reservas=reservas_pag,
        medios=medios,
        productos=productos,
        request=request,
        page=page,
        total_pages=total_pages
    )


# ================== POST: Crear Reserva ==================
@reservas_bp.route("/crear", methods=["POST"])
def crear_reserva():
    """
    Envía la reserva al backend API.
    Si el idcliente no se envía, busca por identificación.
    """
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {
            "Authorization": f"Bearer {session['token']}",
            "Content-Type": "application/json"
        }

        idcliente = request.form.get("idCliente") or request.form.get("idcliente")
        identificacion = request.form.get("identificacion")

        # 🔸 Si no hay idCliente, buscar por identificación
        if not idcliente and identificacion:
            cliente_resp = requests.get(
                f"{config.API_URL}/clientes",
                headers=headers,
                params={"identificacion": identificacion}
            )
            cliente_data = cliente_resp.json()
            if not cliente_data:
                flash("⚠️ Cliente no encontrado", "warning")
                return redirect(url_for("reservas.listar_reservas"))
            idcliente = cliente_data[0]["idcliente"]

        # 🔹 Datos del formulario
        data = {
            "idcliente": idcliente,
            "idproducto": request.form["idproducto"],
            "valorreserva": request.form["valor"],
            "idmedio": request.form["idmedio"],
            "idusuario": session.get("idusuario", 1),
            "observaciones": request.form.get("observaciones", "")
        }

        # 🔹 Enviar a la API
        resp = requests.post(f"{config.API_URL}/reservas", headers=headers, json=data)
        if resp.status_code in [200, 201]:
            flash("✅ Reserva creada correctamente", "success")
        else:
            flash(f"❌ Error creando reserva: {resp.text}", "danger")

    except Exception as e:
        flash(f"❌ Error enviando reserva: {e}", "danger")

    return redirect(url_for("reservas.listar_reservas"))


# ================== GET: Proxy Buscar Clientes ==================
@reservas_bp.route("/clientes", methods=["GET"])
def buscar_clientes():
    """
    Proxy para buscar clientes desde el formulario de reservas (por identificación)
    """
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
