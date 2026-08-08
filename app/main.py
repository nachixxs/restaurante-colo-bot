from typing import Any

from fastapi import FastAPI

from app.claude_client import (
    SYSTEM_PROMPT_BOT,
    client,
    procesar_respuesta_reserva,
    tool_crear_reserva,
)
from app.conversaciones import agregar_mensaje, conversaciones
from app.models import MensajeEntrante

app = FastAPI()


@app.post("/webhook")
async def recibir_mensaje(mensaje: MensajeEntrante) -> dict[str, Any]:
    historial = agregar_mensaje(mensaje.numero, "user", mensaje.texto)

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT_BOT,
        tools=[tool_crear_reserva],
        messages=historial,
    )

    resultado = procesar_respuesta_reserva(response)
    if resultado is not None:
        # Reserva confirmada: se corta el historial de este número para que
        # no arrastre datos (ej. cantidad de personas) hacia una reserva
        # nueva y distinta del mismo cliente.
        conversaciones.pop(mensaje.numero, None)
        return resultado

    # Claude no usó la tool (p. ej. pidió un dato faltante en texto libre)
    texto_respuesta = "".join(
        bloque.text for bloque in response.content if bloque.type == "text"
    )
    agregar_mensaje(mensaje.numero, "assistant", texto_respuesta)
    return {"respuesta": texto_respuesta}
