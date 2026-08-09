<div align="center">

# 🍽️ Restaurante Colo — Bot de Reservas con IA

**Automatización de WhatsApp con IA para la toma de reservas y consultas de FAQ de un restaurante real.**

![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude-D97757?logo=claude&logoColor=white)
![Status](https://img.shields.io/badge/status-en%20construcción-yellow)

Primer caso de uso real de **[Accelerate.ai](#)**, la agencia de automatizaciones de Nacho & Colo.

</div>

---

## 📋 Qué hace

Un cliente le escribe al restaurante por WhatsApp — pidiendo una mesa o preguntando algo del menú — y el sistema:

1. Recibe el mensaje a través de un webhook (FastAPI).
2. Usa la **API de Claude** para decidir si es una reserva o una pregunta.
3. Si es reserva: extrae fecha, hora, personas y nombre con **tool use**, y confirma por WhatsApp.
4. Si es pregunta: busca la respuesta en el FAQ del restaurante mediante **embeddings (Voyage AI) + RAG**.
5. Guarda cada reserva confirmada en **Google Sheets**.

## 🏗️ Arquitectura

```
Cliente (WhatsApp) → n8n → FastAPI ──┬─→ Claude API (decide y extrae datos)
                                      ├─→ Voyage AI (búsqueda RAG en el FAQ)
                                      └─→ Google Sheets (persistencia)
```

## 🛠️ Stack técnico

| Capa | Tecnología |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| IA / Agente | Claude API (tool use / function calling) |
| Búsqueda semántica | Voyage AI (embeddings) + similitud coseno |
| Orquestación | n8n |
| Canal | WhatsApp Cloud API (Meta) |
| Persistencia | Google Sheets |
| Túnel de desarrollo | ngrok |

## 🚀 Cómo correrlo localmente

```bash
git clone https://github.com/nachixxs/restaurante-colo-bot.git
cd restaurante-colo-bot
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env     # completar con tus propias API keys
uvicorn app.main:app --reload
```

## 📅 Estado del proyecto

Construido en 11 días de estudio guiado, del 4 al 14 de agosto de 2026.

### Sección 1 — El caño completo
- [x] Día 1 (4 ago) — Endpoint `/webhook` con FastAPI + Pydantic
- [x] Día 2 (5 ago) — ngrok + Meta + n8n, circuito completo con WhatsApp real

### Sección 2 — Claude como agente
- [x] Día 3 (6 ago) — Tool use, `crear_reserva`
- [x] Día 4 (7 ago) — Confirmación real + guardado en Sheets
- [x] Día 5 (8 ago) — Datos faltantes + memoria de conversación

### Sección 3 — RAG casero
- [x] Día 6 (9 ago) — Embeddings del FAQ (Plan B: FAQ de ejemplo)
- [x] Día 7 (10 ago) — Chunking + búsqueda por similitud
- [x] Día 8 (11 ago) — Unificar reserva + FAQ

### Sección 4 — Pulido y testing
- [ ] Día 9 (12 ago) — Manejo de errores
- [ ] Día 10 (13 ago) — Testing con guiones reales
- [ ] Día 11 (14 ago) — Corrección final

## 👥 Autores

Proyecto de **[Accelerate.ai](#)** — **Nacho** (desarrollo y automatización) y **Colo** (dominio del negocio, administración).

## 📄 Licencia

Proyecto privado desarrollado para un cliente real. Uso educativo del código como referencia — no reutilizar datos del restaurante.