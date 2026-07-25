# Baseline final de arranque inmutable de Phase 1

`phase1-immutable-20260724` midió tres arranques smoke de Aureon con KVM,
4096 MiB de memoria y 2 vCPU. Las tres ejecuciones solicitadas se completaron y
aprobaron; no hubo fallos.

La medición reutilizó una sola base QCOW2 inmutable,
`images/phase1-immutable-20260724-r01/aureon-base.qcow2`. Cada ejecución utilizó
un overlay copy-on-write independiente, pero los tres overlays declararon esa
misma base como backing file. El SHA-256 de la base fue
`af623a046c3f3fecce8fd39b4262efbe0724b543013cafe3ef2da355a03b7221`
antes de la primera ejecución y permaneció idéntico después de cada una. Por
ello, la base compartida no cambió y las imágenes base fueron idénticas entre
repeticiones.

## Resultados

| Repetición | Estado | Readiness (s) | Duración (s) | Overlay (bytes) |
| --- | --- | ---: | ---: | ---: |
| r01 | passed | 66.058 | 80.317 | 24510464 |
| r02 | passed | 73.803 | 87.062 | 24444928 |
| r03 | passed | 75.544 | 90.053 | 24444928 |

Readiness tuvo un mínimo de 66.058 s, una mediana de 73.803 s, un máximo de
75.544 s y un promedio de 71.80166666666666 s. La duración total tuvo un mínimo
de 80.317 s, una mediana de 87.062 s, un máximo de 90.053 s y un promedio de
85.81066666666668 s. El tamaño de los overlays tuvo un mínimo y una mediana de
24444928 bytes, un máximo de 24510464 bytes y un promedio de
24466773.333333332 bytes.

## Comparación con Phase 0

El baseline de Phase 0 usado fue
`docs/testing/phase0-review-20260724t164040z.json`, con readiness de 63.733 s y
duración de 75.488 s. Frente a esos valores, el promedio de Phase 1 aumentó
12.660108054958444 % en readiness y 13.674579624134534 % en duración total.

## Alcance

El guest se ejecutó sin red, sin directorios del host montados, sin acceso a
dispositivos de bloques físicos y sin cambios al arranque o la instalación de
Windows. Con las tres repeticiones aprobadas, una base inmutable verificada y
overlays independientes, el resultado es apto como baseline final de regresión
de arranque para este entorno.

Este baseline permite detectar regresiones futuras cuando se conservan el mismo
host, los mismos recursos y el mismo protocolo. No demuestra todavía
rendimiento equivalente ni tiempos directamente transferibles a hardware
distinto.

La evidencia original se conserva en
`work/measurements/phase1-immutable-20260724/measurement.json`,
`work/measurements/phase1-immutable-20260724/measurement.md` y los resultados
individuales bajo `work/measurements/phase1-immutable-20260724/runs/`.
