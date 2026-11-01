def validateUsersData(email, name, password):
    if email and len(email) > 50:
        return "Email tidak boleh melebihi dari 50 karakter!"
    if name and len(name) > 50:
        return "Nama pengguna tidak boleh melebihi dari 50 karakter!"
    if password and len(password) > 20:
        return "Password tidak boleh melebihi dari 20 karakter!"
    
    return None


def validateHistoryData(label, image):
    if label and len(label) > 20:
        return "Label tidak boleh melebihi dari 20 karakter!"
    if image and len(image) > 255:
        return "Gambar tidak boleh melebihi dari 255 karakter!"
    
    return None
