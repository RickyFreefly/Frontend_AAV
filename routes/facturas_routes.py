from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import requests
import config
from datetime import datetime

facturas_bp = Blueprint("facturas", __name__, url_prefix="/facturas")

# =========================================================
# 🧾 FORMULARIO CREAR FACTURA (MANUAL o DESDE RESERVA)
# =========================================================
@facturas_bp.route("/crear", methods=["GET"])
def crear_factura_form():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    id_cliente = request.args.get("idCliente")
    identificacion = request.args.get("identificacion")
    id_reserva = request.args.get("idReserva")

    cliente = None
    reserva = None
    productos, medios = [], []

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}

        # =========================================================
        # 🔹 Buscar reserva (por identificación o idReserva)
        # =========================================================
        r_reserva = None

        if identificacion:
            # ✅ Buscar por identificación (endpoint completo que trae abono)
            r_reserva = requests.get(f"{config.API_URL}/reservas/cliente/{identificacion}", headers=headers)

        elif id_reserva:
            # ✅ Buscar primero por ID para obtener datos base
            r_simple = requests.get(f"{config.API_URL}/reservas/{id_reserva}", headers=headers)
            identificacion_cliente = None

            if r_simple.status_code == 200:
                r_data = r_simple.json()
                print("DEBUG -> Reserva por ID:", r_data)

                # Intentar obtener identificación directamente
                identificacion_cliente = (
                    r_data.get("identificacion")
                    or r_data.get("identification")
                    or r_data.get("cliente_identificacion")
                )

                # 🧩 Si no tiene identificación, intentar obtenerla del cliente
                if not identificacion_cliente and r_data.get("idcliente"):
                    id_cliente_tmp = r_data.get("idcliente")
                    print(f"DEBUG -> Buscando identificación del cliente {id_cliente_tmp}")
                    r_cliente_tmp = requests.get(f"{config.API_URL}/clientes/{id_cliente_tmp}", headers=headers)
                    if r_cliente_tmp.status_code == 200:
                        c_data = r_cliente_tmp.json()
                        identificacion_cliente = (
                            c_data.get("identificacion")
                            or c_data.get("identification")
                            or c_data.get("numero_documento")
                        )
                        print(f"DEBUG -> Identificación encontrada desde cliente: {identificacion_cliente}")

            # 🔁 Si logramos obtener la identificación, hacemos la búsqueda completa (que trae abono)
            if identificacion_cliente:
                print(f"DEBUG -> Consultando reserva completa para identificación {identificacion_cliente}")
                r_reserva = requests.get(f"{config.API_URL}/reservas/cliente/{identificacion_cliente}", headers=headers)
            else:
                print("⚠️ No se encontró identificación del cliente. Usando respuesta simple sin abono.")
                r_reserva = r_simple

        # =========================================================
        # 🔹 Procesar reserva obtenida
        # =========================================================
        if r_reserva and r_reserva.status_code == 200:
            data = r_reserva.json()
            print("DEBUG -> Reserva obtenida:", data)

            if isinstance(data, list) and len(data) > 0:
                reserva = data[0]
            elif isinstance(data, dict):
                reserva = data

            if reserva:
                # ============================
                # 🧩 Normalización de campos
                # ============================
                def to_float(val):
                    try:
                        return float(val) if val not in [None, "", "null"] else 0.0
                    except (ValueError, TypeError):
                        return 0.0

                reserva["nombre_cliente"] = (
                    reserva.get("nombre_cliente")
                    or reserva.get("cliente")
                    or "Cliente no especificado"
                )

                reserva["precio"] = to_float(
                    reserva.get("precio")
                    or reserva.get("valor")
                    or reserva.get("total")
                )

                reserva["abono"] = to_float(
                    reserva.get("abono")
                    or reserva.get("pago")
                    or reserva.get("valor_abonado")
                    or reserva.get("valorreserva")
                )

                reserva["producto"] = reserva.get("producto") or reserva.get("nombre_producto") or "Producto sin nombre"
                reserva["medio"] = reserva.get("medio") or reserva.get("nombre_medio") or "Sin medio"

                reserva["idcliente"] = reserva.get("idcliente")
                reserva["idmedio"] = reserva.get("idmedio")
                reserva["idproducto"] = reserva.get("idproducto")

                # Campos auxiliares
                reserva["total"] = reserva["precio"]
                reserva["cantidad"] = 1
                reserva["precio_formateado"] = f"{reserva['precio']:,.2f}"
                reserva["abono_formateado"] = f"{reserva['abono']:,.2f}"

                id_cliente = reserva.get("idcliente")
                identificacion = reserva.get("identificacion")

        # =========================================================
        # 🔹 Obtener información del cliente
        # =========================================================
        if id_cliente:
            r_cliente = requests.get(f"{config.API_URL}/clientes/{id_cliente}", headers=headers)
            if r_cliente.status_code == 200:
                cliente = r_cliente.json()

        # =========================================================
        # 🔹 Cargar catálogos de productos y medios de pago
        # =========================================================
        r_prod = requests.get(f"{config.API_URL}/productos", headers=headers)
        if r_prod.status_code == 200:
            productos = r_prod.json()

        r_medios = requests.get(f"{config.API_URL}/medios", headers=headers)
        if r_medios.status_code == 200:
            medios = r_medios.json()

    except Exception as e:
        flash(f"❌ Error conectando al backend: {e}", "danger")

    return render_template(
        "crear_factura.html",
        cliente=cliente,
        reserva=reserva,
        idCliente=id_cliente,
        idReserva=id_reserva,
        identificacion=identificacion,
        productos=productos,
        medios=medios,
        datetime=datetime,
    )


