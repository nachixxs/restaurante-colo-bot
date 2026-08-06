# Bitácora completa — Sección 1 (Día 1 y Día 2)

> Registro cronológico de todo lo trabajado, en el orden real en que fue pasando — pensado para que Colo (o cualquiera) pueda seguir el hilo completo de principio a fin, incluyendo cada tropiezo y cómo se resolvió.

---

## Parte 0 — Preparación del proyecto (antes del Día 1)

**Qué se hizo:**
- Se armó una carpeta madre `accelerate-ai/` con subcarpetas `clientes/`, `plantillas/`, `docs/`, pensada para organizar futuros clientes de la agencia sin mezclar proyectos.
- Se creó la estructura completa del proyecto `restaurante-colo-bot/` (carpetas `app/`, `data/`, `docs/`, archivos base) usando Claude Code.
- Se investigaron y aplicaron buenas prácticas actualizadas para `CLAUDE.md` (instrucciones para Claude Code) y `README.md` (documentación pública del repo).
- Se creó una Skill personalizada (`seguir-guia`) para que Claude Code lea la guía de estudio y construya cada día con criterio propio, en vez de copiar código literal — separando "qué hay que lograr" de "cómo está implementado".

**Error encontrado — Repositorio de GitHub mal armado:**
- Al crear el repo con `gh repo create`, quedó **público** (sin querer) y con una **carpeta anidada de más** (`clientes/restaurante-colo/restaurante-colo-bot/` dentro del propio repo, en vez de los archivos en la raíz) — porque el comando se corrió parado en la carpeta madre, no dentro del proyecto.
- **Solución:** se borró el repo remoto y el `.git` local mal ubicado, y se rehizo todo manualmente (`git init` parado en la carpeta correcta, conexión a un repo nuevo), confirmando con capturas que la estructura quedara limpia.

---

## Día 1 — El caño completo (parte 1)

**Qué se construyó:**
- `app/models.py`: modelo Pydantic `MensajeEntrante` (`numero: str`, `texto: str`).
- `app/main.py`: endpoint `POST /webhook`, `async def`, hace eco del mensaje recibido.
- Decisión de diseño tomada por Claude Code (no impuesta): separar el modelo en `models.py` en vez de dejarlo todo en `main.py` como sugería la guía — aprovechando la estructura de carpetas ya armada.

**Verificación:** `uvicorn app.main:app --reload` + curl a `/webhook` con `{"numero": "123", "texto": "hola"}` → devolvió `{"respuesta": "Recibido: hola"}`, coincidiendo con el resultado esperado.

**Sin errores en este día.** Commit y push limpios.

---

## Día 2 — El caño completo (parte 2): la travesía completa

### Preparación inicial
- Se generó `N8N_API_KEY` en el panel de n8n para que Claude Code pudiera crear/actualizar workflows vía API sin exponer la key directamente en el chat.
- Se decidió, por seguridad, que los comandos que usan claves sensibles los corra siempre Nacho en su propia terminal — Claude Code da el comando, nunca ve el valor real.

### Error 1 — `gh` no reconocido después de instalar
**Problema:** después de `winget install GitHub.cli`, la terminal seguía sin reconocer `gh`.
**Causa:** el PATH se actualiza recién en una sesión nueva de terminal.
**Solución:** cerrar y abrir una ventana nueva de PowerShell (o refrescar el PATH manualmente en la misma sesión).

### Error 2 — El nodo nativo "WhatsApp Trigger" de n8n pedía OAuth2
**Problema:** al intentar configurar las credenciales del nodo WhatsApp Trigger, n8n pedía Client ID / Client Secret (flujo OAuth2 completo), no el token simple que se esperaba.
**Investigación:** se confirmó que es un cambio real de las versiones recientes de n8n — el nodo nativo ahora requiere registrar la app como cliente OAuth2 en Meta (agregar producto "Facebook Login for Business", configurar redirect URIs).
**Decisión:** en vez de sumar esa complejidad, se reemplazó el nodo nativo por un manejo manual del webhook: nodos `Webhook` (GET y POST separados) + `IF` (verificar token) + `Respond to Webhook`. Esto además resultó más portable para futuros clientes de la agencia.

