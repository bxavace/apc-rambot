"""Admin blueprint containing dashboard, upload, and document routes."""

import csv
import logging
import os
import time
from functools import wraps
from io import StringIO

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
    verify_jwt_in_request,
)
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
from langchain_text_splitters import SpacyTextSplitter
from markdown import markdown

from embed import datastore
from models import Conversation, Document, Lead, Session, db
from utils import limiter

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, template_folder="../templates")


def check_auth(username, password):
    env_username = os.getenv("ADMIN_USERNAME")
    env_password = os.getenv("ADMIN_PASSWORD")
    from hmac import compare_digest

    return compare_digest(username, env_username) and compare_digest(password, env_password)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:  # pylint: disable=broad-except
            next_url = request.path
            return redirect(url_for("admin.login", next=next_url))
        return f(*args, **kwargs)

    return decorated


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("admin.admin")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if check_auth(username, password):
            access_token = create_access_token(identity=username)
            response = redirect(next_url)
            set_access_cookies(response, access_token)
            logger.info("Successful login by %s from %s", username, request.remote_addr)
            return response
        logger.warning("Failed login attempt by %s from %s", username, request.remote_addr)
        flash("Invalid credentials.")
    return render_template("login.html", next=next_url)


@admin_bp.route("/logout")
def logout():
    flash("You have been logged out.")
    logger.info("User logged out from %s", request.remote_addr)
    response = redirect(url_for("admin.login"))
    unset_jwt_cookies(response)
    return response


@admin_bp.route("/")
@login_required
def admin():
    page = request.args.get("page", 1, type=int)
    per_page = 15
    sessions = Session.query.order_by(Session.start_time.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )
    return render_template("admin.html", sessions=sessions)


@admin_bp.route("/session/<int:session_id>", methods=["GET"])
@login_required
def view_session(session_id):
    session = (
        Session.query.options(db.joinedload(Session.conversations))
        .filter_by(id=session_id)
        .first()
    )
    if session:
        conversations = sorted(session.conversations, key=lambda x: x.timestamp)
        return render_template("session.html", session=session, conversations=conversations)

    flash("Session not found.", "danger")
    return redirect(url_for("admin.admin"))


@admin_bp.route("/export", methods=["GET"])
@login_required
def export_data():
    return export_csv()


@admin_bp.route("/leads", methods=["GET"])
@login_required
def get_leads():
    page = request.args.get("page", 1, type=int)
    per_page = 15
    leads = Lead.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template("leads.html", leads=leads)


@admin_bp.route("/leads/<int:id>", methods=["POST"])
@login_required
def delete_lead(id):
    lead = Lead.query.get(id)
    if lead:
        db.session.delete(lead)
        db.session.commit()
        flash("Lead deleted successfully.", "success")
    else:
        flash("Lead not found.", "danger")
    return redirect(url_for("admin.get_leads"))


@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    if request.method == "GET":
        return render_template("upload.html")

    if "file" not in request.files:
        flash("No file part", "warning")
        return redirect(request.url)

    files = request.files.getlist("file")
    if not files or all(file.filename == "" for file in files):
        flash("No selected files", "warning")
        return redirect(request.url)

    responses = []

    for file in files:
        if file.filename == "":
            responses.append({"filename": None, "message": "No filename provided"})
            continue

        if not allowed_file(file.filename):
            responses.append({"filename": file.filename, "message": "Invalid file type"})
            continue

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > current_app.config["MAX_FILE_SIZE"]:
            responses.append({"filename": file.filename, "message": "File too large"})
            continue

        base, ext = os.path.splitext(file.filename)
        new_filename = f"{base}{ext}"
        filepath = os.path.join(upload_folder, new_filename)

        if os.path.exists(filepath):
            timestr = time.strftime("%Y%m%d%H%M%S")
            new_filename = f"{base}_{timestr}{ext}"
            filepath = os.path.join(upload_folder, new_filename)

        file.save(filepath)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            success = process_file(filepath)
            if success:
                responses.append({"filename": new_filename, "message": "Upload complete."})
            else:
                responses.append({"filename": new_filename, "message": "Upload failed during processing!"})
        else:
            responses.append({"filename": new_filename, "message": "Saving failed."})

    for response in responses:
        flash(f"{response['filename'] or 'Unnamed file'}: {response['message']}", "info")
    return redirect(url_for("admin.upload"))