# =========================================================
# 📜 LISTAR FACTURAS (con paginación)
# =========================================================
@facturas_bp.route("/", methods=["GET"])
def listar_facturas():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        cliente = request.args.get("cliente", "")
        estado = request.args.get("estado", "")
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))

        params = {"cliente": cliente, "estado": estado, "page": page, "per_page": per_page}
        resp = requests.get(f"{config.API_URL}/facturas", headers=headers, params=params)

        if resp.status_code == 200:
            data = resp.json()
            facturas = data.get("facturas", [])
            total_pages = int(data.get("total_pages", 1))
            page = int(data.get("page", 1))

            for f in facturas:
                f["total"] = float(f.get("total", 0) or 0)

            return render_template(
                "facturas.html",
                facturas=facturas,
                page=page,
                total_pages=total_pages,
                request=request,
            )

        flash("❌ Error obteniendo facturas", "danger")
        return redirect(url_for("dashboard.index"))

    except Exception as e:
        flash(f"❌ Error conectando al backend: {e}", "danger")
        return redirect(url_for("dashboard.index"))


# =========================================================
# 💾 CREAR FACTURA (POST)
# =========================================================
@facturas_bp.route("/crear", methods=["POST"])
def crear_factura():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    id_reserva = request.form.get("idreserva")

    try:
        headers = {"Authorization": f"Bearer {session['token']}", "Content-Type": "application/json"}

        data = {
            "idcliente": request.form.get("idcliente"),
            "idusuario": session.get("idusuario", 1),
            "observaciones": request.form.get("observaciones"),
            "detalles": [],
            "pagos": []
        }

        # ---------- DETALLES ----------
        detalles_temp = {}
        for key, value in request.form.items():
            if key.startswith("detalles["):
                parts = key.replace("detalles[", "").replace("]", "").split("[")
                index, field = int(parts[0]), parts[1]
                detalles_temp.setdefault(index, {})[field] = value

        for d in detalles_temp.values():
            cantidad = float(d.get("cantidad", 0))
            valorunitario = float(d.get("valorunitario", 0))
            subtotal = cantidad * valorunitario
            data["detalles"].append({
                "idproducto": int(d.get("idproducto")) if d.get("idproducto") else None,
                "cantidad": cantidad,
                "valorunitario": valorunitario,
                "subtotal": subtotal,
                "descripcion": d.get("descripcion", None),
            })

        # ---------- PAGOS ----------
        pagos_temp = {}
        for key, value in request.form.items():
            if key.startswith("pagos["):
                parts = key.replace("pagos[", "").replace("]", "").split("[")
                index, field = int(parts[0]), parts[1]
                pagos_temp.setdefault(index, {})[field] = value

        for p in pagos_temp.values():
            data["pagos"].append({
                "idmedio": int(p.get("idmedio")) if p.get("idmedio") else None,
                "valor": float(p.get("valor", 0)),
                "due_date": p.get("due_date"),
            })

        # ---------- Enviar al backend ----------
        response = requests.post(f"{config.API_URL}/facturas", headers=headers, json=data)

        if response.status_code in [200, 201]:
            flash("✅ Factura creada correctamente", "success")

            # 🔁 Si viene de una reserva, marcarla como facturada
            if id_reserva:
                patch_resp = requests.patch(
                    f"{config.API_URL}/reservas/{id_reserva}/facturar",
                    headers={"Authorization": f"Bearer {session['token']}"}
                )
                if patch_resp.status_code == 200:
                    flash("🔁 Reserva asociada marcada como FACTURADA", "info")
                else:
                    flash("⚠️ Factura creada pero no se actualizó la reserva", "warning")

        else:
            flash(f"❌ Error creando factura: {response.text}", "danger")

    except Exception as e:
        flash(f"❌ Error enviando factura: {e}", "danger")

    return redirect(url_for("facturas.listar_facturas"))


