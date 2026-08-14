# Guiones de testing — 18 casos reales

Batería de testing del **Día 10**, escrita para probar el bot end-to-end contra
`POST /webhook` con mensajes tal como los escribiría un cliente real por WhatsApp:
minúsculas, sin tildes, con typos, con emojis y con datos incompletos.

> **Nota:** este archivo se escribió de forma retroactiva al abrir el Día 11. Los
> guiones son los que se corrieron efectivamente en la sesión del Día 10, pero en
> aquel momento quedaron solo en la conversación y nunca se commitearon.

## Cómo se corren

Cada guion usa **su propio número de teléfono**, porque la memoria de conversación
(`app/conversaciones.py`) es un diccionario en RAM indexado por número: reusar un
número arrastraría el historial de otro guion y contaminaría el resultado.

Los guiones **multi-mensaje** (G4, G6, G16) mandan sus mensajes en orden, con el
mismo número, para ejercitar justamente esa memoria.

Reglas de la corrida:

- Espaciar **20-25 segundos** entre cualquier par de mensajes que peguen a Voyage
  (los que van al camino de FAQ), incluidos los que están dentro de un guion
  multi-mensaje. Sin ese espaciado, el rate limit de Voyage hace aparecer
  `MSG_ERROR_BUSQUEDA` en guiones donde no corresponde.
- Verificar **estructuralmente**, nunca por el tono del texto: comparación exacta
  contra `MSG_SIN_MATCH` / `MSG_ERROR_BUSQUEDA` / `MSG_ERROR_RUTEO` importados de
  `app.claude_client`, y presencia o ausencia de la clave `"reserva"` en el JSON
  para saber qué tool usó Claude.
- Levantar el servidor limpio antes de empezar, para que ningún número arrastre
  historial de una corrida anterior.

## Los 18 guiones

### Camino de reserva (G1-G6)

| # | Número | Mensaje(s) | Qué pone a prueba |
|---|---|---|---|
| G1 | 5492625001 | `hola queria reservar para el sabado a la noche, somos 4` | Falta la hora exacta ("a la noche" no es una hora) |
| G2 | 5492625002 | `necesito una mesa para dos personas mañana a las 21` | Fecha relativa + personas escritas en letras |
| G3 | 5492625003 | `reserva a nombre de Martín, para 3, el viernes a las 22hs` | Reserva completa de una, con nombre |
| G4 | 5492625004 | 1) `quiero reservar una mesa`<br>2) `para 6, el domingo`<br>3) `a las 20:30` | Datos que llegan de a poco en 3 mensajes (memoria) |
| G5 | 5492625005 | `para el sabado a las 21hs` | Falta la cantidad de personas |
| G6 | 5492625006 | 1) `mesa para 4 el sabado a las 21`<br>2) `che en realidad somos 5, se suma uno mas` | Modificar una reserva ya confirmada |

### Camino de FAQ (G7-G15)

| # | Número | Mensaje | Qué pone a prueba |
|---|---|---|---|
| G7 | 5492625007 | `che tenes algo pa comer si soy celiaco?` | Sin TACC, en jerga informal |
| G8 | 5492625008 | `hasta que hora abris los sabados` | Horarios, sin signo de pregunta |
| G9 | 5492625009 | `tenes wifi ahi?` | Dato puntual del FAQ |
| G10 | 5492625010 | `aceptan debito?` | Medios de pago |
| G11 | 5492625011 | `puedo ir en auto, hay donde estacionar?` | Estacionamiento, pregunta indirecta |
| G12 | 5492625012 | `llevo a mi perrita, hay problema?` | Mascotas, sin nombrar la palabra clave |
| G13 | 5492625013 | `hacen envios a domicilio?` | **Fuera del FAQ**: tiene que dar `MSG_SIN_MATCH` |
| G14 | 5492625014 | `tienen mesa para cumpleaños, somos re grupo grande?` | Ambiguo entre reserva y consulta |
| G15 | 5492625015 | `abren los feriados?` | **Fuera del FAQ**: tiene que dar `MSG_SIN_MATCH` |

### Casos límite (G16-G18)

| # | Número | Mensaje(s) | Qué pone a prueba |
|---|---|---|---|
| G16 | 5492625099 | 1) `tenes wifi?`<br>2) `dale, aparte quiero reservar para 3 el viernes a las 21` | Cambiar de FAQ a reserva en la misma conversación |
| G17 | 5492625017 | `🍕😋` | Mensaje sin texto útil, solo emojis |
| G18 | 5492625018 | `hola buenas tardes disculpen la hora quería consultar si tienen mesa libre para el sabado que viene somos con mi señora y mis dos hijos osea 4 en total sería como a las 21 o 21:30 mas o menos, gracias` | Mensaje largo, cantidad implícita ("mi señora y mis dos hijos"), hora ambigua |

