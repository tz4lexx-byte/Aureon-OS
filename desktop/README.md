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

Todos estos comandos inspeccionan o crean planes: no instalan controladores, no
transmiten datos, no aplican límites y no realizan cambios de disco. Consulta
[la guía de preview](../docs/testing/desktop-preview.md).
