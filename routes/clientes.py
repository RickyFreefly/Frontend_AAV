from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
import config

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

# =================== LISTAR CLIENTES (con paginación) ===================
@clientes_bp.route("/")
def listar_clientes():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    identificacion = request.args.get("identificacion")
    page = int(request.args.get("page", 1))
    per_page = 10
    clientes = []

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        url = f"{config.API_URL}/clientes"

        params = {"identificacion": identificacion} if identificacion else {}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            clientes = response.json()
            if identificacion and not clientes:
                flash("⚠️ No se encontraron clientes con esa identificación", "warning")
        else:
            flash("❌ Error obteniendo lista de clientes", "danger")

    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    total = len(clientes)
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    clientes_paginados = clientes[offset:offset + per_page]

    return render_template(
        "clientes.html",
        clientes=clientes_paginados,
        page=page,
        total_pages=total_pages,
    )

# =================== CREAR CLIENTE ===================
@clientes_bp.route("/crear", methods=["POST"])
def crear_cliente():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    # 🔠 Conversión segura a mayúsculas
    tipo = (request.form.get("tipo") or "").upper()
    id_type = request.form.get("id_type")
    identificacion = request.form.get("identificacion")
    check_digit = request.form.get("check_digit")
    nombres = (request.form.get("nombres") or "").upper()
    apellidos = (request.form.get("apellidos") or "").upper()
    razonsocial = (request.form.get("razonSocial") or "").upper()
    direccion = (request.form.get("direccion") or "").upper()
    telefono = request.form.get("telefono")
    contact_email = request.form.get("contact_email")
    observacion = (request.form.get("observacion") or "").upper()
    state_code = request.form.get("state_code")
    city_code = request.form.get("city_code")

    data = {
        "tipo": tipo,
        "id_type": id_type,
        "identificacion": identificacion,
        "check_digit": check_digit,
        "nombres": nombres,
        "apellidos": apellidos,
        "razonsocial": razonsocial,  # ⚠️ corregido (antes "razonSocial")
        "direccion": direccion,
        "country_code": "CO",
        "state_code": state_code,
        "city_code": city_code,
        "telefono": telefono,
        "contact_email": contact_email,
        "observacion": observacion,
    }

    try:
        headers = {
            "Authorization": f"Bearer {session['token']}",
            "Content-Type": "application/json",
        }
        r = requests.post(f"{config.API_URL}/clientes", headers=headers, json=data)

        if r.status_code == 201:
            flash("✅ Cliente creado con éxito", "success")
        else:
            try:
                err_msg = r.json().get("error", "Error desconocido")
            except Exception:
                err_msg = r.text
            flash(f"❌ Error creando cliente: {err_msg}", "danger")

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
        "tipo": (request.form.get("tipo") or "").upper(),
        "id_type": request.form.get("id_type"),
        "nombres": (request.form.get("nombres") or "").upper(),
        "apellidos": (request.form.get("apellidos") or "").upper(),
        "razonsocial": (request.form.get("razonSocial") or "").upper(),
        "direccion": (request.form.get("direccion") or "").upper(),
        "state_code": request.form.get("state_code"),
        "city_code": request.form.get("city_code"),
        "telefono": request.form.get("telefono"),
        "contact_email": request.form.get("contact_email"),
        "observacion": (request.form.get("observacion") or "").upper(),
    }

    try:
        headers = {
            "Authorization": f"Bearer {session['token']}",
            "Content-Type": "application/json",
        }
        r = requests.put(f"{config.API_URL}/clientes/{idCliente}", headers=headers, json=data)

        if r.status_code == 200:
            flash("✅ Cliente actualizado con éxito", "success")
        else:
            try:
                err_msg = r.json().get("error", "Error desconocido")
            except Exception:
                err_msg = r.text
            flash(f"❌ Error actualizando cliente: {err_msg}", "danger")

    except Exception as e:
        flash(f"Error conectando al backend: {e}", "danger")

    return redirect(url_for("clientes.listar_clientes"))
