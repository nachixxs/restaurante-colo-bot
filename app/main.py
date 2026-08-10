from typing import Any

import anthropic
from fastapi import FastAPI

from app.claude_client import (
    MSG_ERROR_BUSQUEDA,
    MSG_ERROR_RUTEO,
    MSG_SIN_MATCH,
    SYSTEM_PROMPT_BOT,
    client,
    extraer_texto,
    hay_tool_use,
    procesar_respuesta_reserva,
    responder_con_contexto,
    tool_consultar_faq,
    tool_crear_reserva,
)
from app.conversaciones import agregar_mensaje, conversaciones
from app.models import MensajeEntrante
from app.rag.search import (
    UMBRAL_SIMILITUD,
    BusquedaFallidaError,
    buscar_relevantes,
    cargar_faq_vectores,
)

app = FastAPI()

# Se carga una sola vez, al importar el módulo (o sea, cuando arranca uvicorn):
# leer y parsear el JSON de embeddings en cada mensaje sería trabajo repetido
# al pedo, el archivo no cambia mientras el servidor está corriendo.
faq_vectores = cargar_faq_vectores()
# flush=True para que la línea salga aunque la consola esté redirigida a un
# archivo o a un pipe, donde stdout usa buffer por bloques y la retendría.
print(f"FAQ cargado: {len(faq_vectores)} fragmentos", flush=True)


@app.post("/webhook")
async def recibir_mensaje(mensaje: MensajeEntrante) -> dict[str, Any]:
    historial = agregar_mensaje(mensaje.numero, "user", mensaje.texto)

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT_BOT,
            tools=[tool_crear_reserva, tool_consultar_faq],
            messages=historial,
        )
    except anthropic.APIError:
        return {"respuesta": MSG_ERROR_RUTEO}

    # Camino 1 - reserva (Días 3-5). Se chequea primero, así que si Claude
    # devolviera las dos tools en la misma respuesta, gana crear_reserva.
    resultado = procesar_respuesta_reserva(response)
    if resultado is not None:
        # Reserva confirmada: se corta el historial de este número para que
        # no arrastre datos (ej. cantidad de personas) hacia una reserva
        # nueva y distinta del mismo cliente.
        conversaciones.pop(mensaje.numero, None)
        return resultado

    # Camino 2 - pregunta de FAQ (RAG, Días 6-8): buscamos los fragmentos más
    # parecidos a la pregunta y se los pasamos a Claude como contexto.
    if hay_tool_use(response, "consultar_faq"):
        try:
            fragmentos = buscar_relevantes(mensaje.texto, faq_vectores, top_k=3)
        except BusquedaFallidaError:
            return {"respuesta": MSG_ERROR_BUSQUEDA}

        # Si ni el mejor match llega al umbral, no hay contexto relevante:
        # ni vale la pena gastar otra llamada a Claude para "responder" con
        # fragmentos que no tienen que ver con la pregunta.
        mejor_score = fragmentos[0][0]
        if mejor_score < UMBRAL_SIMILITUD:
            return {"respuesta": MSG_SIN_MATCH}

        contexto = "\n".join(texto for _, texto in fragmentos)
        texto_respuesta = responder_con_contexto(contexto, historial)
        agregar_mensaje(mensaje.numero, "assistant", texto_respuesta)
        return {"respuesta": texto_respuesta}

    # Camino 3 - texto libre, sin ninguna tool: es Claude pidiendo un dato
    # obligatorio que falta para la reserva (Día 5).
    texto_respuesta = extraer_texto(response)
    agregar_mensaje(mensaje.numero, "assistant", texto_respuesta)
    return {"respuesta": texto_respuesta}
