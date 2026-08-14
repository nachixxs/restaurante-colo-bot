# Restaurante Colo — Bot de WhatsApp con IA

Ver @README.md para contexto completo del proyecto, arquitectura y stack.

## Comandos

- Activar entorno (Windows): `venv\Scripts\activate`
- Instalar dependencias: `pip install -r requirements.txt`
- Correr servidor local: `uvicorn app.main:app --reload`
- Exponer a internet: `ngrok http 8000`

## Estilo de código

- Python 3.11+, con type hints en toda función nueva
- Datos estructurados con Pydantic (`BaseModel`), nunca dicts sueltos sin validar
- f-strings para formatear texto, no `.format()` ni `%`
- Comentarios y nombres de variables en español

## Arquitectura del proyecto (no reinventar sin avisar)

- Un único endpoint `POST /webhook` recibe todo desde n8n — no crear endpoints paralelos
- La decisión reserva-vs-pregunta la toma Claude vía tool use, nunca un `if` manual buscando palabras clave
- Memoria de conversación: diccionario en memoria por número de teléfono (sin base de datos — alcanza para el volumen de estos días de construcción: 11 días de guía, completados en 7 días de calendario reales, del 4 al 10 de agosto de 2026)

## IMPORTANT

- Nunca leas, muestres ni commitees el archivo `.env` — tiene las API keys reales
- No agregues campos nuevos a la tool `crear_reserva` sin confirmar antes — el schema está definido en el Día 3 de la guía
- No adelantes lógica de días futuros de la guía sin que se pida explícitamente

## Actualización de progreso

- El estado del proyecto se trackea en el vault (`02-Projects/El-Parador-Bot/Overview.md`), no en este README — este repo es portfolio público, no el lugar de seguimiento de trabajo.
- Nunca marces como terminado un día que no lo esté realmente, aunque el código compile — el estado refleja el resultado esperado cumplido, no solo "escribí algo".

## Git y GitHub

- `gh` ya está autenticado en esta máquina — usalo libremente para lo que haga falta
- Commit después de cada cambio, por chico que sea (un paso, un fix, un ajuste) — no solo al cerrar el día ni solo cuando se pida. Mensaje descriptivo en español.
- Preguntar siempre antes de `git push` — nunca automático
- Cada vez que hagas uno o más commits en una misma sesión de trabajo, al final listalos (hash corto + mensaje) y preguntá explícitamente si hacer push o no — no asumas ninguna de las dos opciones.
- Preguntar siempre antes de cualquier acción irreversible en GitHub (borrar repo, force push, reescribir historial)
- Para trabajar cualquier día de la guía, usá la skill seguir-guia en vez de esperar que te pase el código.

## n8n/workflow-dia2.json

- Es una foto fija sanitizada (sin claves reales) del workflow al cerrar el Día 2/Sección 1, no un espejo en vivo del workflow real.
- Se actualiza solo al cerrar cada día o sección, no en cada edición suelta hecha por API durante el día.
- El workflow real, con las claves reales, vive únicamente en la base de datos local de n8n en esta máquina — no se exporta sin sanitizar a ningún lado.