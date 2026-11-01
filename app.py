from urllib.parse import unquote, urlparse

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash

from detection import detect_trash, clear_history

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

from threading import Lock

import warnings

warnings.filterwarnings("ignore")

load_dotenv()

database_url: str = os.getenv('DATABASE_URL')

database_key: str = os.getenv('DATABASE_KEY')

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

supabase: Client = create_client(database_url, database_key)

# Mapping foreign key berdasarkan jenis akun

USER_FOREIGN_KEYS = {

    "admin": "id_admin",

    "petugas": "id_petugas",

    "nasabah": "id_nasabah",

}

@app.route('/')

def home():

    return render_template('index.html')

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

        res = supabase.rpc(

            "login_lookup",

            {"p_email": email.strip().lower()}

        ).execute()

        user = res.data

        if not user:

            return jsonify({

                "error": "Email tidak ditemukan"

            }), 404

        if not bcrypt.checkpw(

            password.encode("utf-8"),

            user["password"].encode("utf-8")

        ):

            return jsonify({

                "error": "Password salah"

            }), 401

        return jsonify({

            "message": "Login berhasil",

            "user": {

                "id": user["id"],

                "name": user["name"],

                "email": user["email"],

                "role": user["role"]

            }

        }), 200

    except Exception as e:

        return jsonify({

            "error": "Terjadi kesalahan pada server"

        }), 500

@app.route("/api/create/user", methods=["POST"])

def createUser():

    data = request.get_json()

    if not data:

       return jsonify({"error": "Data tidak boleh kosong"}), 400

    email = data.get("email").strip().lower()

    name = data.get("name")

    password = data.get("password")

    idAdmin = data.get("id_admin")

    role = data.get("role")

    # VALIDASI wajib diisi

    if not email or not email.strip():

        return jsonify({"error": "Email wajib diisi"}), 400

    

    if not name or not name.strip():

        return jsonify({"error": "Name wajib diisi"}), 400

    

    if not password:

        return jsonify({"error": "Password wajib diisi"}), 400

    

    if not idAdmin:

        return jsonify({"error": "Id admin wajib ada"}), 400

    if not role or not role.strip():

        return jsonify({"error": "Role User wajib diisi"}), 400

    if role != 'petugas' and role != 'nasabah':

        return jsonify({"error": "Role yang dipilih tidak valid"})

    # VALIDASI format UUID untuk id_admin (mencegah error sintaksis jika ID tidak lengkap)

    try:

        uuid.UUID(idAdmin)

    except ValueError:

        return jsonify({"error": "Format ID Admin tidak valid"}), 400

    # VALIDASI untuk panjang Password

    if len(password) < 8:

        return jsonify({"error": "Password minimal 8 karakter"}), 400

    validate = validateUsersData(email, name, password)

    if (validate is not None):

        return jsonify({"error": validate}), 400

    try:

        # PENCECEKAN EMAIL SUDAH TERDAFTAR ATAU BELUM

        check_petugas_email = supabase.table("petugas") \
            .select("email") \
            .eq("email", email) \
            .execute()

        check_nasabah_email = supabase.table("nasabah") \
            .select("email") \
            .eq("email", email) \
            .execute()

        if check_petugas_email.data or check_nasabah_email.data:

            return jsonify({"error": f"Email '{email}' sudah terdaftar"}), 400

        check_admin = supabase.table("admin") \
            .select("id_admin") \
            .eq("id_admin", idAdmin) \
            .execute()

        if not check_admin.data:

            return jsonify({"error": "Akun yang anda gunakan tidak dapat melakukan aksi ini"}), 403

        id_column_name = USER_FOREIGN_KEYS[str(role)]

        generated_uuid = str(uuid.uuid4())

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        res = supabase.table(str(role)).insert({

            id_column_name: generated_uuid,

            "email": email,

            "nama": name,

            "password": hashed_pw.decode('utf-8')

        }).execute()

        if not res.data:

            return jsonify({"error": "Gagal membuat akun baru"}), 500

        return jsonify({"message": "Berhasil membuat akun baru"}), 201

    except Exception as e:

        return jsonify({"error": str(e)}), 400

@app.route("/api/upload/<id_user>", methods=["POST"])