> G16 usa el número **5492625099** y no el 5492625016: en la corrida del Día 10 ese
> número quedó con historial contaminado en memoria, y se cambió para que el guion
> arranque limpio.

## Casos degenerados

No forman parte de los 18 guiones. Se probaron por primera vez al cerrar el Día 9 y
se reconfirman cada vez que se toca el system prompt. Los tres tienen que devolver
HTTP 200 con una respuesta coherente y cero tracebacks.

| Caso | `texto` |
|---|---|
| D1 | `""` (string vacío) |
| D2 | `" "` (solo espacios) |
| D3 | `"\n\t "` (solo tabs y saltos de línea) |

## Resultado de la corrida de cierre (Día 11)

Corrida única de punta a punta, servidor recién levantado (memoria de conversación
vacía), 25s entre mensajes. Verificación estructural: clave `"reserva"` en el JSON
para la tool, comparación exacta contra los mensajes de resguardo para el resto.

| # | HTTP | Tool | Resultado |
|---|---|---|---|
| D1 `""` | 200 | — | `MSG_ERROR_RUTEO` exacto |
| D2 `" "` | 200 | — | `MSG_ERROR_RUTEO` exacto |
| D3 `"\n\t "` | 200 | — | `MSG_ERROR_RUTEO` exacto |
| G1 | 200 | — | Pide la hora exacta; resuelve "el sábado" a 15/08/2026 |
| G2 | 200 | `crear_reserva` | `fecha: 11/08/2026` — **el bug del Día 10 quedó corregido** |
| G3 | 200 | `crear_reserva` | `{14/08/2026, 22:00, 3, Martín}`, fecha resuelta |
| G4 | 200 | `crear_reserva` (msg 3) | `{16/08/2026, 20:30, 6}` sin perder datos de los mensajes previos |
| G5 | 200 | — | Pide la cantidad de personas; sin el bug viejo de "el el sábado" |
| G6 | 200 | `crear_reserva` (msg 1) | Msg 2 pierde el contexto: **gap conocido**, ver hallazgos |
| G7 | 200 | — | Responde sin TACC desde el FAQ |
| G8 | 200 | — | Responde horario del sábado desde el FAQ |
| G9 | 200 | — | Responde wifi desde el FAQ |
| G10 | 200 | — | Responde medios de pago desde el FAQ |
| G11 | 200 | — | Responde estacionamiento desde el FAQ |
| G12 | 200 | — | Responde mascotas desde el FAQ |
| G13 | 200 | — | `MSG_SIN_MATCH` exacto (fuera del FAQ) |
| G14 | 200 | — | `MSG_SIN_MATCH` exacto — esta vez ruteó a FAQ, ver hallazgos |
| G15 | 200 | — | `MSG_SIN_MATCH` exacto (fuera del FAQ) |
| G16 | 200 | `crear_reserva` (msg 2) | FAQ y después reserva en la misma conversación, sin mezclarse |
| G17 | 200 | — | Repregunta qué necesita el cliente, sin romperse con los emojis |
| G18 | 200 | — | Mantiene personas=4; pide la hora y **qué sábado** (ver hallazgos) |

Ningún `MSG_ERROR_BUSQUEDA` en toda la corrida: el espaciado de 25s alcanza para
el rate limit de Voyage.

## Hallazgos del Día 10

| # | Guion | Hallazgo | Estado |
|---|---|---|---|
| G2 | Fecha relativa | El campo `fecha` quedaba literal (`"mañana"`), inútil para quien mire la planilla de Sheets días después | **Corregido en el Día 11**: el system prompt de ruteo lleva la fecha de hoy y resuelve las expresiones relativas a `DD/MM/AAAA` |
| G14 | Ruteo ambiguo | "tienen mesa para cumpleaños" sesga el ruteo hacia el camino de reserva aunque sea una consulta | **Limitación conocida**, no corregida. En la corrida del Día 11 el síntoma no se reprodujo (ruteó a FAQ y dio `MSG_SIN_MATCH`), así que el guion es inestable: cae para un lado o para el otro |
| G6 | Modificar reserva | Al confirmar una reserva se borra el historial del número, así que el mensaje que la corrige arranca sin contexto | **Gap de producción conocido**: haría falta una tool de modificación de reserva, fuera del alcance de estos 11 días de guía |

### Hallazgo nuevo del Día 11

| # | Guion | Hallazgo | Estado |
|---|---|---|---|
| G18 | "el sabado que viene" | El guion es inestable entre dos comportamientos válidos: a veces resuelve la fecha a 15/08/2026 y pregunta solo la hora, y a veces pide que el cliente aclare de qué sábado habla. Los dos salen de la misma instrucción del prompt, que manda resolver las fechas relativas pero **no** inventar cuando son ambiguas — y "el sábado que viene" lo es de verdad (¿el de esta semana o el de la siguiente?) | **Aceptado**: preguntar es preferible a escribir una fecha equivocada en la planilla |
