# ADR-0003: Conversión QCOW2 de Fase 0 y consola serial

- Estado: aceptado; ejecución manual completada y runner acotado implementado. Falta una repetición real mediante el runner antes de declarar reproducibilidad.
- Fecha: 2026-07-18
- Decisores: equipo de Aureon OS

## Contexto

El primer artefacto de Aureon debe arrancar de forma verificable en una VM UEFI sin instalar nada en el host. Fedora bootc no declara por defecto un filesystem raíz para todos los flujos de creación de disco, y un smoke headless necesita una señal observable y un cierre limpio sin depender de credenciales ni red.

## Decisión

1. La conversión de Fase 0 producirá exclusivamente un `qcow2` x86-64/UEFI, nunca un destino de bloque físico.
2. Se usará `ext4` como filesystem raíz explícito. Es la opción conservadora para el primer disco de prueba y evita depender de una selección implícita del builder.
3. El guest declara `console=tty0` y `console=ttyS0,115200n8` mediante `kargs.d`; el runner captura el primer puerto serie de QEMU.
4. El guest emite `AUREON_PHASE0_READY` después de llegar a `multi-user.target` y solicita un apagado limpio. El runner considera éxito solo si observa exactamente un marcador, el apagado posterior y la salida normal de QEMU.
5. Sin `/dev/kvm`, el runner seleccionará TCG solo como fallback funcional. Sus tiempos no son benchmarks ni se comparan con KVM/WHPX.
6. El convertidor del experimento es el CLI unificado upstream `image-builder`, fijado como `ghcr.io/osbuild/image-builder-cli@sha256:700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5` (versión `1`, commit `08ccdf050b4a5b190f0c500122e6c5763e56ccd8`). El conversor histórico `bootc-image-builder` queda excluido por su señal `build_tainted: true` y no participa en la conversión de Fase 0.

## Invariantes

- La referencia OCI de entrada y la del convertidor deben ser digests `linux/amd64` registrados antes de descargar capas o ejecutar un build.
- La conversión privilegiada requiere `test-smoke --execute` explícito, root dentro de Linux/WSL, un `build-id` nuevo, imágenes locales por digest y allowlist de mounts.
- El único mount Windows-visible de salida escribible será `images/<build-id>/`; no se pasa ningún `/dev`, disco Windows, partición ni directorio personal como entrada del guest. Ese mount pertenece al contenedor conversor, no al guest de QEMU.
- El firmware OVMF de código se abre de solo lectura; sus variables se copian a `work/qemu/<build-id>/` antes de arrancar.
- La VM inicia con red deshabilitada y con un overlay `qcow2` efímero; el `qcow2` base no se abre para escritura.

## Consecuencias

- La Fase 0 puede tardar más bajo TCG, pero produce una prueba funcional reproducible sin asumir aceleración disponible.
- Un cierre automático limita la inspección interactiva de esta imagen mínima; perfiles posteriores usarán un flujo separado para login y escritorio.
- El CLI unificado ya inspeccionó la base de forma aislada. `bootc-image-builder` se conserva solo como evidencia histórica excluida hasta que exista una explicación upstream apta para release.

## Evidencia requerida antes de cerrar la reproducibilidad

1. Digests y versión efectiva del convertidor descargado.
2. Log completo de build/conversión y hash SHA-256 del `qcow2`.
3. Comando QEMU efectivo, configuración OVMF y acelerador declarado.
4. Log serie con `AUREON_PHASE0_READY` y salida limpia de QEMU.
5. Confirmación de que las rutas escritas quedan bajo el `build-id` aprobado.

La ejecución manual `phase0-f44-20260718` ya aporta los puntos 1–4 para una cadena aislada. El runner implementado conserva los mismos límites, pero necesita producir una segunda evidencia con un `build-id` nuevo antes de cerrar la reproducibilidad de Fase 0.