def uploadAPI(id_user):

    # Validasi role

    role = request.form.get("role", "").lower()

    USER_FOREIGN_KEYS = {

        "admin": "id_admin",

        "petugas": "id_petugas",

        "nasabah": "id_nasabah"

    }

    if role not in USER_FOREIGN_KEYS:

        return jsonify({

            "error": "Role tidak valid"

        }), 400

    id_column = USER_FOREIGN_KEYS[role]

    # Validasi file

    if "file" not in request.files:

        return jsonify({

            "error": "File wajib diupload"

        }), 400

    file = request.files["file"]

    if not file.filename:

        return jsonify({

            "error": "File belum dipilih"

        }), 400

    try:

        # Pastikan user tersedia

        user_res = (

            supabase.table(role)

            .select(id_column)

            .eq(id_column, id_user)

            .execute()

        )

        if not user_res.data:

            found_role = None

            for r_name, fk_name in USER_FOREIGN_KEYS.items():

                if r_name == role:

                    continue

                other_res = (

                    supabase.table(r_name)

                    .select(fk_name)

                    .eq(fk_name, id_user)

                    .execute()

                )

                if other_res.data:

                    role = r_name

                    id_column = fk_name

                    found_role = r_name

                    break

            if not found_role:

                return jsonify({

                    "error": "User tidak ditemukan"

                }), 404

        # Decode gambar

        file_bytes = np.frombuffer(file.read(), np.uint8)

        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if frame is None:

            return jsonify({

                "error": "File gambar tidak valid"

            }), 400

        center_roi = (

            request.form.get("center_roi", "false").lower()

            in ["true", "1"]

        )

        # Deteksi sampah

        result_frame, label, label_with_accuracy, accuracy = detect_trash(

            frame,

            is_upload=True,

            center_roi=center_roi

        )

        if label is None:

            return jsonify({

                "error": "Item tidak terdeteksi, silakan coba gambar lain."

            }), 400

        # Validasi label

        validate_label = validateHistoryData(label, None)

        if validate_label is not None:

            return jsonify({

                "error": validate_label

            }), 400

        # Encode hasil deteksi

        success, buffer = cv2.imencode(".jpg", result_frame)

        if not success:

            return jsonify({

                "error": "Gagal memproses gambar"

            }), 500

        filename = f"detection-{uuid.uuid4()}.jpg"

        uploaded = False

        try:

            # Upload gambar ke Supabase Storage

            supabase.storage.from_("images").upload(

                path=filename,

                file=buffer.tobytes(),

                file_options={

                    "content-type": "image/jpeg"

                }

            )

            uploaded = True

            public_url = (

                supabase.storage

                .from_("images")

                .get_public_url(filename)

            )

            # Validasi gambar

            validate_img = validateHistoryData(label, public_url)

            if validate_img is not None:

                return jsonify({

                    "error": validate_img

                }), 400

            # Siapkan data riwayat

            history_data = {

                "id_riwayat": str(uuid.uuid4()),

                "label": label,

                "gambar": public_url,

                "akurasi": float(accuracy.replace("%", "")),

                "id_admin": None,

                "id_petugas": None,

                "id_nasabah": None

            }

            # Isi FK sesuai role

            history_data[id_column] = id_user

            # Simpan riwayat

            supabase.table("riwayat").insert(

                history_data

            ).execute()

            return jsonify({

                "message": "Upload berhasil",

                "id_riwayat": history_data["id_riwayat"],

                "label": label,

                "label_with_accuracy": label_with_accuracy,

                "accuracy": accuracy,

                "image_url": public_url,

                "role": role,

                "type": "upload"

            }), 200

        except Exception:

            # Hapus gambar jika penyimpanan riwayat gagal

            if uploaded:

                try:

                    supabase.storage.from_("images").remove([filename])

                except Exception:

                    pass

            raise

    except Exception as e:

        print("Upload Error:", str(e))

        return jsonify({

            "error": "Terjadi kesalahan saat upload"

        }), 500

@app.route("/api/history/<user_type>/<id_user>", methods=["GET"])