@admin_bp.route("/upload-web", methods=["POST"])
@login_required
def upload_web():
    url = request.form.get("url")
    if not url:
        flash("No URL provided.", "warning")
        return redirect(url_for("admin.upload"))

    loader = WebBaseLoader(url)
    data = loader.load()
    if not data:
        flash("No data loaded from URL.", "warning")
        return redirect(url_for("admin.upload"))

    text_splitter = SpacyTextSplitter()
    docs = text_splitter.split_documents(data)
    if not docs:
        flash("No documents were split from the URL.", "warning")
        return redirect(url_for("admin.upload"))

    ids = datastore.add_documents(documents=docs)
    for doc_id in ids:
        document = Document(document_id=doc_id, document_name=url)
        db.session.add(document)
    db.session.commit()
    flash("Upload complete.", "info")
    return redirect(url_for("admin.upload"))


@admin_bp.route("/documents", methods=["GET"])
@login_required
def get_documents():
    page = request.args.get("page", 1, type=int)
    per_page = 15
    documents = Document.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template("documents.html", documents=documents)


@admin_bp.route("/documents/<int:id>", methods=["GET"])
@login_required
def get_document(id):
    document = Document.query.get(id)
    if document:
        try:
            with open(document.document_name, "r", encoding="utf-8") as file:
                content = file.read()
                html_content = markdown(content) if document.document_name.lower().endswith(".md") else content
                return render_template("document.html", document=document, content=html_content)
        except Exception as err:  # pylint: disable=broad-except
            logger.exception("Error reading file: %s", err)
            flash(f"Error reading file: {err}", "danger")
            return redirect(url_for("admin.get_documents"))
    flash("Document not found.", "danger")
    return redirect(url_for("admin.get_documents"))


@admin_bp.route("/documents/delete/<int:id>", methods=["POST"])
@login_required
def delete_document(id):
    document = Document.query.get(id)
    if not document:
        flash("Document not found.", "danger")
        return redirect(url_for("admin.get_documents"))

    delete_embeddings(document.document_id)
    if os.path.exists(document.document_name):
        os.remove(document.document_name)
    db.session.delete(document)
    db.session.commit()
    flash("Document deleted successfully.", "success")
    return redirect(url_for("admin.get_documents"))


def allowed_file(filename):
    allowed_extensions = {"pdf", "md"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def delete_embeddings(document_id):
    try:
        datastore.delete([document_id])
        return True
    except Exception as err:  # pylint: disable=broad-except
        logger.exception("Error deleting document from Azure Search: %s", err)
        return False


def process_file(filepath):
    if not os.path.isfile(filepath):
        logger.error("Error: File not found: %s", filepath)
        return False
    if not (filepath.lower().endswith(".pdf") or filepath.lower().endswith(".md")):
        logger.error("Error: Unsupported file type: %s", filepath)
        return False
    try:
        if filepath.lower().endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            data = loader.load()
        else:
            loader = TextLoader(filepath, encoding="utf-8")
            data = loader.load()

        if not data:
            logger.warning("Warning: No data was loaded from the file: %s", filepath)
            return False

        text_splitter = SpacyTextSplitter()
        docs = text_splitter.split_documents(data)
        if not docs:
            logger.warning("Warning: No documents were split from the file: %s", filepath)
            return False
        ids = datastore.add_documents(documents=docs)
        for doc_id in ids:
            document = Document(document_id=doc_id, document_name=filepath)
            db.session.add(document)
        db.session.commit()
        return True

    except Exception as err:  # pylint: disable=broad-except
        logger.exception("Error processing file %s: %s", filepath, err)
        return False


def export_csv():
    conversations = Conversation.query.all()

    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)

    csv_writer.writerow(["user_message", "bot_response", "timestamp", "latency"])

    for conversation in conversations:
        csv_writer.writerow(
            [
                conversation.user_message,
                conversation.bot_response,
                conversation.timestamp,
                conversation.latency,
            ]
        )

    response = Response(
        csv_output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=conversations.csv"},
    )
    return response
