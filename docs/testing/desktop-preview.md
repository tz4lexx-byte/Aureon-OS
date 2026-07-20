# Escritorio de prueba Aureon

Esta es una vista previa interactiva de KDE Plasma dentro de una VM QEMU. No
es una instalación de Aureon en el equipo: Windows sigue siendo el sistema de
arranque y no se modifica el BIOS, el bootloader, particiones ni discos
físicos.

## Qué crea

Al ejecutarse con un `build-id` nuevo, el lanzador solo crea estos artefactos
del proyecto:

```text
build/desktop-<id>/
images/desktop-<id>/aureon-desktop.qcow2
work/qemu-desktop/<id>/desktop-overlay.qcow2
```

El archivo `aureon-desktop.qcow2` queda de solo lectura para la ventana QEMU.
Todo cambio de la sesión se escribe en `desktop-overlay.qcow2`, por lo que no
afecta ni Windows ni la imagen base. La VM no recibe NIC, carpetas compartidas,
passthrough USB ni rutas de disco físico.

## Primera ejecución

La primera ejecución descarga los paquetes Fedora de KDE dentro del store
dedicado de Podman **en Ubuntu WSL**. Por ello exige
`--allow-build-network`; solo esa etapa de preparación usa red. La conversión
del disco y la VM permanecen sin red. Necesita aproximadamente 35 GiB libres
en el disco donde está el checkout y puede tardar bastante la primera vez.

Desde PowerShell, pega esta orden completa:

```powershell
wsl.exe -d Ubuntu-24.04 --cd /mnt/c/Users/pc/Documents/Codex/2026-07-18/aureon-os -- bash -lc 'sudo -E /usr/bin/python3 tools/aureon-desktop-preview --build-id preview-01 --execute --allow-build-network'
```

`sudo` pedirá la contraseña que creaste para **Ubuntu/WSL**, no la contraseña
ni el PIN de Windows. Cuando termine de crear la imagen aparecerá una ventana
de QEMU con el escritorio. Puedes usarla normalmente y apagarla desde el menú
de Plasma; la orden termina al cerrarse la VM.

Antes, si quieres comprobar que no escribe nada, usa:

```powershell
wsl.exe -d Ubuntu-24.04 --cd /mnt/c/Users/pc/Documents/Codex/2026-07-18/aureon-os -- /usr/bin/python3 tools/aureon-desktop-preview --build-id preview-01 --dry-run
```

Si el backend gráfico no está disponible, instala dentro de Ubuntu WSL el
paquete `qemu-system-gui` y vuelve a ejecutar la orden. No hace falta tocar el
BIOS ni instalar un sistema operativo en el disco del PC.

## Abrir una preview ya creada, sin recompilar

Si ya existe una conversión validada, por ejemplo `preview-09`, no hace falta
volver a descargar paquetes ni crear otro disco base. Esta orden genera solo
un overlay virtual nuevo para esa sesión y abre la ventana:

```powershell
wsl.exe -d Ubuntu-24.04 --cd /mnt/c/Users/pc/Documents/Codex/2026-07-18/aureon-os -- bash -lc 'sudo -E /usr/bin/python3 tools/aureon-desktop-preview --run-existing --build-id preview-09 --session-id aur-01 --execute'
```

No uses `--allow-build-network` con `--run-existing`: no descarga ni construye
nada. Para otra sesión cambia únicamente `--session-id`, por ejemplo
`aur-02`. La imagen base queda de solo lectura y el estado de la sesión vive
en `work/qemu-desktop/preview-09/sessions/aur-01/`.

## Límites de esta fase

- Es una preview de desarrollo, no una versión para instalar en hardware real.
- El usuario `aureon` es desechable y solo existe dentro de la VM; no hay SSH,
  contraseña de usuario ni acceso a tus archivos de Windows.
- La aceleración gráfica usa `virtio-vga` en modo software (`gl=off`) a través
  de WSLg. Es útil para ver y usar el escritorio, no para medir rendimiento de
  GPU.
- Conserva los artefactos si algo falla; no borra automáticamente ejecuciones
  anteriores. Para reintentar, usa otro `build-id`, por ejemplo `preview-02`.