def get_history(user_type, id_user):

    try:

        page = max(int(request.args.get("page", 1)), 1)

        limit = max(int(request.args.get("limit", 10)), 1)

        # Batasi maksimal data per halaman

        limit = min(limit, 20)

        label = request.args.get("label", "").strip()

        sort_by = request.args.get("sort_by", "created_at").strip()

        order = request.args.get("order", "desc").lower().strip()

        # VALIDASI USER TYPE

        user_type = user_type.lower().strip()

        allowed_users = {

            "admin": {

                "table": "admin",

                "column": "id_admin"

            },

            "petugas": {

                "table": "petugas",

                "column": "id_petugas"

            },

            "nasabah": {

                "table": "nasabah",

                "column": "id_nasabah"

            }

        }

        if user_type not in allowed_users:

            return jsonify({

                "error": "Jenis akun tidak valid"

            }), 400

        user_config = allowed_users[user_type]

        # Validasi UUID

        try:

            id_user = str(uuid.UUID(id_user))

        except ValueError:

            return jsonify({"error": "Format ID User tidak valid"}), 400

        # Validasi Akun user

        check_user = (

            supabase.table(user_config["table"])

            .select(user_config["column"])

            .eq(user_config["column"], id_user)

            .execute()

        )

        if not check_user.data:

            return jsonify({

                "error": "Akun tidak ditemukan atau tidak memiliki akses"

        }), 403

        # Validasi Sorting

        allowed_sort = {

            "dibuat_pada": "dibuat_pada",

            "akurasi": "akurasi",

            "label": "label"

        }

        sort_column = allowed_sort.get(sort_by, "dibuat_pada")

        if order not in ["asc", "desc"]:

            order = "desc"

        offset = (page - 1) * limit

        # Query Riwayat

        query = (

            supabase.table("riwayat")

            .select("*", count="exact")

        )

        # Untuk Admin mengambil semua data

        if user_type == "admin":

            pass

        elif user_type == "petugas":

            query = query.eq("id_petugas", id_user)

        elif user_type == "nasabah":

            query = query.eq("id_nasabah", id_user)

        # Filter Label

        if label:

            query = query.eq("label", label)

        # Sorting

        query = query.order(

            sort_column,

            desc=(order == "desc")

        )

        # Pagination

        query = query.range(

            offset,

            offset + limit - 1

        )

        res = query.execute()

        total = res.count or 0

        # Format Data

        data = []

        # Tampung ID berdasarkan role

        user_ids = {

            "admin": set(),

            "petugas": set(),

            "nasabah": set()

        }

        # Identifikasi pemilik setiap riwayat

        for item in res.data:

            if item.get("id_admin"):

                user_ids["admin"].add(item["id_admin"])

            elif item.get("id_petugas"):

                user_ids["petugas"].add(item["id_petugas"])

            elif item.get("id_nasabah"):

                user_ids["nasabah"].add(item["id_nasabah"])

        # Ambil nama user secara batch

        user_names = {}

        user_tables = {

            "admin": "id_admin",

            "petugas": "id_petugas",

            "nasabah": "id_nasabah"

        }

        for role, ids in user_ids.items():

            if not ids:

                continue

            column = user_tables[role]

            users = (

                supabase.table(role)

                .select(f"{column}, nama")

                .in_(column, list(ids))

                .execute()

            )

            for user in users.data:

                user_names[(role, user[column])] = user["nama"]

        # Response Riwayat

        for item in res.data:

            history_user_id = None

            role_user = None

            if item.get("id_admin"):

                history_user_id = item["id_admin"]

                role_user = "admin"

            elif item.get("id_petugas"):

                history_user_id = item["id_petugas"]

                role_user = "petugas"

            elif item.get("id_nasabah"):

                history_user_id = item["id_nasabah"]

                role_user = "nasabah"

            nama_user = (

                user_names.get((role_user, history_user_id))

                if role_user else None

            )

            data.append({

                "id": item["id_riwayat"],

                "label": item["label"],

                "accuracy": item["akurasi"],

                "image": item["gambar"],

                "id_user": history_user_id,

                "user_type": role_user,

                "user_name": nama_user,

                "created_at": item["dibuat_pada"]

            })

        # Response

        return jsonify({

            "page": page,

            "limit": limit,

            "total": total,

            "total_page": (

                (total + limit - 1) // limit

                if total > 0 else 0

            ),

            "sort_by": sort_column,

            "order": order,

            "data": data

        }), 200

    except ValueError:

        return jsonify({

            "error": "Invalid page or limit"

        }), 400

    except Exception as e:

        print("Get history error:", str(e))

        return jsonify({

            "error": "Terjadi kesalahan saat mengambil riwayat"

        }), 500

