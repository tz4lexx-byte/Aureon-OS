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
  --run-id phase1-baseline \
  --runs 3 \
  --baseline docs/testing/phase0-review-20260724t164040z.json \
  --dry-run
```

Una ejecución futura requiere privilegios ya adquiridos y debe solicitarse
explícitamente con `--execute`; el comando nunca intenta elevarlos. Cada
repetición recibe `<run-id>-rNN`, conserva un overlay copy-on-write
independiente y se detiene en el primer fallo sin borrar la evidencia previa.
El guest permanece sin red, directorios compartidos ni discos físicos.

La evidencia real vive bajo `work/measurements/<run-id>/`: `measurement.json`
y `measurement.md` resumen el lote, mientras `runs/rNN.json` conserva cada
resultado completado. El JSON usa UTF-8, claves ordenadas, indentación de dos
espacios y rutas relativas; no introduce timestamps.
