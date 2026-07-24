# Validación conjunta de las fases 2–6

El código de las fases 2–6 se valida como un solo lote para no reconstruir una
imagen grande después de cada cambio pequeño. La siguiente imagen nueva será la
primera que pueda aportar esta evidencia completa; las previews anteriores no
se modifican retroactivamente.

## Evidencia automática del build

`aureon-desktop-preview` conserva, por build ID:

- digest de todas las fuentes que sí forman parte del contexto;
- exclusión coincidente de `__pycache__`, `.pyc` y `.pyo` tanto en el digest
  como en el contexto de Podman;
- digest OCI derivado;
- inventario RPM ordenado y su SHA-256 en
  `build/desktop-<id>/desktop-packages.lock.json`;
- SHA-256 y metadatos del `qcow2`;
- argumentos QEMU, adaptador de vídeo, backend GTK y modo solicitado;
- captura directa del framebuffer por QMP local, con dimensiones, SHA-256,
  diversidad de color y rango dinámico muestreado.

El inventario de paquetes es evidencia de la build, no un lock de release. La
reproducibilidad de release seguirá pendiente hasta repetir desde un checkout
limpio y comparar dos inventarios y manifiestos independientes.

## Evidencia automática del guest

El marcador `AUREON_DESKTOP_READY` ya no se emite al arrancar `greetd`. Primero
la sesión debe demostrar:

1. procesos `kwin_wayland` y `plasmashell` vivos;
2. respuesta de ambos por DBus;
3. salida KScreen JSON observada en `1920x1080`, ~60 Hz y escala 1;
4. apariencia Liquid Glass aplicada antes del marcador;
5. baseline local disponible;
6. Core mínimo sin componentes opcionales instalados automáticamente;
7. unidades Gaming, Streaming e Integrity inactivas y no habilitadas al
   arranque.

Los tres informes JSON (`baseline`, `core` y `services`) se codifican en la
consola serial y el launcher los incorpora a la evidencia de la preview. No se
usa red y no se enumera una lista general de procesos.

## Puerta de salida del lote

La implementación puede pasar pruebas unitarias antes de construir, pero las
fases permanecen como `implemented-awaiting-runtime-validation` hasta que una
imagen nueva:

- muestre el escritorio de forma usable;
- registre `display_state=observed-1920x1080@60`;
- produzca un framebuffer QMP 1920×1080 no uniforme;
- incluya los tres informes del guest;
- cierre QEMU limpiamente;
- mantenga intacto el hash del disco base.