@app.route("/api/history", methods=["DELETE"])
def delete_history():
    try:
        data = request.get_json(silent=True) or {}
        user_type = str(data.get("user_type", "")).lower().strip()
        id_user = data.get("id_user")
        ids = data.get("ids", [])
        label = data.get("label")
        delete_all = data.get("delete_all", False)

        # VALIDASI INPUT
        allowed_users = {
            "admin": {
                "table": "admin",
                "column": "id_admin"
            },
            "petugas": {
                "table": "petugas",
                "column": "id_petugas"
            },
            "nasabah": {
                "table": "nasabah",
                "column": "id_nasabah"
            }
        }

        if user_type not in allowed_users:
            return jsonify({
                "error": "Jenis akun tidak valid"
            }), 400

        if not id_user:
            return jsonify({
                "error": "id_user wajib diisi"
            }), 400

        try:
            id_user = str(uuid.UUID(str(id_user)))
        except ValueError:
            return jsonify({
                "error": "Format ID User tidak valid"
            }), 400

        user_config = allowed_users[user_type]

        # Validasi delete_all
        if not isinstance(delete_all, bool):
            return jsonify({
                "error": "delete_all harus berupa boolean"
            }), 400

        # Validasi label
        if label is not None:
            label = str(label).strip()
            if not label:
                label = None

        # Validasi IDs
        if not delete_all:
            if not isinstance(ids, list) or not ids:
                return jsonify({
                    "error": "IDs wajib diisi untuk menghapus riwayat terpilih"
                }), 400

            if len(ids) > 100:
                return jsonify({
                    "error": "Maksimal 100 riwayat dalam satu kali penghapusan"
                }), 400

            try:
                ids = list(set(
                    str(uuid.UUID(str(item)))
                    for item in ids
                ))
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Terdapat ID riwayat yang tidak valid"
                }), 400

        # VALIDASI AKUN (dengan fallback pengecekan role lain)
        check_user = (
            supabase.table(user_config["table"])
            .select(user_config["column"])
            .eq(user_config["column"], id_user)
            .execute()
        )

        if not check_user.data:
            found_role = None
            for r_name, r_config in allowed_users.items():
                if r_name == user_type:
                    continue
                c_user = (
                    supabase.table(r_config["table"])
                    .select(r_config["column"])
                    .eq(r_config["column"], id_user)
                    .execute()
                )
                if c_user.data:
                    user_type = r_name
                    user_config = r_config
                    found_role = r_name
                    break
            if not found_role:
                return jsonify({
                    "error": "Akun tidak ditemukan atau tidak memiliki akses"
                }), 403

        # HELPER FILTER ROLE
        def apply_user_filter(query):
            if user_type == "admin":
                return query
            elif user_type == "petugas":
                return query.eq("id_petugas", id_user)
            elif user_type == "nasabah":
                return query.eq("id_nasabah", id_user)
            return query

        # AMBIL DATA RIWAYAT YANG AKAN DIHAPUS
        select_query = (
            supabase.table("riwayat")
            .select("id_riwayat, gambar")
        )
        select_query = apply_user_filter(select_query)

        if delete_all:
            if label:
                select_query = select_query.eq("label", label)
        else:
            select_query = select_query.in_("id_riwayat", ids)

        res = select_query.execute()
        records = res.data or []

        if not records:
            return jsonify({
                "message": "Tidak ada riwayat yang dapat dihapus",
                "deleted_count": 0,
                "deleted_files": [],
                "mode": "all" if delete_all else "selected"
            }), 200

        # AMBIL SEMUA ID RIWAYAT UNTUK DIHAPUS
        target_ids = [item["id_riwayat"] for item in records if item.get("id_riwayat")]

        # EXTRACT STORAGE PATH GAMBAR
        file_paths = []
        for item in records:
            image_url = item.get("gambar")
            if not image_url:
                continue
            try:
                parsed_url = urlparse(image_url)
                path = unquote(parsed_url.path)
                marker = "/images/"
                if marker in path:
                    file_path = path.split(marker, 1)[1]
                    if file_path:
                        file_paths.append(file_path)
            except Exception as storage_error:
                print("Extract storage path error:", str(storage_error))

        file_paths = list(set(file_paths))

        # HAPUS DATA DARI DATABASE (dengan filter ID bertahap agar PostgREST selalu valid)
        for i in range(0, len(target_ids), 100):
            batch = target_ids[i:i + 100]
            supabase.table("riwayat").delete().in_("id_riwayat", batch).execute()

        # HAPUS GAMBAR DARI SUPABASE STORAGE
        storage_error = None
        deleted_files = []
        if file_paths:
            try:
                supabase.storage.from_("images").remove(file_paths)
                deleted_files = file_paths
            except Exception as e:
                storage_error = str(e)
                print("Storage delete error:", storage_error)

        response = {
            "message": "Riwayat berhasil dihapus",
            "deleted_count": len(target_ids),
            "deleted_files": deleted_files,
            "mode": "all" if delete_all else "selected"
        }

        if storage_error:
            response["warning"] = "Data riwayat berhasil dihapus, tetapi beberapa gambar gagal dihapus dari Storage"

        return jsonify(response), 200

    except Exception as e:
        print("Delete history error:", str(e))
        return jsonify({
            "error": "Terjadi kesalahan saat menghapus riwayat"
        }), 500


