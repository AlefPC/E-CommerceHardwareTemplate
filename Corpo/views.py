from application import app
from bd import HDD, PERIFERICOS, GPU, MOTHERBOARD, RAM, SSD, FAN
from database import get_db, get_product
from pathlib import Path
from decimal import Decimal
from flask import (
    abort,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

HOMEPAGE_URL = "http://localhost:4000/homepage"
LOGIN_URL = "http://localhost:4001/login"
CATALOGO_URL = "http://localhost:4002/catalogo"
PRODUTO_URL = "http://localhost:4003/produto/"
CARRINHO_URL = "http://localhost:4004/carrinho"
PRODUTOS = HDD + PERIFERICOS + GPU + MOTHERBOARD + RAM + SSD + FAN

# Links de Rotas

@app.route("/")
def gateway():
    return render_template("gateway.html")

@app.route("/homepage")
def homepage():
    return render_template(
        "homepage.html",
        homepage_url=HOMEPAGE_URL,
        login_url=LOGIN_URL,
        catalogo_url=CATALOGO_URL,
        ofertas=[SSD[0], GPU[0], RAM[0], MOTHERBOARD[2]])

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("usuario", "").strip()
        password = request.form.get("senha", "")
        user = get_db().execute(
            "SELECT usuario, senha_hash FROM usuarios WHERE usuario = ?",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["senha_hash"], password):
            session.clear()
            session["username"] = user["usuario"]
            return redirect(HOMEPAGE_URL)

        error = "Usuário ou senha inválidos."

    return render_template(
        "login.html",
        homepage_url=HOMEPAGE_URL,
        login_url=LOGIN_URL,
        catalogo_url=CATALOGO_URL,
        carrinho_url=CARRINHO_URL,
        produtos=PRODUTOS,
        error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(HOMEPAGE_URL)

def parse_price(price):
    normalized_price = price.replace("R$", "").strip().replace(".", "").replace(",", ".")
    return int(Decimal(normalized_price) * 100)


def format_price(price_in_cents):
    whole, cents = divmod(price_in_cents, 100)
    formatted_whole = f"{whole:,}".replace(",", ".")
    return f"R$ {formatted_whole},{cents:02d}"


def get_cart_items():
    cart = session.get("cart", {})
    items = []
    valid_cart = {}

    if not isinstance(cart, dict):
        session["cart"] = {}
        return items

    for product_id, quantity in cart.items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        product = get_product(product_id)
        if product is None or quantity < 1:
            continue

        valid_cart[str(product_id)] = quantity
        unit_price = parse_price(product["preco"])
        shipping = parse_price(product["frete"])
        items.append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "unit_price_display": format_price(unit_price),
            "shipping": shipping,
            "shipping_display": format_price(shipping),
            "total": (unit_price + shipping) * quantity,
            "total_display": format_price((unit_price + shipping) * quantity),
        })

    session["cart"] = valid_cart
    return items


@app.route("/carrinho", methods=["GET", "POST"])
def carrinho():
    if not session.get("username"):
        return redirect(LOGIN_URL)

    if request.method == "POST":
        items = get_cart_items()
        if not items:
            flash("Adicione produtos ao carrinho antes de confirmar a compra.", "error")
            return redirect(url_for("carrinho"))

        session.pop("cart", None)
        flash("Compra confirmada com sucesso!", "success")
        return redirect(url_for("carrinho"))

    items = get_cart_items()
    subtotal = sum(item["unit_price"] * item["quantity"] for item in items)
    shipping_total = sum(item["shipping"] * item["quantity"] for item in items)
    return render_template(
        "carrinho.html",
        homepage_url=HOMEPAGE_URL,
        items=items,
        subtotal=format_price(subtotal),
        shipping_total=format_price(shipping_total),
        total=format_price(subtotal + shipping_total),
        messages=get_flashed_messages(with_categories=True),
    )


@app.route("/carrinho/adicionar/<int:product_id>", methods=["POST"])
def adicionar_ao_carrinho(product_id):
    if not session.get("username"):
        return redirect(LOGIN_URL)

    if get_product(product_id) is None:
        abort(404)

    cart = session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    product_key = str(product_id)
    cart[product_key] = int(cart.get(product_key, 0)) + 1
    session["cart"] = cart
    flash("Produto adicionado ao carrinho.", "success")
    return redirect(url_for("carrinho"))


@app.route("/carrinho/remover/<int:product_id>", methods=["POST"])
def remover_do_carrinho(product_id):
    if not session.get("username"):
        return redirect(LOGIN_URL)

    cart = session.get("cart", {})
    if isinstance(cart, dict):
        cart.pop(str(product_id), None)
        session["cart"] = cart
    return redirect(url_for("carrinho"))

@app.route("/catalogo")
def catalogo():
    return render_template(
        "catalogo.html",
        homepage_url=HOMEPAGE_URL,
        login_url=LOGIN_URL,
        catalogo_url=CATALOGO_URL,
        carrinho_url=CARRINHO_URL,
        produtos=PRODUTOS)

@app.route("/product-images/<path:filename>")
def product_image(filename):
    image_directory = Path(app.root_path) / "Imagens"
    return send_from_directory(image_directory, filename)

@app.route("/produto")
@app.route("/produto/")
def produto():
    return redirect(url_for("produto_detalhe", product_id=PRODUTOS[0]["id"]))

@app.route("/produto/<int:product_id>")
def produto_detalhe(product_id):
    product = get_product(product_id)
    if product is None:
        abort(404)

    return render_template(
        "produto.html",
        homepage_url=HOMEPAGE_URL,
        login_url=LOGIN_URL,
        catalogo_url=CATALOGO_URL,
        carrinho_url=CARRINHO_URL,
        product=product)