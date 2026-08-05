---
name: seguir-guia
description: Cómo implementar un día de la guía de estudio del proyecto (docs/guia-estudio.pdf)
---

Cuando te pida trabajar en un día de la guía (ej. "Día 1", "Día 3"):

1. Leé la sección correspondiente en docs/guia-estudio.pdf — buscá el día por su título
   ("Día N — fecha") y leé completa la sección de ese día, incluyendo "El concepto, en
   profundidad", "Qué construimos hoy" y "Resultado esperado al cerrar el día".

2. Tratá "Qué construimos hoy" como especificación funcional (qué tiene que lograr el
   código), no como código para copiar literalmente. Podés implementarlo con mejor
   criterio del que muestra el PDF, siempre que:
   - Cubra el concepto central que ese día quiere enseñar (lo que dice "El concepto,
     en profundidad")
   - Mantenga los nombres de variables, campos y claves de respuesta que código de
     días anteriores ya esté usando en el proyecto, para no romper continuidad
   - Respete la estructura de archivos ya definida en CLAUDE.md

3. Implementá siguiendo el estilo de código que ya está en CLAUDE.md.

4. Verificá tu propio trabajo corriendo lo necesario para confirmar que cumple
   "Resultado esperado al cerrar el día" antes de darlo por terminado. Mostrá la
   evidencia (output del comando, del test, lo que corresponda).

5. Tildá el checkbox del día correspondiente en README.md (sección "Estado del
   proyecto").

6. Al terminar, explicame en 3-5 puntos:
   - Qué implementaste
   - Qué decisiones de diseño tomaste, especialmente si te alejaste de la forma
     más simple/básica de resolverlo, y por qué
   - Si hay algo del código que valga la pena que entienda mejor antes de seguir

7. Preguntame antes de hacer commit, y preguntame antes de hacer push — nunca
   automático.
