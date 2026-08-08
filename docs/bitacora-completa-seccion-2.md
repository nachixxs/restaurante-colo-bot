# Bitácora — Sección 2: Claude como agente

## Día 4 — 7 de agosto

Confirmación real por WhatsApp + guardado de cada reserva en Google Sheets.

### Error 0 — Activar un workflow vía API de n8n no siempre registra el webhook en memoria

**Problema:** un workflow marcado como `active: true` en la base de datos de n8n (activado vía API, no desde la UI) no responde a su webhook — devuelve `404 "webhook not registered"` aunque la API confirme que está activo. Se detectó primero al retomar la sesión (el workflow real "Restaurante Colo - Dia 2" había quedado activo de la noche anterior, pero recién se confirmó que escuchaba de verdad tras reiniciar n8n al arrancar el entorno) y se volvió a reproducir dos veces más hoy, con el workflow temporal de la planilla: activarlo vía API (`POST /api/v1/workflows/{id}/activate`) dejó la fila `active=true` en la base, pero el webhook seguía devolviendo 404 hasta reiniciar el proceso completo de n8n.

**Causa:** n8n mantiene un registro de webhooks activos en memoria (el proceso Node corriendo), separado de la fila `active` en la base de datos. Activar un workflow por API actualiza la base, pero no siempre dispara el registro del webhook en memoria del proceso ya corriendo — a diferencia de activar desde la UI, que si dispara ese registro en el momento. La única forma confirmada de sincronizar ambos es reiniciar el proceso de n8n, que al arrancar recorre todos los workflows `active=true` y los registra de una.

**Solución:** cuando un workflow se activa (o reactiva) vía API y su webhook no responde, reiniciar el proceso de n8n (`Stop-Process` + `n8n start`) en vez de asumir que alguna otra llamada a la API (toggle off/on, etc.) lo va a resolver — no se probó una alternativa más liviana que funcione de forma confiable.

**Lección para el próximo cliente:** cualquier automatización que active workflows de n8n por API (por ejemplo, para desplegar cambios sin abrir la UI) tiene que contemplar un reinicio del proceso como parte del paso de activación, o verificar explícitamente que el webhook responde (no solo que `active` sea `true`) antes de dar el despliegue por terminado.

### Error 1 — El workflow temporal (creado vía API) escribió basura en la planilla en vez de los headers

**Problema:** al armar un workflow temporal por API de n8n para crear la planilla "Reservas Restaurante Colo" (nodo "Crear planilla" → nodo "Agregar headers" → Respond to Webhook), el resultado no fue la pestaña "Reservas" con los headers `fecha, hora, personas, nombre, numero` — quedaron escritas las columnas `spreadsheetId`, `sheets`, `properties`.

**Causa:** el parámetro `columns.mappingMode: "defineBelow"` que se le pasó al nodo "Agregar headers" (armado a mano, adivinando el schema JSON del nodo Google Sheets sin poder validarlo contra n8n antes de ejecutar) no fue reconocido como válido. El nodo cayó en modo de auto-mapeo, que toma las claves del JSON de entrada como si fueran columnas — y ese JSON de entrada era la respuesta cruda de la API de Google (`spreadsheetId`, `properties`, `sheets`, `spreadsheetUrl`) que devolvió el nodo "Crear planilla" inmediatamente antes.

**Solución:** no se reintentó por API (para no arriesgar escribir basura de nuevo sobre la planilla real). Se corrigió a mano en sheets.google.com: renombrar la pestaña a "Reservas" y tipear los 5 headers reales en A1:E1.

**Lección para el próximo cliente:** los nodos de n8n con mapeo de columnas tipo "resource mapper" (Google Sheets, y probablemente otros con UI similar) no exponen su schema exacto por la API pública — solo por la UI, que requiere sesión de browser, no API key. Armar estos nodos a mano vía API sobre datos reales es un riesgo real de escribir datos incorrectos sin que la API avise del error (la escritura "funciona", solo que con el contenido equivocado). Preferir la UI para cualquier nodo con mapeo de columnas, reservar la API para nodos simples (Webhook, IF, HTTP Request, Respond to Webhook) cuyo JSON sí es predecible.

### Error 2 — Al insertar un nodo nuevo en el medio de una cadena, una expresión `$json` que apuntaba al nodo viejo se rompió

**Problema:** después de insertar el nodo "Guardar en Sheets" entre "Llamar a FastAPI" y "Responder por WhatsApp", el envío del mensaje de confirmación por WhatsApp empezó a fallar con error 400 de Meta: `falta 'body'` en el campo `text`.

**Causa:** el campo `text.body` del nodo "Responder por WhatsApp" usaba la expresión `$json.respuesta` — que no referencia un nodo por nombre, sino "la salida del nodo inmediatamente anterior en la cadena". Hasta ayer ese nodo anterior era "Llamar a FastAPI" (que sí devuelve `respuesta`). Al insertar "Guardar en Sheets" en el medio, `$json` pasó a apuntar a la salida de ese nodo nuevo (que no tiene campo `respuesta`), dejando `text.body` vacío.

**Solución:** cambiar la expresión de `$json.respuesta` a `$('Llamar a FastAPI').item.json.respuesta` — referenciando el nodo por nombre explícitamente, en vez de depender de la posición en la cadena.

