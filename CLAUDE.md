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
- Memoria de conversación: diccionario en memoria por número de teléfono (sin base de datos — alcanza para el volumen de estos 11 días de prueba)

## IMPORTANT

- Nunca leas, muestres ni commitees el archivo `.env` — tiene las API keys reales
- No agregues campos nuevos a la tool `crear_reserva` sin confirmar antes — el schema está definido en el Día 3 de la guía
- No adelantes lógica de días futuros de la guía sin que se pida explícitamente

## Actualización de progreso

- Al terminar el "Resultado esperado al cerrar el día" de cualquier día de la guía, tildá el checkbox correspondiente en README.md (sección "Estado del proyecto") antes de hacer el commit del día.
- El commit de cierre de día tiene que incluir ese cambio en README.md junto con el código — no como commit aparte.
- Nunca tildes un día que no esté realmente terminado, aunque el código compile — el checkbox refleja el resultado esperado cumplido, no solo "escribí algo".

## Git y GitHub

- `gh` ya está autenticado en esta máquina — usalo libremente para lo que haga falta
- Commit al cerrar cada día de la guía. Mensaje en español: "Día N: qué se construyó"
- Commit también cuando se pida explícitamente ("hacé commit")
- Preguntar siempre antes de `git push` — nunca automático
- Preguntar siempre antes de cualquier acción irreversible en GitHub (borrar repo, force push, reescribir historial)