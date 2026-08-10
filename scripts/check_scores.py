"""
Script de diagnóstico temporal (Día 9) para ver la distribución real de scores
de similitud coseno del RAG, antes de definir un umbral a ciegas.

Se ejecuta una vez y se descarta - no forma parte del flujo de la app.
"""
import sys
import time

from app.rag.embeddings import vo
from app.rag.search import cargar_faq_vectores, similitud_coseno

# Reformulaciones de las 6 preguntas del FAQ (una por tema), en el mismo
# orden que faq_embeddings.json: TACC, sábados, wifi, tarjetas,
# estacionamiento, mascotas.
preguntas_reformuladas = [
    "tienen platos aptos para celíacos?",
    "los sábados hasta qué hora está abierto?",
    "hay internet para los clientes?",
    "puedo pagar con tarjeta de crédito?",
    "dónde puedo dejar el auto?",
    "puedo llevar a mi perro?",
]

# Preguntas fuera de tema: una relacionada al negocio pero no cubierta por el
# FAQ, y otra totalmente ajena a un restaurante.
preguntas_fuera_de_tema = [
    "hacen delivery a otra ciudad?",
    "cuál es la capital de Francia?",
]

preguntas_de_prueba = preguntas_reformuladas + preguntas_fuera_de_tema


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    faq_vectores = cargar_faq_vectores()

    # Misma limitación que search.py: la cuenta gratis de Voyage permite
    # 3 requests por minuto, así que hace falta esta pausa entre preguntas.
    for i, pregunta in enumerate(preguntas_de_prueba):
        if i > 0:
            time.sleep(20)

        emb_pregunta = vo.embed([pregunta], model="voyage-4", input_type="query").embeddings[0]
        scores = [
            (similitud_coseno(emb_pregunta, vector), texto) for texto, vector in faq_vectores
        ]
        scores.sort(reverse=True)

        print(f"\nPregunta: {pregunta}")
        for score, texto in scores:
            print(f"  {score:.4f}  {texto}")


if __name__ == "__main__":
    main()
