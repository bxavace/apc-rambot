"""Client-facing routes (test harness views)."""

from flask import Blueprint, redirect, render_template, url_for

client_bp = Blueprint("client", __name__, template_folder="../templates")


@client_bp.route("/")
def index():
    return redirect(url_for("admin.login"))


@client_bp.route("/client")
def client():
    return render_template("client_test.html")


@client_bp.route("/client-no-history")
def client_no_history():
    return render_template("client_nh.html")
