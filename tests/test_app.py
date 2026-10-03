import re
from datetime import datetime

import pytest

from laundry import create_app
from laundry import services as svc


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    return app.test_client()


def buat_order(client, **override):
    data = {"pelanggan": "Budi", "telepon": "0812-3456-7890", "layanan": "cuci_setrika", "berat_kg": "3"}
    data.update(override)
    return client.post("/order/baru", data=data)


# --- services ---------------------------------------------------------------

def test_hitung_total():
    assert svc.hitung_total("cuci_setrika", 3) == 24000
    assert svc.hitung_total("cuci_kering", 0.5) == 6000  # dibulatkan minimal 1 kg


@pytest.mark.parametrize("layanan,berat", [("ngawur", 2), ("setrika", 0), ("setrika", -1)])
def test_hitung_total_invalid(layanan, berat):
    with pytest.raises(ValueError):
        svc.hitung_total(layanan, berat)


def test_status_berikutnya():
    assert svc.status_berikutnya("diterima") == "dicuci"
    assert svc.status_berikutnya("selesai") is None


def test_buat_kode_format():
    kode = svc.buat_kode(datetime(2026, 10, 3))
    assert re.fullmatch(r"LDR-261003-[0-9A-F]{4}", kode)


@pytest.mark.parametrize("masuk,keluar", [
    ("0812-3456-7890", "6281234567890"),
    ("+62 812 3456 7890", "6281234567890"),
])
def test_normalisasi_telepon(masuk, keluar):
    assert svc.normalisasi_telepon(masuk) == keluar


def test_normalisasi_telepon_invalid():
    with pytest.raises(ValueError):
        svc.normalisasi_telepon("12345")


# --- web --------------------------------------------------------------------

def test_dashboard_kosong(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Belum ada order" in res.data


def test_alur_order_lengkap(client):
    res = buat_order(client)
    assert res.status_code == 302
    kode = res.headers["Location"].rsplit("/", 1)[-1]

    detail = client.get(f"/order/{kode}")
    assert b"Rp24.000" in detail.data
    assert b"wa.me/6281234567890" in detail.data

    for _ in range(3):
        client.post(f"/order/{kode}/maju")
    lacak = client.get(f"/lacak?kode={kode.lower()}")
    assert b"Selesai" in lacak.data
    # halaman lacak publik tidak boleh membocorkan nomor HP pelanggan
    assert b"6281234567890" not in lacak.data


def test_order_invalid_ditolak(client):
    res = buat_order(client, telepon="123")
    assert res.status_code == 400
    assert b"tidak valid" in res.data


def test_filter_dan_cari(client):
    buat_order(client, pelanggan="Siti")
    buat_order(client, pelanggan="Andi")
    res = client.get("/?q=siti")
    assert b"Siti" in res.data and b"Andi" not in res.data


def test_order_tidak_ada(client):
    assert client.get("/order/LDR-000000-XXXX").status_code == 404
