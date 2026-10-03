"""Route halaman admin dan halaman lacak untuk pelanggan."""
from urllib.parse import quote

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from . import services as svc
from .db import get_db

bp = Blueprint("laundry", __name__)


@bp.app_context_processor
def inject_globals():
    return {"LAYANAN": svc.LAYANAN, "STATUS": svc.STATUS, "STATUS_LABEL": svc.STATUS_LABEL}


@bp.get("/")
def dashboard():
    db = get_db()
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()

    sql = "SELECT * FROM orders WHERE 1=1"
    params: list = []
    if status in svc.STATUS:
        sql += " AND status = ?"
        params.append(status)
    if q:
        sql += " AND (pelanggan LIKE ? OR kode LIKE ? OR telepon LIKE ?)"
        params += [f"%{q}%"] * 3
    sql += " ORDER BY dibuat DESC LIMIT 100"
    orders = db.execute(sql, params).fetchall()

    stats = db.execute(
        """
        SELECT
          COALESCE(SUM(CASE WHEN date(dibuat) = date('now','localtime') THEN total END), 0) AS omzet_hari_ini,
          COUNT(CASE WHEN date(dibuat) = date('now','localtime') THEN 1 END) AS order_hari_ini,
          COUNT(CASE WHEN status != 'selesai' THEN 1 END) AS order_aktif,
          COUNT(CASE WHEN status = 'siap_diambil' THEN 1 END) AS siap_diambil
        FROM orders
        """
    ).fetchone()
    return render_template("dashboard.html", orders=orders, stats=stats, status=status, q=q)


@bp.route("/order/baru", methods=["GET", "POST"])
def order_baru():
    if request.method == "POST":
        form = request.form
        try:
            pelanggan = form["pelanggan"].strip()
            if not pelanggan:
                raise ValueError("Nama pelanggan wajib diisi")
            telepon = svc.normalisasi_telepon(form["telepon"])
            layanan = form["layanan"]
            berat = float(form["berat_kg"].replace(",", "."))
            total = svc.hitung_total(layanan, berat)
        except (KeyError, ValueError) as e:
            flash(str(e) if str(e) else "Data tidak lengkap", "error")
            return render_template("order_form.html", form=form), 400

        kode = svc.buat_kode()
        db = get_db()
        db.execute(
            "INSERT INTO orders (kode, pelanggan, telepon, layanan, berat_kg, total, catatan)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (kode, pelanggan, telepon, layanan, berat, total, form.get("catatan", "").strip()),
        )
        db.commit()
        flash(f"Order {kode} berhasil dibuat.", "ok")
        return redirect(url_for("laundry.detail", kode=kode))
    return render_template("order_form.html", form={})


def _ambil_order(kode: str):
    order = get_db().execute("SELECT * FROM orders WHERE kode = ?", (kode,)).fetchone()
    if order is None:
        abort(404)
    return order


@bp.get("/order/<kode>")
def detail(kode):
    order = _ambil_order(kode)
    lacak_url = url_for("laundry.lacak", kode=kode, _external=True)
    pesan = (
        f"Halo {order['pelanggan']}, order laundry Anda {kode} "
        f"berstatus: {svc.STATUS_LABEL[order['status']]}. Lacak di {lacak_url}"
    )
    wa_link = f"https://wa.me/{order['telepon']}?text={quote(pesan)}"
    return render_template(
        "detail.html", order=order, wa_link=wa_link,
        berikutnya=svc.status_berikutnya(order["status"]),
    )


@bp.post("/order/<kode>/maju")
def majukan_status(kode):
    order = _ambil_order(kode)
    baru = svc.status_berikutnya(order["status"])
    if baru:
        db = get_db()
        db.execute(
            "UPDATE orders SET status = ?, diperbarui = datetime('now','localtime') WHERE kode = ?",
            (baru, kode),
        )
        db.commit()
        flash(f"Status diubah menjadi {svc.STATUS_LABEL[baru]}.", "ok")
    return redirect(url_for("laundry.detail", kode=kode))


@bp.get("/lacak")
def lacak():
    kode = request.args.get("kode", "").strip().upper()
    order = None
    if kode:
        order = get_db().execute(
            "SELECT kode, layanan, berat_kg, total, status, dibuat, diperbarui"
            " FROM orders WHERE kode = ?",
            (kode,),
        ).fetchone()
    return render_template("lacak.html", kode=kode, order=order)
