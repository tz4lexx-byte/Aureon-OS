# Protocolo de benchmark

Una comparación con Windows requiere el mismo equipo, juego, versión, driver,
resolución, ajustes, escenario y condiciones térmicas. Se capturan varias
muestras y se publican dispersión y limitaciones.

Métricas: RAM y CPU en reposo, tiempo de arranque, FPS promedio, 1% y 0.1%
lows, frametime, latencia, consumo, temperatura, compilación de shaders,
cuadros perdidos y tiempo de recuperación. También se publican los casos donde
Windows obtiene un resultado mejor.

No se ejecuta automáticamente desde una VM ni se envía ninguna métrica fuera
del equipo.

## Harness reproducible de medición smoke

`measure-smoke` orquesta repeticiones del runner `test-smoke` sin duplicar su
construcción, aislamiento ni arranque. El modo por defecto es un plan
determinista que no escribe ni invoca QEMU, Podman, `sudo` o red:

```bash
python3 tools/aureon-dev measure-smoke \
  --run-id phase1-immutable \
  --runs 3 \
  --baseline docs/testing/phase0-review-20260724t164040z.json \
  --reuse-base \
  --dry-run
```

Una ejecución futura requiere privilegios ya adquiridos y debe solicitarse
explícitamente con `--execute`; el comando nunca intenta elevarlos. Cada
repetición recibe `<run-id>-rNN`. Con `--reuse-base`, la primera prepara una
única imagen base QCOW2 y las demás reutilizan exactamente esa ruta. Cada
arranque recibe un overlay copy-on-write nuevo; QEMU conecta solo el overlay y
la base nunca se presenta como disco escribible. El SHA-256 de la base se fija
antes del primer arranque y se comprueba después de cada intento. Cualquier
cambio detiene el lote inmediatamente, sin borrar la evidencia ya conservada.
El guest permanece sin red, directorios compartidos ni discos físicos, y el
flujo no cambia el arranque o la instalación de Windows.

La evidencia real vive bajo `work/measurements/<run-id>/`: `measurement.json`
y `measurement.md` resumen el lote, mientras `runs/rNN.json` conserva cada
resultado completado. El JSON usa UTF-8, claves ordenadas, indentación de dos
espacios y rutas relativas; no introduce timestamps. `measurement.json`
registra la ruta y hashes de la base compartida, la ruta y backing file de cada
overlay, si la base permaneció idéntica y si el lote completo puede utilizarse
como baseline final de regresión de arranque.
