import os

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


def probar_extraccion() -> None:
    mensaje_prueba = "quiero una mesa para 4 el sábado a las 21hs"

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool_crear_reserva],
        messages=[{"role": "user", "content": mensaje_prueba}],
    )

    print(response.content)


if __name__ == "__main__":
    probar_extraccion()
