conversaciones: dict[str, list[dict[str, str]]] = {}  # numero -> lista de mensajes


def agregar_mensaje(numero: str, rol: str, texto: str) -> list[dict[str, str]]:
    historial = conversaciones.setdefault(numero, [])
    historial.append({"role": rol, "content": texto})
    return historial
