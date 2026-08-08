import json
import sys
import time

import numpy as np

from app.rag.embeddings import RUTA_EMBEDDINGS, vo


def cargar_faq_vectores() -> list[tuple[str, list[float]]]:
    with open(RUTA_EMBEDDINGS, encoding="utf-8") as f:
        return json.load(f)


def similitud_coseno(a: list[float], b: list[float]) -> float:
    a_np, b_np = np.array(a), np.array(b)
    return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))


def buscar_relevantes(
    pregunta: str, faq_vectores: list[tuple[str, list[float]]], top_k: int = 3
) -> list[str]:
    emb_pregunta = vo.embed([pregunta], model="voyage-4", input_type="query").embeddings[0]
    scores = [(similitud_coseno(emb_pregunta, vector), texto) for texto, vector in faq_vectores]
    scores.sort(reverse=True)
    return [texto for _, texto in scores[:top_k]]


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
        for j, texto in enumerate(resultados, start=1):
            print(f"  {j}. {texto}")
