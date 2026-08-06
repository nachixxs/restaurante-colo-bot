import os
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

tool_crear_reserva: dict = {
    "name": "crear_reserva",
    "description": (
        "Registra una reserva de mesa cuando el cliente da fecha, hora "
        "y cantidad de personas para comer en el restaurante."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "fecha": {
                "type": "string",
                "description": "Fecha para la que se pide la reserva",
            },
            "hora": {
                "type": "string",
                "description": "Hora a la que se pide la mesa",
            },
            "personas": {
                "type": "integer",
                "description": "Cantidad de personas para la reserva",
            },
            "nombre": {
                "type": "string",
                "description": "Nombre a nombre de quien queda la reserva",
            },
        },
        "required": ["fecha", "hora", "personas"],
    },
}


def probar_extraccion() -> anthropic.types.Message:
    mensaje_prueba = "quiero una mesa para 4 el sábado a las 21hs"

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool_crear_reserva],
        messages=[{"role": "user", "content": mensaje_prueba}],
    )

    print(response.content)
    return response


def procesar_respuesta_reserva(
    response: anthropic.types.Message,
) -> dict[str, Any] | None:
    for bloque in response.content:
        if bloque.type == "tool_use" and bloque.name == "crear_reserva":
            datos = bloque.input
            confirmacion = (
                f"Confirmado: mesa para {datos['personas']} "
                f"el {datos['fecha']} a las {datos['hora']}"
            )
            return {
                "respuesta": confirmacion,
                "reserva": datos,
            }

    return None


if __name__ == "__main__":
    response = probar_extraccion()
    resultado = procesar_respuesta_reserva(response)
    print(resultado)
