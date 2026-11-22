"""Conversión reversible entre el identificador interno y el código corto."""

import base62


def encode_url_id(url_id: int) -> str:
    if url_id < 0:
        raise ValueError("url_id debe ser positivo")
    return base62.encode(url_id)


def decode_short_code(short_code: str) -> int:
    try:
        url_id = base62.decode(short_code)
    except ValueError as exc:
        raise ValueError("Código corto inválido") from exc
    if encode_url_id(url_id) != short_code:
        raise ValueError("Código corto inválido")
    return url_id
