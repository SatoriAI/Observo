import hashlib

from observo import settings


def hash_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return
    return hashlib.sha256(f"{settings.IP_SALT}:{ip_address}".encode()).hexdigest()
