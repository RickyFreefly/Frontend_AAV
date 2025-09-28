from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

API_URL = "http://localhost:3000/api/clientes"  # 👈 backend Express

# =================== LISTAR CLIENTES ===================
@clientes_bp.route("/")
def listar_clientes():
    identificacion = request.args.get("identificacion")  # ✅ Capturar parámetro de búsqueda
    clientes = []

    try:
        if identificacion:
            # Buscar cliente por identificación en backend
            response = requests.get(f"{API_URL}?identificacion={identificacion}")
            if response.status_code == 200:
                clientes = response.json()
                if not clientes:
                    flash("⚠️ No se encontraron clientes con esa identificación", "warning")
            else:
                flash("❌ Error en búsqueda de cliente", "danger")
        else:
            # Listar todos si no hay búsqueda
            response = requests.get(API_URL)
            clientes = response.json()
    except Exception as e:
        flash(f"Error obteniendo clientes: {e}", "danger")

    return render_template("clientes.html", clientes=clientes)


# =================== CREAR CLIENTE ===================
@clientes_bp.route("/crear", methods=["POST"])
def crear_cliente():
    try:
        data = {
            "tipo": request.form.get("tipo"),
            "id_type": request.form.get("id_type"),
            "identificacion": request.form.get("identificacion"),
            "check_digit": request.form.get("check_digit"),
            "nombres": request.form.get("nombres"),
            "apellidos": request.form.get("apellidos"),
            "razonSocial": request.form.get("razonSocial"),
            "direccion": request.form.get("direccion"),
            "country_code": "CO",
            "state_code": request.form.get("state_code"),
            "city_code": request.form.get("city_code"),
            "telefono": request.form.get("telefono"),
            "contact_first_name": request.form.get("contact_first_name"),
            "contact_last_name": request.form.get("contact_last_name"),
            "contact_email": request.form.get("contact_email"),
            "observacion": request.form.get("observacion"),
        }

        r = requests.post(API_URL, json=data)
        if r.status_code == 201:
            flash("✅ Cliente creado con éxito", "success")
        else:
            flash(f"❌ Error creando cliente: {r.json().get('error')}", "danger")

    except Exception as e:
        flash(f"Error en petición: {e}", "danger")

    return redirect(url_for("clientes.listar_clientes"))


# =================== FORMULARIO EDITAR CLIENTE ===================
@clientes_bp.route("/editar/<int:idCliente>")
def editar_cliente_form(idCliente):
    try:
        r = requests.get(f"{API_URL}/{idCliente}")
        if r.status_code == 200:
            cliente = r.json()
        else:
            flash("Cliente no encontrado", "warning")
            return redirect(url_for("clientes.listar_clientes"))
    except Exception as e:
        flash(f"Error obteniendo cliente: {e}", "danger")
        return redirect(url_for("clientes.listar_clientes"))

    return render_template("editar_cliente.html", cliente=cliente)


# =================== ACTUALIZAR CLIENTE ===================
@clientes_bp.route("/actualizar/<int:idCliente>", methods=["POST"])
def actualizar_cliente(idCliente):
    try:
        data = {
            "tipo": request.form.get("tipo"),
            "id_type": request.form.get("id_type"),
            "nombres": request.form.get("nombres"),
            "apellidos": request.form.get("apellidos"),
            "razonsocial": request.form.get("razonSocial"),
            "direccion": request.form.get("direccion"),
            "state_code": request.form.get("state_code"),
            "city_code": request.form.get("city_code"),
            "telefono": request.form.get("telefono"),
            "contact_first_name": request.form.get("contact_first_name"),
            "contact_last_name": request.form.get("contact_last_name"),
            "contact_email": request.form.get("contact_email"),
            "observacion": request.form.get("observacion"),
        }

        r = requests.put(f"{API_URL}/{idCliente}", json=data)
        if r.status_code == 200:
            flash("✅ Cliente actualizado con éxito", "success")
        else:
            flash(f"❌ Error actualizando cliente: {r.json().get('error')}", "danger")

    except Exception as e:
        flash(f"Error en petición: {e}", "danger")

    return redirect(url_for("clientes.listar_clientes"))
