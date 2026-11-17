from functools import wraps

from flask import Blueprint, redirect, render_template, session, url_for

client_bp = Blueprint("client", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("client.login_page"))
        return view(*args, **kwargs)

    return wrapped


@client_bp.route("/")
def home():
    return redirect("/client/index.html")


@client_bp.route("/client/index.html")
def index_page():
    return render_template("client/index.html")


@client_bp.route("/client/storeproduct.html")
def storeproduct_page():
    return render_template("client/storeproduct.html")


@client_bp.route("/client/checkout.html")
@login_required
def checkout_page():
    return render_template("client/checkout.html")


@client_bp.route("/client/login.html")
def login_page():
    return render_template("client/login.html")
