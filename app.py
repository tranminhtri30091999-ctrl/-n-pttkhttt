import os

from flask import Flask, redirect

from database.db_helper import init_db
from modules.admin.routes import admin_bp
from modules.client.routes import client_bp
from modules.order.routes import order_bp
from modules.products.routes import products_bp
from modules.report.routes import report_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(client_bp)
app.register_blueprint(products_bp, url_prefix="/staff")
app.register_blueprint(order_bp, url_prefix="/staff")
app.register_blueprint(report_bp, url_prefix="/staff")


@app.route("/")
def root():
    return redirect("/client/index.html")


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
