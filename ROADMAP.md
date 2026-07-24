# Roadmap

## Plan maestro 0–32

El estado completo vive en
[`packaging/aureon-control-plane.json`](packaging/aureon-control-plane.json) y
se consulta sin escribir con:

```bash
python3 tools/aureonctl status
python3 tools/aureonctl validate
```

Los estados `implemented-awaiting-runtime-validation` significan que el código
y sus pruebas están preparados, pero la prueba de salida todavía necesita una
imagen nueva. Las fases que requieren hardware, firmware, discos físicos o
consentimiento permanecen explícitamente bloqueadas.

## Bloque I — Fundamentos

- [x] Fase 0: contrato de autoridad A–D, privacidad, datos, actualizaciones,
  controladores y modos.
- [x] Fase 1: tags recuperables, artefactos separados y recuperación sin
  sobrescritura.
- [x] Fase 2 (fuente): base fijada por digest, cachés locales fuera del
  contexto, manifiesto fuente e inventario RPM por build.
- [x] Fase 3 (fuente): baseline local ampliado y transporte de evidencia por
  consola serial.
- [ ] Fases 2–3 (runtime): construir dos veces desde estados limpios y comparar
  inventarios, manifiestos y métricas.

## Bloque II — Sistema base ligero

- [x] Fase 4 (fuente): Core KDE/Wayland mínimo y `aureonctl core doctor`.
- [x] Fase 5 (fuente): Liquid Glass, solicitud 1920×1080, observación KScreen,
  GTK/X11 para WSLg y readiness real de KWin/Plasma.
- [x] Fase 6 (fuente): clasificación y auditoría de servicios bajo demanda.
- [ ] Fases 4–6 (runtime): validar una preview nueva y usable con los informes
  automáticos `core`, `baseline` y `services`.

## Bloques posteriores

- 7–10: recursos, memoria, CPU/I/O y arquitectura de datos.
- 11–14: hardware, Driver Fabric, gráficos, audio e input.
- 15–16: kernel y compatibilidad Windows.
- 17–20: gaming y streaming.
- 21–24: seguridad e Integrity.
- 25–28: actualizaciones, firmware e instalador.
- 29–32: laboratorio, comparación, UX y release.

Los fundamentos declarativos de estos bloques existen, pero no equivalen a sus
pruebas de salida. Consulta [el mapa de fases](docs/aureon-phase-map.md) y
[la validación conjunta 2–6](docs/testing/phase-2-6-validation.md).
