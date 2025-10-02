from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
import config

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

# =================== LISTAR CLIENTES ===================
@clientes_bp.route("/")
def listar_clientes():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    identificacion = request.args.get("identificacion")
    clientes = []

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        url = f"{config.API_URL}/clientes"

        if identificacion:
            response = requests.get(url, headers=headers, params={"identificacion": identificacion})
            if response.status_code == 200:
                clientes = response.json()
                if not clientes:
                    flash("⚠️ No se encontraron clientes con esa identificación", "warning")
            else:
                flash("❌ Error en búsqueda de cliente", "danger")
        else:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                clientes = response.json()
            else:
                flash("❌ Error listando clientes", "danger")

    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return render_template("clientes.html", clientes=clientes)


# =================== CREAR CLIENTE ===================
@clientes_bp.route("/crear", methods=["POST"])
def crear_cliente():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

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

    try:
        headers = {"Authorization": f"Bearer {session['token']}", "Content-Type": "application/json"}
        r = requests.post(f"{config.API_URL}/clientes", headers=headers, json=data)
        if r.status_code == 201:
            flash("✅ Cliente creado con éxito", "success")
        else:
            flash(f"❌ Error creando cliente: {r.json().get('error', 'Error desconocido')}", "danger")
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return redirect(url_for("clientes.listar_clientes"))


# =================== FORMULARIO EDITAR CLIENTE ===================
@clientes_bp.route("/editar/<int:idCliente>")
def editar_cliente_form(idCliente):
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        r = requests.get(f"{config.API_URL}/clientes/{idCliente}", headers=headers)
        if r.status_code == 200:
            cliente = r.json()
        else:
            flash("Cliente no encontrado", "warning")
            return redirect(url_for("clientes.listar_clientes"))
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")
        return redirect(url_for("clientes.listar_clientes"))

    return render_template("editar_cliente.html", cliente=cliente)


# =================== ACTUALIZAR CLIENTE ===================
@clientes_bp.route("/actualizar/<int:idCliente>", methods=["POST"])
def actualizar_cliente(idCliente):
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    data = {
        "tipo": request.form.get("tipo"),
        "id_type": request.form.get("id_type"),
        "nombres": request.form.get("nombres"),
        "apellidos": request.form.get("apellidos"),
        "razonSocial": request.form.get("razonSocial"),
        "direccion": request.form.get("direccion"),
        "state_code": request.form.get("state_code"),
        "city_code": request.form.get("city_code"),
        "telefono": request.form.get("telefono"),
        "contact_first_name": request.form.get("contact_first_name"),
        "contact_last_name": request.form.get("contact_last_name"),
        "contact_email": request.form.get("contact_email"),
        "observacion": request.form.get("observacion"),
    }

    try:
        headers = {"Authorization": f"Bearer {session['token']}", "Content-Type": "application/json"}
        r = requests.put(f"{config.API_URL}/clientes/{idCliente}", headers=headers, json=data)
        if r.status_code == 200:
            flash("✅ Cliente actualizado con éxito", "success")
        else:
            flash(f"❌ Error actualizando cliente: {r.json().get('error', 'Error desconocido')}", "danger")
    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return redirect(url_for("clientes.listar_clientes"))
