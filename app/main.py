from fastapi import FastAPI

from app.models import MensajeEntrante

app = FastAPI()


@app.post("/webhook")
async def recibir_mensaje(mensaje: MensajeEntrante):
    # por ahora, devolvemos un eco
    return {"respuesta": f"Recibido: {mensaje.texto}"}