@app.route("/users")

def users_page():

    return render_template("users.html")

@app.route("/api/users", methods=["GET"])

def get_all_users():

    id_admin = request.args.get("id_admin", "").strip()

    role_filter = request.args.get("role", "all").strip().lower()

    search = request.args.get("search", "").strip()

    try:

        page = max(int(request.args.get("page", 1)), 1)

        limit = min(max(int(request.args.get("limit", 10)), 1), 50)

    except ValueError:

        return jsonify({"error": "Parameter page atau limit tidak valid"}), 400

    if not id_admin:

        return jsonify({"error": "id_admin wajib diisi"}), 400

    try:

        uuid.UUID(id_admin)

    except ValueError:

        return jsonify({"error": "Format ID Admin tidak valid"}), 400

    check_admin = supabase.table("admin").select("id_admin").eq("id_admin", id_admin).execute()

    if not check_admin.data:

        return jsonify({"error": "Akses ditolak"}), 403

    try:

        data = []

        if role_filter in ["all", "petugas"]:

            q = supabase.table("petugas").select("id_petugas, nama, email")

            if search:

                q = q.ilike("nama", f"%{search}%")

            res = q.order("nama").execute()

            for u in res.data:

                data.append({"id": u["id_petugas"], "nama": u["nama"], "email": u["email"], "role": "petugas"})

        if role_filter in ["all", "nasabah"]:

            q = supabase.table("nasabah").select("id_nasabah, nama, email")

            if search:

                q = q.ilike("nama", f"%{search}%")

            res = q.order("nama").execute()

            for u in res.data:

                data.append({"id": u["id_nasabah"], "nama": u["nama"], "email": u["email"], "role": "nasabah"})

        data.sort(key=lambda x: x["nama"].lower())

        total = len(data)

        offset = (page - 1) * limit

        paginated = data[offset:offset + limit]

        return jsonify({

            "page": page,

            "limit": limit,

            "total": total,

            "total_page": (total + limit - 1) // limit if total > 0 else 0,

            "data": paginated

        }), 200

    except Exception as e:

        print("Get all users error:", str(e))

        return jsonify({"error": "Terjadi kesalahan saat mengambil data pengguna"}), 500

@app.route("/api/users/<role>/<id_user>", methods=["DELETE"])

def delete_user(role, id_user):

    data = request.get_json(silent=True) or {}

    id_admin = str(data.get("id_admin", "")).strip()

    if role not in ["petugas", "nasabah"]:

        return jsonify({"error": "Tidak dapat menghapus akun dengan role ini"}), 400

    if not id_admin:

        return jsonify({"error": "id_admin wajib diisi"}), 400

    try:

        uuid.UUID(id_admin)

        uuid.UUID(id_user)

    except ValueError:

        return jsonify({"error": "Format ID tidak valid"}), 400

    check_admin = supabase.table("admin").select("id_admin").eq("id_admin", id_admin).execute()

    if not check_admin.data:

        return jsonify({"error": "Akses ditolak"}), 403

    try:

        id_column = USER_FOREIGN_KEYS[role]

        check_user = supabase.table(role).select(id_column).eq(id_column, id_user).execute()

        if not check_user.data:

            return jsonify({"error": "Pengguna tidak ditemukan"}), 404

        supabase.table(role).delete().eq(id_column, id_user).execute()

        return jsonify({"message": "Pengguna berhasil dihapus"}), 200

    except Exception as e:

        print("Delete user error:", str(e))

        return jsonify({"error": "Terjadi kesalahan saat menghapus pengguna"}), 500

@app.route("/api/users/<role>/<id_user>/password", methods=["PATCH"])

