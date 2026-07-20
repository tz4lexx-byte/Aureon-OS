# CI

La Fase 0 define el siguiente orden de validación:

1. Formato y lint.
2. Pruebas unitarias del tooling.
3. Build reproducible de la imagen.
4. Arranque QEMU headless.
5. Smoke test y recolección de logs.
6. Escaneo de secretos y de dependencias antes de publicar artefactos.

La configuración de un proveedor concreto queda pendiente de seleccionar el remoto del proyecto. Un pipeline no debe marcar como correcto un paso de imagen o arranque que no se haya ejecutado.

Mientras se selecciona proveedor, el contrato local reutilizable es:

```bash
python3 -m unittest discover -s tests/unit -p 'test_*.py'
python3 tools/aureon-dev test-smoke --build-id ci-review --dry-run
```

El smoke real requiere un runner Linux/WSL con root, imágenes locales ya
precargadas y un build ID nuevo. Debe ejecutarse explícitamente con
`test-smoke --execute`; no se habilita en un proveedor remoto hasta revisar sus
límites de privilegios, almacenamiento y virtualización.
