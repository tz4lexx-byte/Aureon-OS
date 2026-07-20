# Medición inicial local

Desde Ubuntu WSL o desde una imagen Aureon nueva, el informe se genera sin red
y sin guardar nada por sí mismo:

```bash
python3 tools/aureonctl baseline > aureon-baseline.json
```

La redirección es intencional: el usuario decide cuándo y dónde conservar el
archivo. El informe contiene métricas de arranque, memoria, servicios,
filesystem, PSI, estado de SELinux, cgroup y herramientas gráficas; no se
transmite. Una medición WSL se etiqueta como entorno de desarrollo y no sirve
para afirmar rendimiento de hardware o GPU.
