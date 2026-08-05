from pydantic import BaseModel


class MensajeEntrante(BaseModel):
    numero: str
    texto: str
