import os
import sys
from flask import Flask, render_template, request, redirect, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import threading
import time
from flask import Response
#from rfid import poll_rfid, get_last_uid, clear_last_uid

sys.path.append("../app")

from storage import get_tag_map, save_tag_map
from config import AUDIO_FOLDER
from auth import login_manager, authenticate

UPLOAD_FOLDER = f"../{AUDIO_FOLDER}"
ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg"}

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

login_manager.init_app(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------
# Helpers
# -----------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def list_audio():
    return sorted([
        f for f in os.listdir(UPLOAD_FOLDER)
        if allowed_file(f)
    ])


# -----------------------
# Views
# -----------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate(request.form["username"], request.form["password"])
        if user:
            login_user(user)
            return redirect("/")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        tags=get_tag_map(),
        audio_files=list_audio(),
        user=current_user.id
    )


# -----------------------
# REST API
# -----------------------

@app.route("/api/tags", methods=["GET"])
@login_required
def api_get_tags():
    return jsonify(get_tag_map())


@app.route("/api/tags", methods=["POST"])
@login_required
def api_set_tag():
    data = request.json
    tag_map = get_tag_map()
    tag_map[data["uid"]] = data["filename"]
    save_tag_map(tag_map)
    return jsonify({"status": "ok"})


@app.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    file = request.files.get("file")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return jsonify({"status": "uploaded"})


@app.route("/api/files", methods=["GET"])
@login_required
def api_files():
    return jsonify(list_audio())


@app.route("/api/files/<filename>", methods=["DELETE"])
@login_required
def api_delete_file(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"status": "deleted"})

@app.route("/api/stream")
@login_required
def stream():
    def event_stream():
        last_sent = None
        while True:
            uid = get_last_uid()
            if uid and uid != last_sent:
                yield f"data: {uid}\n\n"
                last_sent = uid
            time.sleep(0.5)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/api/clear_last_tag", methods=["POST"])
@login_required
def clear_tag():
    clear_last_uid()
    return jsonify({"status": "cleared"})

#rfid_thread = threading.Thread(target=poll_rfid, daemon=True)
#rfid_thread.start()
app.run(host="0.0.0.0", port=5000)