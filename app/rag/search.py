import json
import sys
import time

import numpy as np
from voyageai.error import VoyageError

from app.rag.embeddings import RUTA_EMBEDDINGS, vo

# Medido el Día 9 con 8 preguntas reales contra el FAQ (ver
# scripts/check_scores.py): el mejor match de una pregunta cubierta por el
# FAQ dio 0.5635 de similitud, y el de una pregunta fuera de tema dio 0.3278.
# El umbral es el punto medio entre ambos.
UMBRAL_SIMILITUD = 0.45


class BusquedaFallidaError(Exception):
    """Se lanza cuando falla la llamada a Voyage para embedear la pregunta.

    buscar_relevantes() la lanza en vez de devolver algún valor especial,
    para no mezclar "no hubo resultados" (una lista vacía, un caso válido)
    con "no se pudo ni intentar buscar" (un error real que el llamador tiene
    que manejar distinto, con el mensaje de resguardo correspondiente).
    """


def cargar_faq_vectores() -> list[tuple[str, list[float]]]:
    with open(RUTA_EMBEDDINGS, encoding="utf-8") as f:
        return json.load(f)


def similitud_coseno(a: list[float], b: list[float]) -> float:
    a_np, b_np = np.array(a), np.array(b)
    return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))


def buscar_relevantes(
    pregunta: str, faq_vectores: list[tuple[str, list[float]]], top_k: int = 3
) -> list[tuple[float, str]]:
    """Devuelve los top_k fragmentos más parecidos a la pregunta, cada uno
    junto con su score de similitud (antes se descartaba y solo quedaba el
    texto) para que el llamador pueda compararlo contra UMBRAL_SIMILITUD.
    """
    try:
        emb_pregunta = vo.embed([pregunta], model="voyage-4", input_type="query").embeddings[0]
    except VoyageError as e:
        raise BusquedaFallidaError("Falló el embedding de la pregunta") from e

    scores = [(similitud_coseno(emb_pregunta, vector), texto) for texto, vector in faq_vectores]
    scores.sort(reverse=True)
    return scores[:top_k]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    faq_vectores = cargar_faq_vectores()

    preguntas_de_prueba = [
        "puedo ir con mi perro?",
        "hay internet en el local?",
        "les puedo pagar con visa?",
        "tienen algo para alguien celíaco?",
        "hasta que hora puedo ir un finde?",
    ]

    # La cuenta gratis de Voyage limita a 3 requests por minuto: sin esta
    # pausa, la 4ta pregunta en adelante tira RateLimitError.
    for i, pregunta in enumerate(preguntas_de_prueba):
        if i > 0:
            time.sleep(20)
        resultados = buscar_relevantes(pregunta, faq_vectores)
        print(f"\nPregunta: {pregunta}")
        for j, (score, texto) in enumerate(resultados, start=1):
            print(f"  {j}. ({score:.4f}) {texto}")
