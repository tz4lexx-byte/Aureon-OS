# Recuperación de la preview

Las previews de escritorio son artefactos de QEMU, no instalaciones en el PC.
Cada build ID crea una imagen base de solo lectura y un overlay escribible
separado. Por ello, apagar la VM o descartar el overlay no afecta Windows ni la
imagen base.

## Estado que se preserva

- `images/desktop-preview-08/aureon-desktop.qcow2` es el primer escritorio
  conservado.
- `images/desktop-preview-09/aureon-desktop.qcow2` es una segunda conversión
  validada.
- Los hashes, logs y manifiestos asociados viven bajo `build/desktop-*`.
- La sesión escribible de cada preview solo está en
  `work/qemu-desktop/<id>/desktop-overlay.qcow2`.

Los artefactos grandes están ignorados por Git deliberadamente. El código,
overlays y políticas son lo que se versiona y permite reconstruirlos.

## Recuperación segura

1. Ejecuta `python3 tools/aureonctl validate` desde el checkout para comprobar
   los contratos fuente sin escribir nada.
2. Conserva una carpeta `images/desktop-<id>/` que haya pasado `qcow2.json`.
3. No reutilices un build ID para una compilación nueva: el launcher rechaza
   sobrescribir evidencia o discos existentes.
4. Para una nueva prueba, usa otro ID. El disco base anterior permanecerá
   intacto.

No hay comando de limpieza automática. El borrado de imágenes queda fuera de
la automatización hasta que exista una confirmación explícita y una revisión de
espacio disponible.
