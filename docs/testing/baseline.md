# Medición inicial local

Desde Ubuntu WSL o desde una imagen Aureon nueva, el informe se genera sin red
y sin guardar nada por sí mismo:

```bash
python3 tools/aureonctl baseline > aureon-baseline.json
```

La redirección es intencional: el usuario decide cuándo y dónde conservar el
archivo. El informe contiene métricas de arranque, memoria, servicios,
filesystem, PSI, carga, CPU ocupada durante una ventana de un segundo,
actividad local de red y disco, errores de arranque, temperatura cuando está
disponible, SELinux, cgroup y herramientas gráficas; no se transmite. Una
medición WSL se etiqueta como entorno de desarrollo y no sirve para afirmar
rendimiento de hardware o GPU.

En una preview nueva el mismo informe se recoge automáticamente después de que
KWin y Plasma respondan, y se conserva dentro de la evidencia de la sesión.

## Baseline de Phase 0 para mediciones smoke

El baseline histórico
`docs/testing/phase0-review-20260724t164040z.json` es evidencia inmutable. El
harness `measure-smoke` carga de él `readiness_after_seconds` y
`wall_duration_seconds` para calcular la variación porcentual de las medias de
un lote nuevo. También agrega mínimo, máximo, media y mediana de readiness,
duración total y tamaño de overlay, sin alterar los valores Phase 0.
