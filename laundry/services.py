"""Logika bisnis: harga, status, dan kode order. Dipisah dari route agar mudah dites."""
import secrets
from datetime import datetime

LAYANAN = {
    "cuci_kering": {"nama": "Cuci Kering", "harga_per_kg": 6000},
    "cuci_setrika": {"nama": "Cuci + Setrika", "harga_per_kg": 8000},
    "setrika": {"nama": "Setrika Saja", "harga_per_kg": 5000},
    "express": {"nama": "Express 6 Jam", "harga_per_kg": 15000},
}

STATUS = ["diterima", "dicuci", "siap_diambil", "selesai"]
STATUS_LABEL = {
    "diterima": "Diterima",
    "dicuci": "Sedang Dicuci",
    "siap_diambil": "Siap Diambil",
    "selesai": "Selesai",
}

MIN_BERAT_KG = 1.0


def hitung_total(layanan: str, berat_kg: float) -> int:
    """Hitung total harga. Berat minimal dibulatkan ke MIN_BERAT_KG."""
    if layanan not in LAYANAN:
        raise ValueError(f"Layanan tidak dikenal: {layanan}")
    if berat_kg <= 0:
        raise ValueError("Berat harus lebih dari 0")
    berat = max(berat_kg, MIN_BERAT_KG)
    return round(berat * LAYANAN[layanan]["harga_per_kg"])


def status_berikutnya(status: str) -> str | None:
    """Kembalikan status selanjutnya, atau None kalau sudah selesai."""
    idx = STATUS.index(status)
    return STATUS[idx + 1] if idx + 1 < len(STATUS) else None


def buat_kode(now: datetime | None = None) -> str:
    """Kode order unik & mudah dibaca, contoh: LDR-261003-7F3A."""
    now = now or datetime.now()
    return f"LDR-{now:%y%m%d}-{secrets.token_hex(2).upper()}"


def normalisasi_telepon(telepon: str) -> str:
    """Ubah 08xx / +628xx menjadi format 628xx (siap untuk link WhatsApp)."""
    digit = "".join(c for c in telepon if c.isdigit())
    if digit.startswith("0"):
        digit = "62" + digit[1:]
    if not digit.startswith("62") or not 10 <= len(digit) <= 15:
        raise ValueError("Nomor telepon tidak valid")
    return digit
