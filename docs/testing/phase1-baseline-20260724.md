# Baseline exploratorio Phase 1 — 2026-07-24

Las tres ejecuciones de `phase1-baseline-20260724` pasaron con aceleración KVM,
4096 MiB de memoria, 2 vCPU y las políticas de aislamiento de `test-smoke`:
guest sin red, sin directorios del host, sin dispositivos de bloque físicos y
sin cambios de instalación o arranque de Windows.

## Resultados

| Repetición | Readiness | Duración total | Estado |
| --- | ---: | ---: | --- |
| r01 | 72.025 s | 88.284 s | passed |
| r02 | 71.865 s | 84.872 s | passed |
| r03 | 68.873 s | 81.880 s | passed |

El readiness medio fue **70.921 s** y la duración media fue **85.012 s**. Frente
a la evidencia Phase 0, las variaciones fueron **+11.28 %** en readiness y
**+12.62 %** en duración total.

## Interpretación

Esta evidencia se clasifica como `exploratory-baseline`, no como baseline final
para regresiones de arranque. Los SHA-256 de las imágenes base difieren entre
r01, r02 y r03, por lo que las repeticiones no partieron de una imagen binaria
idéntica. Además, tanto readiness como duración descendieron de r01 a r03; puede
existir un efecto de caché caliente o de orden.

El siguiente experimento debe reutilizar una única imagen base inmutable y
crear tres overlays copy-on-write independientes. Así separará la variación de
arranque de la variación introducida al reconstruir la base.

La evidencia compacta revisada está en
`docs/testing/phase1-baseline-20260724.json`; sus rutas apuntan a la evidencia
original bajo `work/measurements/phase1-baseline-20260724/` sin copiar los logs.