### Error 3 — Script de PowerShell fallando con "Cannot find path .env"
**Problema:** al correr el script de importación del workflow, tiraba error de que no encontraba `.env`.
**Causa:** la terminal estaba parada en `C:\Users\ignac` (carpeta de usuario), no en la raíz del proyecto.
**Solución:** `cd` a la carpeta correcta antes de correr el script.

### Error 4 — El mismo script, pero con `.env` vacío
**Problema:** aun parado en la carpeta correcta, `$apiKey` seguía quedando vacío.
**Causa:** el archivo `.env` se había creado pero nunca se guardó de verdad (faltó Ctrl+S).
**Solución:** reabrir con Notepad, pegar las claves, guardar explícitamente, confirmar con `Get-Content .env`.

### Error 5 — Repo de GitHub duplicado y mal armado (segunda vez, con el workflow)
Mismo patrón que en la Parte 0: `gh repo create` corrido desde el lugar equivocado generó un repo con estructura anidada y público. Se optó por seguir el resto del proyecto con comandos manuales de `git`/`gh` en vez de scripts automáticos para reducir el margen de error.

### Error 6 — Nodo de n8n pidiendo credenciales "WhatsApp OAuth account"
**Problema:** al configurar el nodo, apareció una pantalla pidiendo Client ID / Client Secret de OAuth, no lo esperado.
**Causa:** confirmado por investigación — es el comportamiento real y actual de ese tipo de credencial en n8n.
**Solución:** confirmó la decisión ya tomada de usar el camino manual (Webhook + IF + Respond), evitando el flujo OAuth2 por completo.

### Error 7 — FastAPI "caído" según n8n, pero corriendo según curl
**Problema:** n8n reportaba `"The service refused the connection - perhaps it is offline"` al llamar a FastAPI, pero un curl manual confirmaba que FastAPI respondía perfecto.
**Causa (diagnosticada por Claude Code):** `localhost` se resolvía a IPv6 en el proceso de n8n/Node, mientras uvicorn solo escuchaba en IPv4 — un problema de resolución de nombre en Windows, no un servidor caído.
**Solución:** cambiar la URL del nodo "Llamar a FastAPI" de `localhost:8000` a `127.0.0.1:8000`.

### Error 8 — "Authorization failed" en el nodo de respuesta por WhatsApp
**Problema:** al intentar responder, n8n devolvía error de autorización.
**Causa:** el header `Authorization` seguía con el placeholder `<WHATSAPP_TOKEN>` literal, sin reemplazar por el token real.
**Solución:** pegar el token real directo en el campo del nodo (nunca vía Claude Code, siempre a mano en la UI).

### Error 9 — El cambio de token "no se aplicaba" pese a estar bien pegado
**Problema:** después de corregir el token, el error de autorización seguía apareciendo exactamente igual.
**Causa (el gran hallazgo de n8n 2.0):** n8n separa **guardar un cambio** (automático) de **publicarlo** (botón explícito "Publish"). El workflow real que atendía los webhooks seguía siendo la versión anterior, no la editada.
**Solución:** apretar "Publish" después de cada cambio en un nodo. Este patrón se repitió varias veces más durante la noche (Phone ID, URL, etc.) — cada edición necesitaba su propio Publish.

### Error 10 — "Bad request" al probar con el botón de test de Meta
**Problema:** al usar el botón "Enviar a mi servidor" de Meta, el envío de respuesta fallaba con "número no autorizado".
**Causa:** el payload de ejemplo de Meta usa un número de teléfono falso (`16315551181`), que lógicamente no está en la lista de destinatarios permitidos.
**Conclusión:** no era un error real — confirmaba que el resto de la cadena funcionaba perfecto.

