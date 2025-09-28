from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import requests

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")

API_URL = "http://localhost:3000/api/reservas"
API_CLIENTES = "http://localhost:3000/api/clientes"
API_MEDIOS = "http://localhost:3000/api/medios"
API_PRODUCTOS = "http://localhost:3000/api/productos"

# ================== GET: Listar Reservas ==================
@reservas_bp.route("/", methods=["GET"])
def listar_reservas():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    reservas = []
    try:
        params = {}
        if fecha_inicio:
            params["fecha_inicio"] = fecha_inicio
        if fecha_fin:
            params["fecha_fin"] = fecha_fin

        response = requests.get(API_URL, params=params)
        reservas = response.json()
    except Exception as e:
        print("❌ Error consultando backend reservas:", e)

    # Medios de pago y productos
    medios, productos = [], []
    try:
        medios = requests.get(API_MEDIOS).json()
    except Exception as e:
        print("❌ Error consultando backend medios:", e)
    try:
        productos = requests.get(API_PRODUCTOS).json()
    except Exception as e:
        print("❌ Error consultando backend productos:", e)

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
    try:
        idcliente = request.form.get("idcliente")  # capturamos hidden
        identificacion = request.form.get("identificacion")

        if not idcliente:
            # fallback: buscar por identificación si hidden no se llenó
            cliente_resp = requests.get(API_CLIENTES, params={"identificacion": identificacion})
            cliente_data = cliente_resp.json()

            if not cliente_data or len(cliente_data) == 0:
                print("⚠️ Cliente no encontrado")
                return redirect(url_for("reservas.listar_reservas"))

            idcliente = cliente_data[0]["idcliente"]

        # 👉 Crear reserva con idcliente
        data = {
            "idcliente": idcliente,
            "idproducto": request.form["idproducto"],
            "valorreserva": request.form["valor"],
            "idmedio": request.form["idmedio"],
            "idusuario": 1,
            "observaciones": ""
        }
        requests.post(API_URL, json=data)
    except Exception as e:
        print("❌ Error creando reserva:", e)

    return redirect(url_for("reservas.listar_reservas"))

# ================== GET: Buscar clientes (proxy) ==================
@reservas_bp.route("/clientes", methods=["GET"])
def buscar_clientes():
    identificacion = request.args.get("identificacion", "")
    clientes = []
    try:
        params = {}
        if identificacion:
            params["identificacion"] = identificacion
        resp = requests.get(API_CLIENTES, params=params)
        if resp.status_code == 200:
            clientes = resp.json()
    except Exception as e:
        print("❌ Error consultando backend clientes:", e)

    return jsonify(clientes)
