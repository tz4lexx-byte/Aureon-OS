# Aureon Desktop Preview

La capa de escritorio vive en `system/desktop/` y se ejecuta únicamente dentro
de un `qcow2` desechable. No instala ni configura Windows, firmware, discos
físicos ni el cargador de arranque del host.

La preview usa KDE Plasma/Wayland, un usuario temporal sin contraseña ni sudo,
guest sin red y overlays QEMU separados. El próximo build incorpora:

- Aureon Liquid Glass con assets SVG locales;
- modo solicitado y observado de 1920×1080 a escala 1;
- marcador de sesión solo después de KWin/Plasma responsivos;
- inventario de paquetes y baseline local;
- diagnósticos `aureon-core`, `aureon-services`, `aureon-hardware`,
  `aureon-driver`, `aureon-resource` y `aureon-integrity`.

## Aureon System Overview

El panel inferior incluye una entrada **Aureon System Overview** junto al área
de estado. Al abrirla muestra versión del sistema y kernel, arquitectura, CPU
lógicas, memoria, almacenamiento principal, tiempo encendido y estado general.

El plasmoide consulta de forma asíncrona el contrato local y de solo lectura
`aureonctl overview`. El proveedor limita sus lecturas a `/etc/os-release`,
`/proc/meminfo`, `/proc/uptime` y estadísticas del sistema de archivos raíz;
no muestra hostname, usuario ni identificadores de hardware. Si una fuente o
el helper no está disponible, conserva el resto de datos y muestra
`Unavailable`. Actualmente es un resumen local: no diagnostica componentes,
no monitoriza en tiempo real y no sustituye los comandos `doctor`.

Todos estos comandos inspeccionan o crean planes: no instalan controladores, no
transmiten datos, no aplican límites y no realizan cambios de disco. Consulta
[la guía de preview](../docs/testing/desktop-preview.md).
