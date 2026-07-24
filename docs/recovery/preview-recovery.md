# Recuperación de la preview

Las previews de escritorio son artefactos de QEMU, no instalaciones en el PC.
Cada build ID crea una imagen base de solo lectura y un overlay escribible
separado. Por ello, apagar la VM o descartar el overlay no afecta Windows ni la
imagen base.

## Estado que se preserva

- El código recuperable está etiquetado como
  `aureon-liquid-glass-v0.2.0`; los cambios posteriores permanecen en la rama
  de trabajo hasta superar la próxima validación.
- `preview-10` es evidencia histórica con readiness antiguo. `preview-13`
  llegó a `qcow2` y QEMU, pero falló el contrato gráfico; ninguna se acepta en
  `--run-existing` como escritorio usable.
- Los hashes, logs y manifiestos asociados viven bajo `build/desktop-*`.
- Cada sesión nueva usa su propio overlay en
  `work/qemu-desktop/<id>/sessions/<session-id>/desktop-overlay.qcow2`.

Los artefactos grandes están ignorados por Git deliberadamente. El código,
overlays y políticas son lo que se versiona y permite reconstruirlos.

## Recuperación segura

1. Ejecuta `python3 tools/aureonctl validate` desde el checkout para comprobar
   los contratos fuente sin escribir nada.
2. Conserva una carpeta `images/desktop-<id>/` que tenga evidencia
   `qcow2.json` con estado `passed`.
3. No reutilices un build ID ni un session ID: el launcher rechaza sobrescribir
   evidencia o discos existentes.
4. Para una build nueva usa otro ID. La imagen base anterior permanece intacta.
5. Para regresar al último código etiquetado, crea una rama aparte desde el tag;
   no borres ni sobrescribas el trabajo actual.

No hay limpieza automática. El borrado de imágenes exige una decisión
explícita y rutas exactas dentro de `build/`, `images/` y `work/qemu-desktop/`.