### Error 11 (el grande de la primera noche) — Mensajes reales nunca llegaban
**Problema:** el botón de test de Meta funcionaba de punta a punta, pero un mensaje real mandado desde el teléfono no generaba ninguna ejecución en n8n — ni un solo request nuevo aparecía ni siquiera en el panel de ngrok.
**Descartado en el camino:** número no autorizado (sí estaba en la lista), verificación del webhook (seguía activa), suscripción al campo `messages` (estaba activada).
**Hallazgo real:** un aviso de Meta, hasta entonces ignorado, decía que la app **no publicada** no entrega datos de producción a ningún webhook, ni siquiera a administradores.
**Solución aplicada esa noche:** se publicó la app de Meta (requería completar URL de política de privacidad — se creó `PRIVACY.md` en el repo para eso — y categoría).
**Resultado:** publicar la app **no resolvió el problema**. Se decidió, después de investigar en profundidad, cortar la sesión pasadas las 2 AM y retomar con la cabeza descansada.

### Trabajo intermedio — Documentación para retomar
Antes de cortar la primera noche, se armaron dos artefactos para no perder el hilo:
- Un archivo `.md` explicando en profundidad cómo funciona cada pieza (FastAPI, ngrok, n8n, Meta) y sus conexiones.
- Un diagrama visual (SVG/PNG) de toda la arquitectura, revisado y corregido por superposiciones visuales.

### Error 12 (el real, encontrado al retomar) — Falta el link WABA ↔ App
**Investigación:** se encontró documentación específica (un caso casi idéntico, de diciembre 2025/febrero 2026) que explicaba una arquitectura de **3 capas** en WhatsApp Cloud API: Número de teléfono → WABA (WhatsApp Business Account) → App. El link entre el WABA y la App **no se crea desde ningún botón visible del panel** — se crea con una llamada a la API (`subscribed_apps`).
**Diagnóstico confirmado con comando real:**
```
GET https://graph.facebook.com/v21.0/{WABA_ID}/subscribed_apps
```
Devolvió que el WABA tenía suscripta una app genérica de Meta ("WA DevX Webhook Events 1P App"), **no la app del proyecto**.
**Solución:**
```
POST https://graph.facebook.com/v21.0/{WABA_ID}/subscribed_apps
```
Confirmado con `success: true`, y verificado de nuevo con el GET mostrando ahora las dos apps suscriptas.
**Resultado:** el mensaje real **llegó** por primera vez — "Webhook POST" y "Llamar a FastAPI" quedaron en verde. Bug de anoche resuelto.

### Error 13 — Token vencido (el mismo patrón de antes, distinto día)
**Problema:** con el mensaje ya llegando, el nodo de respuesta volvió a fallar con 401.
**Causa:** el token temporal de la noche anterior ya había vencido (duran poco, no 24hs completas).
**Solución:** generar un token nuevo desde el panel de Meta, pegarlo en el nodo, publicar de nuevo.

### Error 14 — Número argentino rechazado: "Recipient phone number not in allowed list"
Este fue el obstáculo más largo del día, con varios intentos fallidos antes de dar con la causa real:

1. **Primer intento:** se asumió que el "9" que Argentina agrega a los celulares causaba un desajuste de formato. Se aplicó una regex en n8n para sacar el "9" del número antes de responder. **Falló** — seguía diciendo "no autorizado".
2. **Investigación del motivo del fallo:** se encontró que el número, en el panel de Meta, estaba guardado con el **viejo formato local argentino** (`+54 2625 15-63-4845`, con el "15" de discado local) — ni con "9" ni sin "9" iba a coincidir nunca contra eso.
3. **Segundo intento:** se borró ese número de la lista y se volvió a agregar, esta vez explícitamente **con el "9"** (`+54 9 2625 63-4845`), verificado por código OTP recibido por WhatsApp. Se revirtió la regex (para mandar el número tal cual, con "9"). **Falló de nuevo** — mismo error.
4. **Investigación profunda (búsqueda + lectura de un caso documentado en detalle, proyecto Chatwoot):** se confirmó que Meta, en modo desarrollo, además de la comparación exacta, tiene un comportamiento específico y documentado para países con el "9" adicional (Argentina, Brasil, México): **hay que registrar el número SIN el "9" Y mandar el mensaje de salida también SIN el "9"** — las dos cosas a la vez, no una sola.
5. **Solución final:** se volvió a borrar y re-agregar el número, esta vez **sin** el "9" (`+54 2625 63-4845`), verificado por OTP. Se **reaplicó** la regex que saca el "9" del número de salida. **Funcionó.**