**Lección para el próximo cliente:** cualquier expresión que use `$json` (sin nombre de nodo) es implícitamente frágil a futuras inserciones de nodos en el medio de una cadena. Conviene usar `$('Nombre del Nodo').item.json.campo` desde el principio en los campos que se sabe que van a sobrevivir varias iteraciones del workflow (como la confirmación final que se manda al cliente), no solo cuando ya se rompió.

### Nota — Token de WhatsApp venció por tercera vez

El token de acceso de la API de WhatsApp volvió a vencer durante las pruebas de hoy — ya es la tercera vez en el proyecto (recurrencia documentada también para el Error 13 de la Sección 1). Confirma que es un patrón esperable del token temporal de la app de desarrollador de Meta, no un accidente puntual. Queda pendiente resolverlo antes de cualquier demo real: pasar a un token de sistema (system user token) de vida permanente en vez del token temporal de 24hs que da el panel de "Primeros pasos".

## Día 5 — 8 de agosto

System prompt para pedir datos faltantes explícitamente + memoria de conversación por número de teléfono.

### Nota — Pendiente conocido: fecha duplicada en el texto de confirmación ("el el sábado")

Al probar la conversación de memoria (mensaje 3: "el sábado a las 21hs"), Claude extrajo el campo `fecha` como `"el sábado"` (con el artículo incluido) en vez de `"sábado"`. Como el f-string de `procesar_respuesta_reserva` ya antepone su propio "el" (`f"el {datos['fecha']}"`), el texto de confirmación quedó "Confirmado: mesa para 4 **el el sábado** a las 21hs".

No es un bug de la memoria de conversación ni del system prompt — es un detalle de cómo Claude interpreta el campo libre `fecha` según cómo esté redactado el mensaje del cliente. Se decidió no tocarlo ahora: queda anotado como pendiente conocido para relevar en el testing con guiones reales de los Días 9-10, junto con el resto de los casos raros de extracción.

### Error 0 — El historial de conversación filtraba datos de una reserva ya confirmada hacia una reserva nueva y distinta

**Problema:** con la memoria de conversación recién implementada, un mismo número de teléfono que ya había confirmado una reserva (ej. mesa para 4 el sábado a las 21hs) y después, en un mensaje posterior, pedía una reserva distinta sin repetir la cantidad de personas (ej. "quiero otra mesa para el miércoles a las 21hs"), corría el riesgo de que Claude reutilizara el dato "personas: 4" de la reserva anterior ya cerrada, en vez de preguntarlo de nuevo — sin ningún error visible, el dato quedaba mal asumido en silencio.

**Causa:** `conversaciones[numero]` guardaba el historial completo desde el primer mensaje, sin cortarlo nunca. Cada llamada a Claude mandaba ese historial entero como `messages`, así que una reserva ya confirmada y cerrada seguía formando parte del contexto de cualquier mensaje futuro de ese mismo número, sin distinguir "estoy completando esta misma reserva" de "estoy arrancando una reserva nueva".

**Solución:** en `app/main.py`, justo cuando `procesar_respuesta_reserva()` devuelve un resultado exitoso (la tool se usó y la reserva quedó confirmada), se resetea el historial de ese número con `conversaciones.pop(mensaje.numero, None)`. Así, la próxima vez que ese número escriba, arranca una conversación en blanco, sin arrastrar datos de la reserva anterior.

**Verificación:** se repitió la conversación de 3 mensajes que completa una reserva de a poco (confirma que la memoria dentro de UNA reserva sigue funcionando), y se agregó un cuarto mensaje simulando una reserva nueva y distinta sin mencionar la cantidad de personas — Claude preguntó la cantidad de personas en vez de asumir la de la reserva anterior.

**Lección para el próximo cliente / para días futuros de este proyecto:** este reset total del historial tras cada reserva confirmada asume que, por ahora, la única interacción posible después de confirmar es "empezar una reserva nueva" — no existe todavía ninguna tool para modificar o cancelar una reserva ya hecha. Si en el futuro se agrega una tool de ese tipo, resetear todo el historial va a borrar también el contexto de la reserva que el cliente querría modificar. En ese momento va a hacer falta una estrategia de memoria distinta — por ejemplo, no vaciar el historial por completo sino guardar el ID (o los datos clave) de la última reserva confirmada, para poder referenciarla en un pedido de modificación sin arrastrar el resto de la conversación vieja.

## Resumen de causas raíz — para no repetir estos errores con el próximo cliente

| # | Síntoma | Causa real | Categoría |
|---|---|---|---|
| 0 | Webhook 404 pese a `active: true` | Activar por API no registra el webhook en memoria del proceso corriendo; hace falta reiniciar n8n | n8n, activación vía API |
| 1 | Planilla con columnas `spreadsheetId`/`sheets`/`properties` en vez de headers | Nodo Google Sheets armado a mano por API cayó en auto-mapeo (schema no válido) | n8n, nodos con resource mapper |
| 2 | WhatsApp 400 "falta 'body'" tras insertar un nodo nuevo | Expresión `$json.campo` (implícita al nodo anterior) rota al cambiar el orden de la cadena | n8n, expresiones |
| 3 | Token de WhatsApp vencido (recurrente) | Token temporal de 24hs de la app de desarrollador de Meta, no un token de sistema permanente | Meta, configuración |
| 4 | Reserva nueva heredaba datos (personas) de una reserva ya confirmada del mismo número | Historial de conversación sin corte, se mandaba completo en cada llamada a Claude | Claude API, memoria de conversación |
