import hashlib
import json
import uuid

def new_request_id() -> str:
    # Gera um identificador único para a requisição
    return uuid.uuid4().hex

def payload_hash(payload: dict) -> str:
    # Serializa o payload de forma determinística
    # sort_keys garante ordem fixa das chaves
    # default=str evita erro com tipos não serializáveis (ex: datetime)
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    # Gera hash SHA-256 do payload
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
