import os
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Una key vacía no rompe al construir el cliente: revienta recién en la primera
# llamada, y lo hace con un TypeError que NO es subclase de anthropic.APIError,
# así que se escapa del except del ruteo en main.py y termina en un 500 con el
# bot mudo. Igual que el FAQ vacío, es un error de deploy y no una condición
# válida de runtime, así que corta el arranque. Si la variable directamente no
# está, el os.environ[...] ya tira KeyError, que también mata el arranque.
api_key = os.environ["ANTHROPIC_API_KEY"].strip()
if not api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY está vacía en el .env. Completala con la key real "
        "(ver .env.example)."
    )

client = anthropic.Anthropic(api_key=api_key)

# Mensajes de resguardo del Día 9: se muestran cuando falla una llamada
# externa (Claude o Voyage) y el bot no puede seguir el flujo normal.
MSG_ERROR_RUTEO = "Perdón, tuve un problema para procesar tu mensaje. ¿Me lo repetís?"
MSG_ERROR_BUSQUEDA = "No pude buscar esa información ahora mismo, probá de nuevo en un momento."
MSG_SIN_MATCH = "No tengo esa información a mano, te va a responder alguien del local."

SYSTEM_PROMPT_BOT = (
    "Sos el asistente de un restaurante y atendés a los clientes por "
    "WhatsApp. Tenés dos herramientas y siempre tenés que usar la que "
    "corresponda:\n"
    "- crear_reserva: cuando el cliente quiere reservar una mesa. Si falta "
    "un dato obligatorio (fecha, hora o cantidad de personas), preguntalo "
    "directamente en vez de inventarlo o asumirlo, y no uses la tool hasta "
    "tenerlos todos.\n"
    "- consultar_faq: cuando el cliente pregunta cualquier otra cosa sobre "
    "el restaurante. Nunca contestes esas preguntas de memoria: no sabés "
    "nada del restaurante que no venga de consultar_faq."
)

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

tool_consultar_faq: dict = {
    "name": "consultar_faq",
    "description": (
        "Busca la respuesta en las preguntas frecuentes del restaurante. "
        "Usala cuando el cliente pregunta algo sobre el restaurante que no "
        "es pedir una mesa: horarios, menú y platos, opciones sin TACC, "
        "wifi, mascotas, estacionamiento, medios de pago o ubicación."
    ),
    # Vacío a propósito: la tool no nos tiene que devolver ningún dato, sirve
    # solo para que Claude marque que el mensaje es una pregunta y no una
    # reserva. La búsqueda la hacemos nosotros con el texto del cliente.
    "input_schema": {
        "type": "object",
        "properties": {},
    },
}


def probar_extraccion(mensaje_prueba: str) -> anthropic.types.Message:
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT_BOT,
        tools=[tool_crear_reserva],
        messages=[{"role": "user", "content": mensaje_prueba}],
    )

    print(response.content)
    return response


def hay_tool_use(response: anthropic.types.Message, nombre_tool: str) -> bool:
    return any(
        bloque.type == "tool_use" and bloque.name == nombre_tool
        for bloque in response.content
    )


def extraer_texto(response: anthropic.types.Message) -> str:
    return "".join(bloque.text for bloque in response.content if bloque.type == "text")


def responder_con_contexto(contexto: str, historial: list[dict[str, str]]) -> str:
    """Segunda llamada a Claude para el camino de FAQ: responde la pregunta
    del cliente apoyándose solo en los fragmentos que trajo la búsqueda.
    """
    system_prompt = (
        "Sos el asistente de un restaurante y atendés por WhatsApp. Respondé "
        "la última pregunta del cliente usando únicamente la información del "
        "contexto de abajo. Si el contexto no alcanza para responderla, decí "
        "que no tenés ese dato a mano y que lo va a responder alguien del "
        "local. Nunca inventes información del restaurante que no esté en el "
        "contexto. Contestá corto y natural, como un mensaje de WhatsApp.\n\n"
        f"Contexto (preguntas frecuentes del restaurante):\n{contexto}"
    )

    # Sin tools acá: en esta llamada solo queremos texto, no otra decisión de
    # ruteo. Va el historial completo para que el modelo entienda repreguntas
    # encadenadas ("¿y los domingos?").
    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=system_prompt,
            messages=historial,
        )
    except anthropic.APIError:
        return MSG_ERROR_BUSQUEDA

    return extraer_texto(response)


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
    mensajes_prueba = (
        "quiero una mesa para 4 el sábado a las 21hs",
        "quiero reservar una mesa",
    )
    for mensaje_prueba in mensajes_prueba:
        print(f"--- Mensaje: {mensaje_prueba!r} ---")
        response = probar_extraccion(mensaje_prueba)
        resultado = procesar_respuesta_reserva(response)
        print(resultado)
        print()