def update_user_password(role, id_user):

    data = request.get_json(silent=True) or {}

    id_admin = str(data.get("id_admin", "")).strip()

    new_password = data.get("new_password", "")

    if role not in ["petugas", "nasabah"]:

        return jsonify({"error": "Role tidak valid"}), 400

    if not id_admin:

        return jsonify({"error": "id_admin wajib diisi"}), 400

    if not new_password or len(str(new_password)) < 8:

        return jsonify({"error": "Password minimal 8 karakter"}), 400

    try:

        uuid.UUID(id_admin)

        uuid.UUID(id_user)

    except ValueError:

        return jsonify({"error": "Format ID tidak valid"}), 400

    check_admin = supabase.table("admin").select("id_admin").eq("id_admin", id_admin).execute()

    if not check_admin.data:

        return jsonify({"error": "Akses ditolak"}), 403

    try:

        id_column = USER_FOREIGN_KEYS[role]

        check_user = supabase.table(role).select(id_column).eq(id_column, id_user).execute()

        if not check_user.data:

            return jsonify({"error": "Pengguna tidak ditemukan"}), 404

        hashed_pw = bcrypt.hashpw(str(new_password).encode("utf-8"), bcrypt.gensalt())

        supabase.table(role).update({"password": hashed_pw.decode("utf-8")}).eq(id_column, id_user).execute()

        return jsonify({"message": "Password berhasil diperbarui"}), 200

    except Exception as e:

        print("Update password error:", str(e))

        return jsonify({"error": "Terjadi kesalahan saat memperbarui password"}), 500

@app.route("/api/profile/<user_type>/<id_user>", methods=["PATCH"])

def update_profile(user_type, id_user):

    try:

        data = request.get_json(silent=True) or {}

        updated_user = data.get("updatedUser")

        if not isinstance(updated_user, dict) or not updated_user:

            return jsonify({

                "error": "Data profile tidak ditemukan"

            }), 400

        allowed_users = {

            "admin": {

                "table": "admin",

                "column": "id_admin"

            },

            "petugas": {

                "table": "petugas",

                "column": "id_petugas"

            },

            "nasabah": {

                "table": "nasabah",

                "column": "id_nasabah"

            }

        }

        user_type = user_type.lower().strip()

        if user_type not in allowed_users:

            return jsonify({

                "error": "Jenis akun tidak valid"

            }), 400

        user_config = allowed_users[user_type]

        table = user_config["table"]

        id_column = user_config["column"]

        try:

            id_user = str(uuid.UUID(id_user))

        except ValueError:

            return jsonify({

                "error": "Format ID User tidak valid"

            }), 400

        check_user = (

            supabase.table(table)

            .select(f"{id_column}, email, nama")

            .eq(id_column, id_user)

            .execute()

        )

        if not check_user.data:

            return jsonify({

                "error": "User tidak ditemukan"

            }), 404

        current_user = check_user.data[0]

        name = updated_user.get("name")

        email = updated_user.get("email")

        password = updated_user.get("password")

        if not isinstance(name, str) or not name.strip():

            return jsonify({

                "error": "Nama wajib diisi!"

            }), 400

        if not isinstance(email, str) or not email.strip():

            return jsonify({

                "error": "Email wajib diisi!"

            }), 400

        name = name.strip()

        email = email.strip().lower()

        if password is not None and not isinstance(password, str):

            return jsonify({

                "error": "Format password tidak valid"

            }), 400

        validate = validateUsersData(

            email,

            name,

            password if password else None

        )

        if validate:

            return jsonify({

                "error": validate

            }), 400

        if email != current_user["email"].lower():

            check_email = (

                supabase.table(table)

                .select(id_column)

                .eq("email", email)

                .execute()

            )

            if check_email.data:

                return jsonify({

                    "error": "Email sudah digunakan"

                }), 409

        update_data = {

            "nama": name,

            "email": email

        }

        if password:

            if len(password) < 8:

                return jsonify({

                    "error": "Password minimal 8 karakter"

                }), 400

            hashed_password = bcrypt.hashpw(

                password.encode("utf-8"),

                bcrypt.gensalt()

            )

            update_data["password"] = hashed_password.decode("utf-8")

        response = (

            supabase.table(table)

            .update(update_data)

            .eq(id_column, id_user)

            .execute()

        )

        if not response.data:

            return jsonify({

                "error": "Gagal memperbarui profile"

            }), 400

        user_data = response.data[0]

        filtered_user = {

            "id": user_data.get(id_column),

            "name": user_data.get("nama"),

            "email": user_data.get("email"),

            "user_type": user_type

        }

        return jsonify({

            "message": "Profile berhasil diperbarui",

            "data": filtered_user

        }), 200

    except Exception as e:

        print("Update profile error:", str(e))

        return jsonify({

            "error": "Terjadi kesalahan server"

        }), 500

@app.route("/api/profile/<user_type>/<id_user>", methods=["DELETE"])