# =========================================================
# 🔎 DETALLE DE FACTURA
# =========================================================
@facturas_bp.route("/<int:id>", methods=["GET"])
def detalle_factura(id):
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}
        r = requests.get(f"{config.API_URL}/facturas/{id}", headers=headers)
        if r.status_code == 200:
            factura = r.json()
            return render_template("detalle_factura.html", factura=factura)
        else:
            flash("Factura no encontrada ❌", "danger")
    except Exception as e:
        flash(f"❌ Error consultando factura: {e}", "danger")

    return redirect(url_for("facturas.listar_facturas"))


# =========================================================
# 🔄 PROXIES (Clientes, Productos, Medios, Reservas)
# =========================================================
@facturas_bp.route("/buscar_cliente", methods=["GET"])
def proxy_buscar_cliente():
    if "token" not in session:
        return jsonify([]), 401
    identificacion = request.args.get("identificacion", "")
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{config.API_URL}/clientes", headers=headers, params={"identificacion": identificacion})
        return jsonify(resp.json()) if resp.status_code == 200 else jsonify([])
    except Exception as e:
        print("❌ Error proxy cliente:", e)
        return jsonify([]), 500


@facturas_bp.route("/buscar_productos", methods=["GET"])
def proxy_productos():
    if "token" not in session:
        return jsonify([]), 401
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{config.API_URL}/productos", headers=headers)
        return jsonify(resp.json()) if resp.status_code == 200 else jsonify([])
    except Exception as e:
        print("❌ Error proxy productos:", e)
        return jsonify([]), 500


@facturas_bp.route("/buscar_medios", methods=["GET"])
def proxy_medios():
    if "token" not in session:
        return jsonify([]), 401
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{config.API_URL}/medios", headers=headers)
        return jsonify(resp.json()) if resp.status_code == 200 else jsonify([])
    except Exception as e:
        print("❌ Error proxy medios:", e)
        return jsonify([]), 500


@facturas_bp.route("/buscar_reserva/<identificacion>", methods=["GET"])
def proxy_buscar_reserva(identificacion):
    if "token" not in session:
        return jsonify([]), 401
    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{config.API_URL}/reservas/cliente/{identificacion}", headers=headers)
        return jsonify(resp.json()) if resp.status_code == 200 else jsonify([])
    except Exception as e:
        print("❌ Error proxy reserva:", e)
        return jsonify([]), 500
