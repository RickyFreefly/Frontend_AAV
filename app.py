from flask import Flask
from routes.auth_routes import auth_bp
from routes.usuarios_routes import usuarios_bp
from routes.dashboard_routes import dashboard_bp
from routes.egresos_routes import egresos_bp
from routes.reservas_routes import reservas_bp
from routes.clientes import clientes_bp
from routes.facturas_routes import facturas_bp
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(egresos_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(facturas_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
