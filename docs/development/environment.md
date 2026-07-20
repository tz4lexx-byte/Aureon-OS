# Entorno de desarrollo — estado actual

Fecha de observación: 18–19 de julio de 2026. Esta página separa el host Windows del guest Ubuntu de WSL2 para no confundir una herramienta virtual con una modificación del sistema anfitrión.

## Disponible

| Entorno | Herramienta o capacidad | Resultado observado |
| --- | --- | --- |
| Windows | Git | `2.53.0.windows.1` en `C:\Program Files\Git\cmd\git.exe`. |
| Windows | CMake | `4.2.3` en `C:\Program Files\CMake\bin\cmake.exe`. |
| Windows | WSL2 | `Ubuntu-24.04` está inicializado y permite abrir una sesión Linux. |
| Ubuntu WSL2 | Python | Python `3.12.3` disponible. |
| Ubuntu WSL2 | OCI | Podman `4.9.3`; se verificaron consultas rootless y rootful. |
| Ubuntu WSL2 | VM | QEMU `8.2.2`, `qemu-img` y OVMF están instalados. |
| Ubuntu WSL2 | Aceleración | `/dev/kvm` estuvo disponible; la VM documentada arrancó con KVM y se apagó limpiamente. |

Las herramientas de la tabla de Ubuntu viven dentro del disco virtual de la distribución WSL. No se instalaron como servicios, controladores ni firmware de Windows, y no se ha usado ningún disco físico como destino de Aureon.

## Qué está preparado y qué no

El guest aloja las entradas fijadas de la cadena de build: se descargaron la base Fedora bootc y el CLI unificado `image-builder` por digest, y este último inspeccionó la base en un contenedor aislado. La ejecución manual `phase0-f44-20260718` creó una OCI derivada, un `qcow2` válido y una VM de Aureon que emitió `AUREON_PHASE0_READY` y se apagó limpiamente.

`aureon-dev` tiene dos comandos de planificación seguros:

- `build` emite un manifiesto JSON versionado con entradas declaradas, hashes y rutas planeadas.
- `image` hace lo mismo para un destino `.qcow2`, y rechaza rutas fuera del checkout, extensiones no permitidas y dispositivos físicos.

Ambos se ejecutan en modo *dry-run* por defecto: no escriben manifiestos, imágenes ni archivos temporales; no invocan WSL, red, Podman, QEMU o un builder. Sus modos `--execute` siguen cerrados porque el único ejecutor aprobado de Fase 0 es `test-smoke --execute`, con una cadena completa y acotada en lugar de pasos parciales.

La receta bootc tiene el gate activo para la cadena completa aprobada. Las entradas inmutables, el modo de almacenamiento dedicado y los mounts permitidos están revisados; no obstante, cada build OCI o conversión privilegiada exige aprobación explícita. `aureon-dev test-smoke --execute` exige root dentro de WSL, un `build-id` nuevo, imágenes locales ya fijadas y espacio libre suficiente; no descarga, no limpia automáticamente ni toca Windows.

## Límites y pendientes

1. KVM funcionó en la ejecución documentada, pero una sola muestra no es un benchmark ni garantiza que estará expuesto en cada sesión WSL futura.
2. `doctor` ya incluye probes WSL de solo lectura cuando se ejecuta en Windows: valida `Ubuntu-24.04`, `x86_64`, Python, Podman, QEMU, `qemu-img`, OVMF y la disponibilidad opcional de KVM dentro del guest. Esa integración está cubierta por pruebas unitarias; la validación final debe ejecutarse desde la sesión Windows del propietario de WSL, porque las distribuciones WSL son por usuario.
3. La instalación de paquetes creó enlaces de systemd para Podman y `qemu-kvm` dentro de Ubuntu. Se auditó el estado y se detuvieron/deshabilitaron `podman-auto-update.timer`, `podman.socket` y `qemu-kvm.service`; esto no cambia servicios de Windows. `podman.service` estaba inactivo y se conserva para uso explícito de CLI.
4. La conversión con el CLI unificado requiere privilegios dentro de Linux. La ejecución documentada usó red deshabilitada, store dedicado y una salida virtual limitada; el runner conserva esos límites y requiere `--execute` explícito por invocación.

## Comandos de diagnóstico seguros

Desde PowerShell, las siguientes consultas no instalan paquetes ni crean imágenes:

```powershell
wsl.exe -l -v
wsl.exe -d Ubuntu-24.04 -- podman --version
wsl.exe -d Ubuntu-24.04 -- qemu-system-x86_64 --version
wsl.exe -d Ubuntu-24.04 -- qemu-img --version
wsl.exe -d Ubuntu-24.04 -- sh -lc 'test -r /dev/kvm && echo KVM-disponible || echo KVM-no-disponible'
```

Desde la raíz del checkout dentro de Ubuntu WSL2, estos planes solo leen entradas declaradas e imprimen JSON a la consola:

```bash
python3 tools/aureon-dev build --build-id review --dry-run
python3 tools/aureon-dev image --build-id review --dry-run
python3 tools/aureon-dev test-smoke --build-id review --dry-run
```

No se debe interpretar una ruta mostrada por esos comandos como un archivo existente. El único modo de ejecución implementado es `test-smoke --execute`, que debe correrse con un `build-id` nuevo y root dentro de WSL; los otros `--execute` siguen siendo guardrails sin efectos.