**Resultado:** el mensaje "hola" mandado desde el WhatsApp real llegó a n8n, pasó por FastAPI, y la respuesta "Recibido: hola" llegó de vuelta al teléfono. Resultado esperado del Día 2, cumplido.

### Error 15 (menor, de robustez) — Eventos de estado de WhatsApp rompiendo el workflow
**Problema:** después del éxito, aparecieron dos ejecuciones más con error "JSON parameter needs to be valid JSON", casi al mismo segundo que la exitosa.
**Causa:** WhatsApp manda, además del mensaje, eventos de **estado** (entregado, leído) al mismo webhook — con una estructura distinta (`statuses` en vez de `messages`), que rompía el nodo al intentar procesarlos como si fueran un mensaje.
**Solución:** se agregó un nodo `IF` ("Filtrar eventos de estado") que revisa si el payload tiene `messages`; si no lo tiene, responde 200 OK y no sigue la cadena («Ignorar evento de estado»).

### Ajuste cosmético final
El nodo "Rechazar verificación" había quedado dibujado superpuesto visualmente con "Llamar a FastAPI" en el canvas de n8n (sin afectar la lógica) — se reposicionó a mano para que se vea prolijo.

---

## Cierre del Día 2

- Revisión completa de punta a punta (código, workflow, archivos, git) antes de commitear.
- Commit: *"Día 2: webhook manual con verificación Meta, suscripción WABA-App y manejo de números argentinos"*.
- Checkbox del Día 2 tildado en el README.
- Push a GitHub.

---

## Resumen de causas raíz — para no repetir estos errores con el próximo cliente

| # | Síntoma | Causa real | Categoría |
|---|---|---|---|
| 7 | n8n no encuentra FastAPI | `localhost` resuelve a IPv6 en Windows | Red / entorno |
| 9 | Cambios en n8n "no se aplican" | Falta publicar (Publish ≠ guardar) | n8n 2.0 |
| 11 | Mensajes reales no llegan (1ra causa) | App de Meta sin publicar | Meta, configuración |
| 12 | Mensajes reales no llegan (causa real) | Falta `subscribed_apps` entre WABA y App | Meta, API oculta |
| 14 | Respuesta rechazada a número argentino | Formato "9" debe coincidir en registro Y en envío | Meta, quirk regional |
| 15 | Errores JSON intermitentes | Eventos de estado sin filtrar | Diseño del workflow |
| 13b | Token vencido otra vez, tras unas horas + reinicio de máquina (ocurrió en los hechos el Día 4, no el Día 2 — anotado acá por ser el mismo patrón que el Error 13) | Mismo síntoma exacto que el Error 13: 401, `OAuthException` code 190 | Meta, **patrón recurrente esperable con tokens temporales** |

Estos puntos son los que más tiempo consumieron — y son exactamente los que, documentados así, evitan que el próximo cliente (o el próximo proyecto de Accelerate.ai) pase por lo mismo.

**Nota sobre el Error 13 / 13b:** no fue un accidente puntual — los tokens temporales de Meta vencen cada pocas horas, con o sin reinicio de por medio, así que este 401 va a **volver a aparecer** mientras sigamos usando un token temporal. Relevante para cuando se migre a un **token de sistema (system user token) permanente**: ese cambio debería eliminar esta clase de error de raíz, no solo parchearlo cada vez que vence.
