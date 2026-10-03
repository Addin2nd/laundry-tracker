"""Koneksi SQLite dan skema database."""
import sqlite3

import click
from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kode        TEXT UNIQUE NOT NULL,
    pelanggan   TEXT NOT NULL,
    telepon     TEXT NOT NULL,
    layanan     TEXT NOT NULL,
    berat_kg    REAL NOT NULL,
    total       INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'diterima',
    catatan     TEXT DEFAULT '',
    dibuat      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    diperbarui  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    get_db().executescript(SCHEMA)


@click.command("init-db")
def init_db_command() -> None:
    """Buat tabel database."""
    init_db()
    click.echo("Database siap.")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    with app.app_context():
        init_db()
