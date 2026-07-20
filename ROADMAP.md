# Roadmap

## Fase 0 — Investigación y cimientos

- [x] Crear repositorio local aislado.
- [x] Registrar la decisión de base del sistema y sus alternativas.
- [x] Documentar modelo inicial de amenazas y presupuesto de rendimiento.
- [x] Implementar `aureon-dev doctor` de solo lectura, con pruebas unitarias.
- [x] Configurar `Ubuntu-24.04` en WSL2 y verificar Podman, QEMU, `qemu-img` y OVMF dentro del guest.
- [x] Implementar `aureon-dev build` e `image` como planes deterministas de *dry-run*, con rechazo de rutas externas, discos físicos y modos de ejecución no verificados.
- [x] Completar la revisión por digest de la base Fedora bootc y del CLI unificado `image-builder` antes de activar el experimento de receta.
- [ ] Ejecutar y aprobar el runner reproducible de una imagen bootc mínima. El runner `test-smoke --execute` y sus pruebas unitarias ya existen; falta su primera ejecución real con un build ID nuevo.
- [x] Convertir la imagen derivada a `qcow2` dentro de una ruta virtual permitida (`phase0-f44-20260718`).
- [x] Arrancar esa imagen con QEMU y OVMF, capturar consola serial y apagar limpiamente con KVM (`phase0-f44-20260718`).
- [ ] Ejecutar `aureon-dev test-smoke --execute` y guardar la primera evidencia verificable. El modo *dry-run*, las validaciones de seguridad y el runner ya están implementados.
- [x] Revisar las unidades systemd creadas por los paquetes de Podman/QEMU dentro de WSL antes del primer build real.

### Criterio de salida

Desde un checkout limpio, un comando implementado y revisado construye una imagen mínima a partir de referencias fijadas, usa solo almacenamiento virtual permitido, la arranca en QEMU, confirma el target de systemd definido, ejecuta un smoke test, guarda logs y apaga la VM. La evidencia debe registrar ID de build, hashes, acelerador, duración, rutas de imagen y logs. Un resultado con TCG es funcional, no un benchmark.

## Fase 1 — Escritorio funcional

Wayland, login, sesión, panel, lanzador, notificaciones, controles básicos, terminal y explorador de archivos. No comienza hasta que Fase 0 sea reproducible.

## Fases posteriores

2. Identidad visual y accesibilidad.
3. Aureon Insight y `aureond`.
4. Actualizaciones atómicas, rollback y recovery.
5. Gaming.
6. Instalador y pruebas de hardware real dedicado.
7. Beta, localización y auditoría.

Los criterios detallados de cada fase se añaden antes de comenzar su implementación.
