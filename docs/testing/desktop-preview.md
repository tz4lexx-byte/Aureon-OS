# Escritorio de prueba Aureon

Esta es una preview de KDE Plasma dentro de una VM QEMU. No instala Aureon en
el PC: Windows conserva el arranque y el launcher no modifica BIOS, bootloader,
particiones ni discos físicos.

## Aislamiento

Cada build crea únicamente artefactos bajo el checkout:

```text
build/desktop-<id>/
images/desktop-<id>/aureon-desktop.qcow2
work/qemu-desktop/<id>/
```

El `qcow2` base queda de solo lectura y cada apertura utiliza un overlay nuevo.
La VM no recibe NIC, carpetas compartidas, USB físico ni rutas de discos del
host.

## Próxima validación del lote 2–6

Las previews existentes no incorporan el nuevo marcador de sesión ni la
comprobación Full HD. Cuando se decida probar el lote completo, se construirá
un ID nuevo, por ejemplo `preview-14`:

```powershell
wsl.exe -d Ubuntu-24.04 --cd /mnt/c/Users/pc/Documents/Codex/2026-07-18/aureon-os -- bash -lc 'sudo -E /usr/bin/python3 tools/aureon-desktop-preview --build-id preview-14 --video virtio --gtk-backend x11 --execute --allow-build-network'
```

`sudo` pide la contraseña del usuario Ubuntu/WSL, no el PIN ni la contraseña de
Windows. El build necesita aproximadamente 35 GiB libres. La red se permite
solo durante la descarga explícita de paquetes Fedora; la conversión y el guest
permanecen sin red.

La preview solicita `1920x1080@60`, escala 1 y `virtio-vga` con EDID. El kernel
ya no fuerza `video=Virtual-1`: `preview-13` demostró que Virtio rechazaba ese
modo. KScreen selecciona y vuelve a observar el modo desde JSON. Plasma se
inicia con el wrapper D-Bus oficial incluido por Fedora, y QEMU conserva una
captura interna PPM mediante QMP local. Esto permite distinguir un framebuffer
guest correcto de un fallo de presentación GTK/WSLg.

## Abrir una imagen validada sin reconstruir

Usa siempre un session ID nuevo:

```powershell
wsl.exe -d Ubuntu-24.04 --cd /mnt/c/Users/pc/Documents/Codex/2026-07-18/aureon-os -- bash -lc 'sudo -E /usr/bin/python3 tools/aureon-desktop-preview --run-existing --build-id preview-14 --session-id usable-01 --execute'
```

`--run-existing` solo acepta una base que ya haya superado el contrato visual
actual; por eso rechaza `preview-10` y cualquier build fallida. No añadas
`--allow-build-network`: esa ruta nunca descarga ni recompila. Para comparar la tarjeta clásica puede añadirse `--video std`;
para comparar el frontend anterior, `--gtk-backend wayland`.

## Evidencia y límites

Una build nueva conserva inventario RPM, hashes, logs, parámetros gráficos y
los informes JSON `baseline`, `core` y `services` emitidos por el guest. Consulta
[`phase-2-6-validation.md`](phase-2-6-validation.md) para la puerta completa.

Sigue siendo una preview de desarrollo con renderizado por software (`gl=off`),
no una medición de GPU ni una imagen apta para instalar en hardware real.
