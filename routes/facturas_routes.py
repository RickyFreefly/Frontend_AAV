from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
import requests
import config

facturas_bp = Blueprint("facturas", __name__)

# ================== LISTAR FACTURAS (con filtros y paginación) ==================
@facturas_bp.route("/facturas")
def listar_facturas():
    if "token" not in session:
        flash("Debes iniciar sesión primero", "warning")
        return redirect(url_for("auth.login"))

    try:
        headers = {"Authorization": f"Bearer {session['token']}"}

        # 🔎 Parámetros desde querystring
        cliente = request.args.get("cliente", "")
        estado = request.args.get("estado", "")
        page = int(request.args.get("page", 1))      # aseguramos enteros
        per_page = int(request.args.get("per_page", 10))

        params = {
            "cliente": cliente,
            "estado": estado,
            "page": page,
            "per_page": per_page,
        }

        response = requests.get(f"{config.API_URL}/facturas", headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            facturas = data.get("facturas", [])
            page = int(data.get("page", 1))
            total_pages = int(data.get("total_pages", 1))

            # 🔧 Convertir total a float para evitar error de formateo en Jinja
            for f in facturas:
                try:
                    f["total"] = float(f.get("total", 0))
                except (ValueError, TypeError):
                    f["total"] = 0.0

            return render_template(
                "facturas.html",
                facturas=facturas,
                page=page,
                total_pages=total_pages,
                request=request  # 👉 para que HTML recuerde filtros en los inputs
            )
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
            "idcliente": request.form.get("idcliente"),
            "idusuario": session.get("idusuario", 1),
            "observaciones": request.form.get("observaciones"),
            "detalles": [],
            "pagos": []
        }

        # Procesar detalles dinámicos
        detalles_temp = {}
        for key, value in request.form.items():
            if key.startswith("detalles["):
                parts = key.replace("detalles[", "").replace("]", "").split("[")
                index, field = int(parts[0]), parts[1]
                if index not in detalles_temp:
                    detalles_temp[index] = {}
                detalles_temp[index][field] = value

        for d in detalles_temp.values():
            cantidad = float(d.get("cantidad", 0))
            valorunitario = float(d.get("valorunitario", 0))
            subtotal = cantidad * valorunitario
            data["detalles"].append({
                "idproducto": int(d.get("idproducto")) if d.get("idproducto") else None,
                "cantidad": cantidad,
                "valorunitario": valorunitario,
                "subtotal": subtotal,
                "descripcion": d.get("descripcion"),
                "descuento": float(d.get("descuento", 0)),
                "impuesto_id": d.get("impuesto_id")
            })

        # Procesar pagos dinámicos
        pagos_temp = {}
        for key, value in request.form.items():
            if key.startswith("pagos["):
                parts = key.replace("pagos[", "").replace("]", "").split("[")
                index, field = int(parts[0]), parts[1]
                if index not in pagos_temp:
                    pagos_temp[index] = {}
                pagos_temp[index][field] = value

        for p in pagos_temp.values():
            data["pagos"].append({
                "idmedio": int(p.get("idmedio")) if p.get("idmedio") else None,
                "valor": float(p.get("valor", 0)),
                "due_date": p.get("due_date"),
                "siigo_pago_id": p.get("siigo_pago_id")
            })

        idreserva = request.form.get("idreserva")

        try:
            headers = {
                "Authorization": f"Bearer {session['token']}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{config.API_URL}/facturas", headers=headers, json=data)

            if response.status_code in [200, 201]:
                flash("✅ Factura creada correctamente", "success")

                if idreserva:
                    patch_resp = requests.patch(
                        f"{config.API_URL}/reservas/{idreserva}/facturar",
                        headers={"Authorization": f"Bearer {session['token']}"}
                    )
                    if patch_resp.status_code == 200:
                        flash("✅ Reserva asociada marcada como FACTURADA", "info")
                    else:
                        flash("⚠️ Factura creada pero no se actualizó la reserva", "warning")

                return redirect(url_for("facturas.listar_facturas"))
            else:
                flash(f"❌ Error al crear factura: {response.text}", "danger")

        except Exception as e:
            flash(f"❌ Error conectando al backend: {e}", "danger")

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


# ================== PROXIES ==================
@facturas_bp.route("/facturas/buscar_cliente")
def proxy_buscar_cliente():
    if "token" not in session:
        return jsonify({"error": "No autorizado"}), 401

    identificacion = request.args.get("identificacion", "")
    headers = {"Authorization": f"Bearer {session['token']}"}

    try:
        resp = requests.get(f"{config.API_URL}/clientes", headers=headers, params={"identificacion": identificacion})
        return jsonify(resp.json()) if resp.status_code == 200 else (jsonify([]), 404)
    except Exception as e:
        print("❌ Error en proxy clientes:", e)
        return jsonify({"error": "Backend no disponible"}), 500


@facturas_bp.route("/facturas/buscar_productos")
def proxy_productos():
    if "token" not in session:
        return jsonify({"error": "No autorizado"}), 401

    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{config.API_URL}/productos", headers=headers)
        return jsonify(resp.json()) if resp.status_code == 200 else (jsonify([]), 404)
    except Exception as e:
        print("❌ Error en proxy productos:", e)
        return jsonify({"error": "Backend no disponible"}), 500


@facturas_bp.route("/facturas/buscar_medios")
def proxy_medios():
    if "token" not in session:
        return jsonify({"error": "No autorizado"}), 401

    headers = {"Authorization": f"Bearer {session['token']}"}
    try:
        resp = requests.get(f"{config.API_URL}/medios", headers=headers)
        return jsonify(resp.json()) if resp.status_code == 200 else (jsonify([]), 404)
    except Exception as e:
        print("❌ Error en proxy medios:", e)
        return jsonify({"error": "Backend no disponible"}), 500