def delete_profile(user_type, id_user):

    try:

        allowed_users = {

            "admin": {

                "table": "admin",

                "column": "id_admin"

            },

            "petugas": {

                "table": "petugas",

                "column": "id_petugas"

            },

            "nasabah": {

                "table": "nasabah",

                "column": "id_nasabah"

            }

        }

        user_type = user_type.lower().strip()

        if user_type not in allowed_users:

            return jsonify({

                "error": "Jenis akun tidak valid"

            }), 400

        # Akun admin tidak boleh dihapus

        if user_type == "admin":

            return jsonify({

                "error": "Akun admin tidak dapat dihapus"

            }), 403

        user_config = allowed_users[user_type]

        table = user_config["table"]

        id_column = user_config["column"]

        try:

            id_user = str(uuid.UUID(id_user))

        except ValueError:

            return jsonify({

                "error": "Format ID User tidak valid"

            }), 400

        user = (

            supabase.table(table)

            .select(id_column)

            .eq(id_column, id_user)

            .execute()

        )

        if not user.data:

            return jsonify({

                "error": "User tidak ditemukan"

            }), 404

        history_foreign_key = {

            "admin": "id_admin",

            "petugas": "id_petugas",

            "nasabah": "id_nasabah"

        }

        foreign_key = history_foreign_key[user_type]

        history_res = (

            supabase.table("riwayat")

            .select("id_riwayat, gambar")

            .eq(foreign_key, id_user)

            .execute()

        )

        histories = history_res.data or []

        file_paths = []

        for item in histories:

            image_url = item.get("gambar")

            if not image_url:

                continue

            try:

                parsed_url = urlparse(image_url)

                path = unquote(parsed_url.path)

                # Contoh:

                # /storage/v1/object/public/images/detection-123.jpg

                marker = "/images/"

                if marker in path:

                    filename = path.split(marker, 1)[1]

                    if filename:

                        file_paths.append(filename)

            except Exception as e:

                print("Extract image path error:", str(e))

        file_paths = list(set(file_paths))

        if histories:

            delete_history = (

                supabase.table("riwayat")

                .delete()

                .eq(foreign_key, id_user)

                .execute()

            )

            if delete_history.data is None:

                raise Exception("Gagal menghapus data riwayat")

        delete_user = (

            supabase.table(table)

            .delete()

            .eq(id_column, id_user)

            .execute()

        )

        if not delete_user.data:

            return jsonify({

                "error": "Gagal menghapus akun pengguna"

            }), 500

        deleted_files = []

        storage_error = None

        if file_paths:

            try:

                supabase.storage.from_("images").remove(

                    file_paths

                )

                deleted_files = file_paths

            except Exception as e:

                storage_error = str(e)

                print("Storage delete error:", storage_error)

        response = {

            "message": "Akun dan seluruh riwayat berhasil dihapus",

            "user_type": user_type,

            "id_user": id_user,

            "total_history_deleted": len(histories),

            "deleted_files": deleted_files

        }

        if storage_error:

            response["warning"] = (

                "Akun dan riwayat berhasil dihapus, "

                "tetapi gambar gagal dihapus dari Storage"

            )

        return jsonify(response), 200

    except Exception as e:

        print("ERROR DELETE PROFILE:", str(e))

        return jsonify({

            "error": "Terjadi kesalahan saat menghapus profile"

        }), 500

uploaded_users = set()

processing_users = set()

upload_lock = Lock()

def send_response(data):

    emit("response_back", data, to=request.sid)

@socketio.on("image")

