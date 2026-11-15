import sqlite3
from pathlib import Path

from flask import g
from werkzeug.security import generate_password_hash

from bd import HDD, PERIFERICOS, GPU, MOTHERBOARD, RAM, SSD, FAN
from usuarios import USUARIOS

DATABASE_PATH = Path(__file__).with_name("usuarios.sqlite3")
PRODUTOS = HDD + PERIFERICOS + GPU + MOTHERBOARD + RAM + SSD + FAN


def get_products():
    return get_db().execute(
        "SELECT id, nome, descricao, imagem, frete, preco FROM produtos ORDER BY id"
    ).fetchall()


def get_product(product_id):
    return get_db().execute(
        """
        SELECT id, nome, descricao, imagem, frete, preco
        FROM produtos
        WHERE id = ?
        """,
        (product_id,),
    ).fetchone()


def get_db():
    if "database" not in g:
        g.database = sqlite3.connect(DATABASE_PATH)
        g.database.row_factory = sqlite3.Row
    return g.database


def close_db(exception=None):
    database = g.pop("database", None)
    if database is not None:
        database.close()


def init_database():
    with sqlite3.connect(DATABASE_PATH) as database:
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL
            )
            """
        )
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT NOT NULL,
                imagem TEXT NOT NULL,
                frete TEXT NOT NULL,
                preco TEXT NOT NULL
            )
            """
        )
        database.executemany(
            "INSERT OR IGNORE INTO usuarios (usuario, senha_hash) VALUES (?, ?)",
            [
                (user["usuario"], generate_password_hash(user["senha"]))
                for user in USUARIOS
            ],
        )
        database.executemany(
            """
            INSERT INTO produtos (id, nome, descricao, imagem, frete, preco)
            VALUES (:id, :nome, :descricao, :imagem, :frete, :preco)
            ON CONFLICT(id) DO UPDATE SET
                nome = excluded.nome,
                descricao = excluded.descricao,
                imagem = excluded.imagem,
                frete = excluded.frete,
                preco = excluded.preco
            """,
            PRODUTOS,
        )
