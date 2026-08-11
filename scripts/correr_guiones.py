"""Corre los guiones de testing de docs/guiones_testing.md contra /webhook.

Verifica de forma estructural, no por el tono del texto: compara las respuestas
contra los mensajes de resguardo importados del código real y mira si el JSON
trae la clave "reserva" para saber qué tool eligió Claude.

Uso:
    python scripts/correr_guiones.py            # los 18 guiones + degenerados
    python scripts/correr_guiones.py G1 G3 G4   # solo algunos
    python scripts/correr_guiones.py --degenerados
"""

import sys
import time
from typing import Any

import requests

from app.claude_client import MSG_ERROR_BUSQUEDA, MSG_ERROR_RUTEO, MSG_SIN_MATCH

URL = "http://127.0.0.1:8000/webhook"

# Espera entre mensajes. La búsqueda del FAQ pega a Voyage, que tiene rate limit
# bajo en el plan gratuito: sin esta pausa aparece MSG_ERROR_BUSQUEDA en guiones
# donde no corresponde. Se espera entre todos los mensajes y no solo entre los
# de FAQ porque desde la respuesta no se puede distinguir el camino 2 (FAQ) del
# camino 3 (texto libre pidiendo un dato) — ambos devuelven solo "respuesta".
ESPERA_SEGUNDOS = 25

GUIONES: list[tuple[str, str, list[str]]] = [
    ("G1", "5492625001", ["hola queria reservar para el sabado a la noche, somos 4"]),
    ("G2", "5492625002", ["necesito una mesa para dos personas mañana a las 21"]),
    ("G3", "5492625003", ["reserva a nombre de Martín, para 3, el viernes a las 22hs"]),
    (
        "G4",
        "5492625004",
        ["quiero reservar una mesa", "para 6, el domingo", "a las 20:30"],
    ),
    ("G5", "5492625005", ["para el sabado a las 21hs"]),
    (
        "G6",
        "5492625006",
        ["mesa para 4 el sabado a las 21", "che en realidad somos 5, se suma uno mas"],
    ),
    ("G7", "5492625007", ["che tenes algo pa comer si soy celiaco?"]),
    ("G8", "5492625008", ["hasta que hora abris los sabados"]),
    ("G9", "5492625009", ["tenes wifi ahi?"]),
    ("G10", "5492625010", ["aceptan debito?"]),
    ("G11", "5492625011", ["puedo ir en auto, hay donde estacionar?"]),
    ("G12", "5492625012", ["llevo a mi perrita, hay problema?"]),
    ("G13", "5492625013", ["hacen envios a domicilio?"]),
    ("G14", "5492625014", ["tienen mesa para cumpleaños, somos re grupo grande?"]),
    ("G15", "5492625015", ["abren los feriados?"]),
    (
        "G16",
        "5492625099",
        ["tenes wifi?", "dale, aparte quiero reservar para 3 el viernes a las 21"],
    ),
    ("G17", "5492625017", ["🍕😋"]),
    (
        "G18",
        "5492625018",
        [
            "hola buenas tardes disculpen la hora quería consultar si tienen mesa "
            "libre para el sabado que viene somos con mi señora y mis dos hijos "
            "osea 4 en total sería como a las 21 o 21:30 mas o menos, gracias"
        ],
    ),
]

DEGENERADOS: list[tuple[str, str, list[str]]] = [
    ("D1", "5492625901", [""]),
    ("D2", "5492625902", ["   "]),
    ("D3", "5492625903", ["\n\t "]),
]


def clasificar(respuesta: str) -> str:
    """Compara exacto contra los mensajes de resguardo del código real."""
    if respuesta == MSG_SIN_MATCH:
        return "MSG_SIN_MATCH"
    if respuesta == MSG_ERROR_BUSQUEDA:
        return "MSG_ERROR_BUSQUEDA"
    if respuesta == MSG_ERROR_RUTEO:
        return "MSG_ERROR_RUTEO"
    return "texto"


def enviar(numero: str, texto: str) -> tuple[int, dict[str, Any]]:
    r = requests.post(URL, json={"numero": numero, "texto": texto}, timeout=90)
    return r.status_code, r.json()


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    solo_degenerados = "--degenerados" in sys.argv

    if solo_degenerados:
        a_correr = DEGENERADOS
    elif args:
        a_correr = [g for g in GUIONES if g[0] in args]
    else:
        a_correr = DEGENERADOS + GUIONES

    primero = True
    for guion, numero, mensajes in a_correr:
        for i, texto in enumerate(mensajes, start=1):
            if not primero:
                time.sleep(ESPERA_SEGUNDOS)
            primero = False

            etiqueta = guion if len(mensajes) == 1 else f"{guion}.{i}"
            estado, datos = enviar(numero, texto)
            respuesta = datos.get("respuesta", "")
            tipo = clasificar(respuesta)
            reserva = datos.get("reserva")

            print(f"[{etiqueta}] HTTP {estado} | tool={'crear_reserva' if reserva else '-'} | {tipo}")
            print(f"    >> {texto[:75]!r}")
            if reserva:
                print(f"    reserva: {reserva}")
            print(f"    << {respuesta!r}", flush=True)

            # Criterio de corte acordado: si el error de búsqueda aparece en un
            # guion donde no corresponde, el espaciado no alcanzó y el resto de
            # la corrida deja de ser confiable.
            if tipo == "MSG_ERROR_BUSQUEDA":
                print(f"\n*** CORTE: MSG_ERROR_BUSQUEDA en {etiqueta} ***", flush=True)
                return 1

    print("\nCorrida completa sin cortes.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
