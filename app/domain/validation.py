# Conjuntos de valores permitidos
ALLOWED_STATUS = {"NEW", "PROCESSING", "DONE", "FAILED"}
ALLOWED_TYPES = {"ORDER", "PAYMENT", "SHIPMENT"}

def validate_event(event_type: str, event_status: str) -> list[dict]:
    # Lista de erros de validação encontrados
    errors = []

    # Valida se o tipo do evento é permitido
    if event_type not in ALLOWED_TYPES:
        errors.append({
            "category": "BUSINESS",
            "field": "event_type",
            "rule": "ALLOWED_TYPES",
            "message": "event_type inválido",
            "severity": "HIGH",
        })

    # Valida se o status do evento é permitido
    if event_status not in ALLOWED_STATUS:
        errors.append({
            "category": "BUSINESS",
            "field": "event_status",
            "rule": "ALLOWED_STATUS",
            "message": "event_status inválido",
            "severity": "HIGH",
        })

    # Retorna todas as violações encontradas
    return errors
