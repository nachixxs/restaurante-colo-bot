from typing import Any

from fastapi import FastAPI

from app.claude_client import (
    SYSTEM_PROMPT_RESERVA,
    client,
    procesar_respuesta_reserva,
    tool_crear_reserva,
)
from app.conversaciones import agregar_mensaje
from app.models import MensajeEntrante

app = FastAPI()


@app.post("/webhook")
async def recibir_mensaje(mensaje: MensajeEntrante) -> dict[str, Any]:
    historial = agregar_mensaje(mensaje.numero, "user", mensaje.texto)

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT_RESERVA,
        tools=[tool_crear_reserva],
        messages=historial,
    )

    resultado = procesar_respuesta_reserva(response)
    if resultado is not None:
        agregar_mensaje(mensaje.numero, "assistant", resultado["respuesta"])
        return resultado

    # Claude no usó la tool (p. ej. pidió un dato faltante en texto libre)
    texto_respuesta = "".join(
        bloque.text for bloque in response.content if bloque.type == "text"
    )
    agregar_mensaje(mensaje.numero, "assistant", texto_respuesta)
    return {"respuesta": texto_respuesta}
