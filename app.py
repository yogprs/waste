from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from detection import detect_trash
from validate import validateUsersData, validateHistoryData
from flask_socketio import SocketIO, emit
from supabase import create_client, Client
from dotenv import load_dotenv
import base64
import os
import numpy as np
import cv2
import bcrypt
import uuid

import warnings
warnings.filterwarnings("ignore")

load_dotenv()

database_url: str = os.getenv('DATABASE_URL')
database_key: str = os.getenv('DATABASE_KEY')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

supabase: Client = create_client(database_url, database_key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/detection')
def scan():
    return render_template('detection.html')

@app.route("/detection/live")
def live():
    return render_template("livescan.html")

@app.route("/detection/result")
def result():
    return render_template("result.html")

@app.route("/history")
def history():
    return render_template("history.html")

@app.route('/api/register', methods=['POST'])
def registerAPI():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON tidak terbaca"}), 400
    
    email = data.get("email").strip().lower()
    name = data.get("name")
    password = data.get("password")

    # VALIDASI REQUIRED
    if not email or not email.strip():
        return jsonify({"error": "Email wajib diisi"}), 400
    
    if not name or not name.strip():
        return jsonify({"error": "Name wajib diisi"}), 400
    
    if not password:
        return jsonify({"error": "Password wajib diisi"}), 400

    # VALIDASI untuk panjang Password
    if len(password) < 8:
        return jsonify({"error": "Password minimal 8 karakter"}), 400

    validate = validateUsersData(email, name, password)

    if (validate is not None):
        return jsonify({"error": validate}), 400

    try:
        check_email = supabase.table("users") \
            .select("id") \
            .eq("email", email) \
            .execute()

        if check_email.data:
            return jsonify({"error": "Email sudah terdaftar"}), 400

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        res = supabase.table("users").insert({
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name,
            "password": hashed_pw.decode('utf-8')
        }).execute()

        if not res.data:
            return jsonify({"error": "Gagal register"}), 500

        return jsonify({"message": "Register berhasil"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def loginAPI():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not email.strip():
        return jsonify({"error": "Email wajib diisi"}), 400
    
    if not password:
        return jsonify({"error": "Password wajib diisi"}), 400

    try:
        # ambil user berdasarkan email
        res = supabase.table("users").select("*").eq("email", email).execute()

        if not res.data:
            return jsonify({"error": "User tidak ditemukan"}), 404
        user = res.data[0]

        # cek password
        if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            return jsonify({
                "message": "Login berhasil",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                }
            }), 200
        else:
            return jsonify({"error": "Password salah"}), 401
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload/<id_user>", methods=["POST"])
def uploadAPI(id_user):
    file = request.files["file"]
    file_bytes = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    result_frame, label, label_with_accuracy, accuracy = detect_trash(frame)

    if label is None:
        return jsonify({
            "error": "Item tidak terdeksi, silahkan coba lagi atau menggunakan gambar yang lain."
        })

    validateLabel = validateHistoryData(label, None)

    if (validateLabel is not None):
        return jsonify({"error": validateLabel}), 400

    filename = f"detection-{uuid.uuid4()}.jpg"

    # Encode the result_frame to jpg, then convert to base64
    _, buffer = cv2.imencode('.jpg', result_frame)

    supabase.storage.from_("images").upload(
        path=filename,
        file=buffer.tobytes(),
        file_options={"content-type": "image/jpeg"}
    )

    public_url = supabase.storage.from_("images").get_public_url(filename)

    validateImg = validateHistoryData(label, public_url)

    if (validateImg is not None):
        supabase.storage.from_("images").remove([filename])
        return jsonify({"error": validateImg}), 400

    supabase.table("history").insert({
        "id": str(uuid.uuid4()),
        "label": label,
        "image": public_url,
        "accuracy": float(accuracy.replace('%', '')),
        "id_user": id_user,
    }).execute()

    return jsonify({
        "message": "Successfully",
        'label': label,
        'label_with_accuracy': label_with_accuracy,
        'accuracy': accuracy,
        'image_url': public_url,
        'type': 'upload',
    })

@app.route("/api/history/<id_user>")
def get_history_by_user(id_user):
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        label = request.args.get("label")
        sort_by = request.args.get("sort_by", "created_at")
        order = request.args.get("order", "desc")

        offset = (page - 1) * limit

        query = supabase.table("history") \
            .select("*", count="exact") \
            .eq("id_user", id_user)

        # FILTER
        if label:
            query = query.eq("label", label)

        query = query.order(sort_by, desc=(order == "desc"))

        # PAGINATION
        query = query.range(offset, offset + limit)

        # EXECUTE
        res = query.execute()

        return jsonify({
            "page": page,
            "limit": limit,
            "total": res.count,
            "data": res.data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/history/ids/<id_user>")
def get_all_history_ids(id_user):
    try:
        label = request.args.get("label")

        query = supabase.table("history") \
            .select("id") \
            .eq("id_user", id_user)

        if label:
            query = query.eq("label", label)

        res = query.execute()

        ids = [item["id"] for item in res.data]

        return jsonify({"ids": ids}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/history/delete", methods=["DELETE"])
def delete_history():
    try:
        data = request.get_json()

        ids = data.get("ids", [])
        id_user = data.get("id_user")
        label = data.get("label")
        delete_all = data.get("delete_all", False)

        # ======================
        # STEP 1: AMBIL DATA DULU
        # ======================
        select_query = supabase.table("history").select("id, image")

        if delete_all:
            if not id_user:
                return jsonify({"error": "id_user required"}), 400

            select_query = select_query.eq("id_user", id_user)

            if label:
                select_query = select_query.eq("label", label)

        else:
            if not ids:
                return jsonify({"error": "No IDs provided"}), 400

            select_query = select_query.in_("id", ids)

        res = select_query.execute()
        records = res.data

        # ======================
        # STEP 2: EXTRACT FILE PATH
        # ======================
        file_paths = []

        for item in records:
            image_url = item.get("image")

            if image_url:
                # ambil nama file dari URL
                filename = image_url.split("/")[-1]
                file_paths.append(filename)

        # ======================
        # STEP 3: DELETE FILE DI STORAGE
        # ======================
        if file_paths:
            supabase.storage.from_("images").remove(file_paths)

        # ======================
        # STEP 4: DELETE DATA DB
        # ======================
        delete_query = supabase.table("history").delete()

        if delete_all:
            delete_query = delete_query.eq("id_user", id_user)

            if label:
                delete_query = delete_query.eq("label", label)
        else:
            delete_query = delete_query.in_("id", ids)

        delete_query.execute()

        return jsonify({
            "message": "Delete success (DB + Storage)",
            "deleted_files": file_paths,
            "mode": "all" if delete_all else "selected"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/profile/<id>", methods=["PATCH"])
def update_profile(id):
    try:
        data = request.get_json()
        updated_user = data.get("updatedUser")

        if not updated_user:
            return jsonify({"error": "Data tidak ditemukan"}), 400

        name = updated_user.get("name")
        email = updated_user.get("email").strip().lower()
        password = updated_user.get("password")

        # ======================
        # VALIDASI
        # ======================
        if not name:
            return jsonify({"error": "Nama wajib di isi!"}), 400

        if not email:
            return jsonify({"error": "Email wajib di isi!"}), 400


        validate = validateUsersData(email, name, password)

        if (validate is not None):
            return jsonify({"error": validate}), 400


        update_data = {
            "name": name,
            "email": email,
        }

        # ======================
        # HANDLE PASSWORD
        # ======================
        if password:
            if len(password) < 8:
                return jsonify({"error": "Password minimal 8 karakter"}), 400

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            update_data["password"] = hashed_password.decode("utf-8")

        # ======================
        # UPDATE KE DATABASE
        # ======================
        response = supabase.table("users").update(update_data).eq("id", id).execute()

        if not response.data:
            return jsonify({"error": "User tidak ditemukan"}), 404

        user_data = response.data[0]

        filtered_user = {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "email": user_data.get("email"),
        }

        return jsonify({
            "message": "Profile berhasil diperbarui",
            "data": filtered_user
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "Terjadi kesalahan server"}), 500

@app.route("/api/profile/<id>", methods=["DELETE"])
def delete_profile(id):
    try:
        # ======================
        # STEP 1: CEK USER
        # ======================
        user = supabase.table("users").select("id").eq("id", id).execute()

        if not user.data:
            return jsonify({"error": "User tidak ditemukan"}), 404

        # ======================
        # STEP 2: AMBIL SEMUA HISTORY USER
        # ======================
        history_res = supabase.table("history") \
            .select("id, image") \
            .eq("id_user", id) \
            .execute()

        histories = history_res.data

        # ======================
        # STEP 3: AMBIL FILE PATH DARI STORAGE
        # ======================
        file_paths = []

        for item in histories:
            image_url = item.get("image")

            if image_url:
                filename = image_url.split("/")[-1]
                file_paths.append(filename)

        # ======================
        # STEP 4: HAPUS FILE DI STORAGE
        # ======================
        if file_paths:
            supabase.storage.from_("images").remove(file_paths)

        # ======================
        # STEP 5: HAPUS DATA HISTORY
        # ======================
        supabase.table("history").delete().eq("id_user", id).execute()

        # ======================
        # STEP 6: HAPUS USER
        # ======================
        supabase.table("users").delete().eq("id", id).execute()

        return jsonify({
            "message": "Akun, history, dan file berhasil dihapus",
            "deleted_files": file_paths,
            "total_history_deleted": len(histories)
        }), 200

    except Exception as e:
        print("ERROR DELETE PROFILE:", e)
        return jsonify({"error": "Terjadi kesalahan server"}), 500

uploaded_users = set()

@socketio.on('image')
def handle_image(data):
    sid = request.sid

    try:
        encoded = data['image'].split(',')[1]
        user_id = data['user_id']
        img_bytes = base64.b64decode(encoded)

        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is not None:
            public_url = None

            result_frame, label, label_with_accuracy, accuracy = detect_trash(frame)
            
            _, buffer = cv2.imencode('.jpg', result_frame)
            base64_result = base64.b64encode(buffer).decode('utf-8')


            # hanya 1x per user
            if label is not None and sid not in uploaded_users:
                uploaded_users.add(sid)

                 #  VALIDASI LABEL
                validateLabel = validateHistoryData(label, None)
                if validateLabel:
                    emit('response_back', {
                        'error': validateLabel,
                        'image': "data:image/jpeg;base64," + base64_result,
                        'label': label,
                        'label_with_accuracy': label_with_accuracy,
                        'accuracy': accuracy,
                        'image_url': None,
                        'type': 'stream'
                    })
                    return

                # _, buffer = cv2.imencode('.jpg', result_frame)

                filename = f"detection-{uuid.uuid4()}.jpg"
                # with open(f"./stream/{filename}", "wb") as f:
                #     f.write(file_bytes)

                supabase.storage.from_("images").upload(
                    path=filename,
                    file=buffer.tobytes(),
                    file_options={"content-type": "image/jpeg"}
                )

                public_url = supabase.storage.from_("images").get_public_url(filename)

                validateURL = validateHistoryData(label, public_url)
                if validateURL:
                    supabase.storage.from_("images").remove([filename])
                    emit('response_back', {
                        'error': validateURL,
                        'image': "data:image/jpeg;base64," + base64_result,
                        'label': label,
                        'label_with_accuracy': label_with_accuracy,
                        'accuracy': accuracy,
                        'image_url': None,
                        'type': 'stream'
                    })
                    return

                supabase.table("history").insert({
                    "id": str(uuid.uuid4()),
                    "label": label,
                    "image": public_url,
                    "accuracy": float(accuracy.replace('%', '')),
                    "id_user": user_id,
                }).execute()

                emit('response_back', {
                    'image': "data:image/jpeg;base64," + base64_result,
                    'label': label,
                    'label_with_accuracy': label_with_accuracy,
                    'accuracy': accuracy,
                    'image_url': public_url,
                    'type': 'stream',
                })
            else:
                emit('response_back', {
                    'image': "data:image/jpeg;base64," + base64_result,
                    'label': label,
                    'label_with_accuracy': label_with_accuracy,
                    'accuracy': accuracy,
                    'image_url': None,
                    'type': 'stream'
                })

    except Exception as e:
        print("Socket error:", str(e))

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    uploaded_users.discard(sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)