def handle_image(data):

    sid = request.sid

    filename = None

    upload_started = False

    try:

        # VALIDASI INPUT

        image_data = data.get("image")

        user_id = data.get("user_id")

        user_type = data.get("user_type")

        if not image_data or not user_id or not user_type:

            send_response({

                "error": "Data gambar, user_id, dan user_type wajib diisi",

                "type": "stream"

            })

            return

        # Validasi jenis user

        foreign_key = USER_FOREIGN_KEYS.get(user_type.lower())

        if not foreign_key:

            send_response({

                "error": "Jenis user tidak valid",

                "type": "stream"

            })

            return

        # Validasi UUID

        try:

            user_id = str(uuid.UUID(str(user_id)))

        except ValueError:

            send_response({

                "error": "User ID tidak valid",

                "type": "stream"

            })

            return

        # DECODE IMAGE

        encoded = image_data.split(",", 1)[-1]

        img_bytes = base64.b64decode(

            encoded,

            validate=True

        )

        np_arr = np.frombuffer(img_bytes, np.uint8)

        frame = cv2.imdecode(

            np_arr,

            cv2.IMREAD_COLOR

        )

        if frame is None:

            raise ValueError("Gambar tidak dapat diproses")

        # DETEKSI SAMPAH

        result_frame, label, label_with_accuracy, accuracy = detect_trash(

            frame,

            sid=sid

        )

        _, buffer = cv2.imencode(".jpg", result_frame)

        if buffer is None:

            raise ValueError("Gagal melakukan encoding gambar")

        base64_result = base64.b64encode(

            buffer.tobytes()

        ).decode("utf-8")

        response_data = {

            "image": "data:image/jpeg;base64," + base64_result,

            "label": label,

            "label_with_accuracy": label_with_accuracy,

            "accuracy": accuracy,

            "image_url": None,

            "type": "stream"

        }

        # CEK LABEL

        if label is None:

            send_response(response_data)

            return

        # CEK DUPLIKASI UPLOAD

        with upload_lock:

            if sid in uploaded_users or sid in processing_users:

                send_response(response_data)

                return

            processing_users.add(sid)

            upload_started = True

        # VALIDASI LABEL

        validate_label = validateHistoryData(label, None)

        if validate_label:

            response_data["error"] = validate_label

            send_response(response_data)

            return

        # UPLOAD IMAGE KE SUPABASE STORAGE

        filename = f"detection-{uuid.uuid4()}.jpg"

        supabase.storage.from_("images").upload(

            path=filename,

            file=buffer.tobytes(),

            file_options={

                "content-type": "image/jpeg"

            }

        )

        public_url = supabase.storage.from_("images").get_public_url(

            filename

        )

        # VALIDASI URL DAN LABEL

        validate_url = validateHistoryData(label, public_url)

        if validate_url:

            supabase.storage.from_("images").remove([filename])

            filename = None

            response_data["error"] = validate_url

            send_response(response_data)

            return

        # Validasi ketersediaan user dan FK yang sesuai

        actual_table = user_type.lower()

        actual_fk = foreign_key

        user_check = (

            supabase.table(actual_table)

            .select(actual_fk)

            .eq(actual_fk, user_id)

            .execute()

        )

        if not user_check.data:

            found = False

            for r_name, fk_name in USER_FOREIGN_KEYS.items():

                if r_name == actual_table:

                    continue

                other_check = (

                    supabase.table(r_name)

                    .select(fk_name)

                    .eq(fk_name, user_id)

                    .execute()

                )

                if other_check.data:

                    actual_table = r_name

                    actual_fk = fk_name

                    found = True

                    break

            if not found:

                if filename is not None:

                    try:

                        supabase.storage.from_("images").remove([filename])

                    except Exception:

                        pass

                    filename = None

                send_response({

                    "error": "User tidak ditemukan di database. Silakan login kembali.",

                    "type": "stream"

                })

                return

        # INSERT KE DATABASE RIWAYAT

        accuracy_value = float(

            str(accuracy).replace("%", "").strip()

        )

        history_data = {

            "id_riwayat": str(uuid.uuid4()),

            "label": label,

            "gambar": public_url,

            "akurasi": accuracy_value,

            "id_admin": None,

            "id_petugas": None,

            "id_nasabah": None

        }

        history_data[actual_fk] = user_id

        supabase.table("riwayat").insert(

            history_data

        ).execute()

        # UPDATE STATUS UPLOAD

        with upload_lock:

            uploaded_users.add(sid)

        response_data["image_url"] = public_url

        send_response(response_data)

    except Exception as e:

        print("Socket error:", str(e))

        # Hapus gambar jika proses database gagal

        if filename is not None:

            try:

                supabase.storage.from_("images").remove([filename])

            except Exception as storage_error:

                print("Storage cleanup error:", storage_error)

        send_response({

            "error": str(e),

            "type": "stream"

        })

    finally:

        # Lepaskan status processing

        if upload_started:

            with upload_lock:

                processing_users.discard(sid)

@socketio.on("disconnect")

def handle_disconnect():

    sid = request.sid

    with upload_lock:

        uploaded_users.discard(sid)

        processing_users.discard(sid)

    clear_history(sid)

if __name__ == '__main__':
    is_debug = os.environ.get("FLASK_DEBUG", "true").lower() in ["true", "1"]
    use_reloader = os.environ.get("FLASK_USE_RELOADER", str(is_debug)).lower() in ["true", "1"]
    socketio.run(app, host='0.0.0.0', port=3000, debug=is_debug, use_reloader=use_reloader, allow_unsafe_werkzeug=True)