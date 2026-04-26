from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# -------------------------
# CREATE UPLOAD FOLDER
# -------------------------
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -------------------------
# FILE TYPE CHECK
# -------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------
# DATABASE CONNECTION
# -------------------------
def get_db():
    return sqlite3.connect("database.db")


# -------------------------
# DATABASE INIT (SAFE)
# -------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # admin table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        image TEXT
    )
    """)

    # pickups table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pickups(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        address TEXT,
        weight TEXT,
        date TEXT
    )
    """)

    # insert admin ONLY if not exists
    cursor.execute("SELECT * FROM admin WHERE username=?", ('janarthan',))
    admin_exists = cursor.fetchone()

    if not admin_exists:
        cursor.execute(
            "INSERT INTO admin (username,password) VALUES (?,?)",
            ('janarthan', 'janarthan2026')
        )

    conn.commit()
    conn.close()


init_db()


# -------------------------
# HOMEPAGE
# -------------------------
@app.route("/")
def home():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    product_list = [
        {"id": p[0], "name": p[1], "price": p[2], "image": p[3]}
        for p in products
    ]

    return render_template("index.html", products=product_list)


# -------------------------
# STATIC PAGES
# -------------------------
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/impact")
def impact():
    return render_template("impact.html")

@app.route("/school")
def school():
    return render_template("school.html")

@app.route("/certification")
def certification():
    return render_template("certification.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


# -------------------------
# SHOP PAGE
# -------------------------
@app.route("/shop")
def shop():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    product_list = [
        {"id": p[0], "name": p[1], "price": p[2], "image": p[3]}
        for p in products
    ]

    return render_template("shop.html", products=product_list)


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )

        admin = cursor.fetchone()
        conn.close()

        if admin:
            session["admin"] = username
            return redirect("/admin")

        return "Invalid login"

    return render_template("login.html")


# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    product_list = [
        {"id": p[0], "name": p[1], "price": p[2], "image": p[3]}
        for p in products
    ]

    return render_template("admin.html", products=product_list)


# -------------------------
# ADD PRODUCT PAGE
# -------------------------
@app.route("/admin/add-product")
def add_product():
    if "admin" not in session:
        return redirect("/login")

    return render_template("add_product.html")


# -------------------------
# SAVE PRODUCT
# -------------------------
@app.route("/admin/save-product", methods=["POST"])
def save_product():
    if "admin" not in session:
        return redirect("/login")

    name = request.form["name"]
    price = request.form["price"]
    image = request.files["image"]

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO products (name,price,image) VALUES (?,?,?)",
            (name, price, filename)
        )

        conn.commit()
        conn.close()

    return redirect("/admin")


# -------------------------
# EDIT PRODUCT
# -------------------------
@app.route("/admin/edit-product/<int:id>")
def edit_product(id):
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    product = cursor.fetchone()

    conn.close()

    return render_template("edit_product.html", product=product)


# -------------------------
# UPDATE PRODUCT
# -------------------------
@app.route("/admin/update-product/<int:id>", methods=["POST"])
def update_product(id):
    if "admin" not in session:
        return redirect("/login")

    name = request.form["name"]
    price = request.form["price"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE products SET name=?, price=? WHERE id=?",
        (name, price, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# -------------------------
# DELETE PRODUCT
# -------------------------
@app.route("/admin/delete-product/<int:id>")
def delete_product(id):
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT image FROM products WHERE id=?", (id,))
    product = cursor.fetchone()

    if product:
        image_file = product[0]
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_file)

        if os.path.exists(image_path):
            os.remove(image_path)

    cursor.execute("DELETE FROM products WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# -------------------------
# SAVE PICKUP
# -------------------------
@app.route("/pickup", methods=["POST"])
def pickup():
    name = request.form["name"]
    phone = request.form["phone"]
    address = request.form["address"]
    weight = request.form["weight"]
    date = request.form["date"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO pickups (name, phone, address, weight, date) VALUES (?,?,?,?,?)",
        (name, phone, address, weight, date)
    )

    conn.commit()
    conn.close()

    return render_template("success.html")


# -------------------------
# VIEW PICKUPS
# -------------------------
@app.route("/admin/pickups")
def view_pickups():
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pickups")
    pickups = cursor.fetchall()

    conn.close()

    pickup_list = [
        {
            "id": p[0],
            "name": p[1],
            "phone": p[2],
            "address": p[3],
            "weight": p[4],
            "date": p[5]
        }
        for p in pickups
    ]

    return render_template("pickups.html", pickups=pickup_list)


# -------------------------
# DELETE PICKUP
# -------------------------
@app.route("/admin/delete-pickup/<int:id>")
def delete_pickup(id):
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pickups WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/pickups")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)