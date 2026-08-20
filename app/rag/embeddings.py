import json
from pathlib import Path

import voyageai
from dotenv import load_dotenv

load_dotenv()

vo = voyageai.Client()  # lee VOYAGE_API_KEY del entorno

RUTA_EMBEDDINGS = Path(__file__).resolve().parent.parent.parent / "data" / "faq_embeddings.json"

# Plan B: FAQ de ejemplo, mientras el FAQ real del restaurante todavía no
# está listo. Reemplazar esta lista por el FAQ real apenas lo manden - el resto
# del código de este archivo no cambia.
faq: list[str] = [
    "Tienen opciones sin TACC? Sí, 3 platos aptos para celíacos.",
    "Hasta qué hora atienden los sábados? Hasta las 00:30.",
    "Tienen wifi para clientes? Sí, la clave está en las mesas.",
    "Aceptan tarjeta de débito y crédito? Sí, todas las tarjetas.",
    "Tienen estacionamiento propio? No, pero hay uno público a media cuadra.",
    "Aceptan mascotas? Sí, en las mesas de la vereda.",
]


def generar_embeddings(textos: list[str]) -> list[list[float]]:
    resultado = vo.embed(textos, model="voyage-4", input_type="document")
    return resultado.embeddings


def guardar_embeddings(textos: list[str], vectores: list[list[float]]) -> None:
    faq_vectores = list(zip(textos, vectores))
    with open(RUTA_EMBEDDINGS, "w", encoding="utf-8") as f:
        json.dump(faq_vectores, f)


if __name__ == "__main__":
    vectores = generar_embeddings(faq)
    guardar_embeddings(faq, vectores)
    print(f"Generados {len(vectores)} embeddings, guardados en {RUTA_EMBEDDINGS}")
