# Aureon Desktop Preview

Este directorio documenta la capa de escritorio que se ejecuta únicamente
dentro de una imagen `qcow2` de prueba. Su definición reproducible está en
`system/desktop/`. No instala ni configura Windows, el firmware del equipo,
discos físicos ni el cargador de arranque del host.

La primera variante gráfica usa KDE Plasma en una VM aislada, con red del
guest deshabilitada y sin carpetas compartidas con el host. El usuario
temporal `aureon` existe solo dentro de esa VM, no tiene contraseña utilizable
ni permisos de `sudo`, y entra automáticamente para que puedas ver el
escritorio sin configurar nada en tu PC.

Usa `tools/aureon-desktop-preview --dry-run` para inspeccionar el plan o
consulta [la guía de uso](../docs/testing/desktop-preview.md) para la orden de
PowerShell que abre la ventana de QEMU mediante WSLg.
