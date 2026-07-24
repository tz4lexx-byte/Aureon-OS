# Estado verificado

## Fase actual

Las fases maestras 0-1 tienen su fundamento protegido y etiquetado. El codigo
de las fases 2-6 esta en estado `implemented-awaiting-runtime-validation`:
paso la validacion fuente y las pruebas unitarias, pero todavia necesita una
repeticion runtime nueva antes de declararse completo.

Las fases de hardware, firmware, instalacion, controladores propietarios y
compatibilidad real siguen bloqueadas por sus gates; una preview QEMU no puede
cerrarlas.

## Hechos confirmados

- Windows, sus discos, BIOS, bootloader y configuracion de arranque no fueron
  destinos. Todo vive en Ubuntu WSL, Podman y artefactos virtuales del checkout.
- WSL2 `Ubuntu-24.04`, Podman, QEMU, `qemu-img`, OVMF y KVM funcionaron en las
  ejecuciones documentadas.
- `python3 tools/aureon-dev doctor` termina con `Readiness: READY` cuando se
  ejecuta contra `Ubuntu-24.04` desde Windows.
- En WSL se ejecutaron 92 pruebas unitarias y todas pasaron.
- Los tres fallos vistos desde Windows eran incompatibilidades de rutas
  Windows/bash, no defectos del proyecto.
- La cadena bootc -> OCI -> `qcow2` -> QEMU produjo y arranco imagenes
  aisladas.
- `preview-10` es una imagen historica. Tanto `virtio` como `std` alcanzaron
  `graphical.target`, pero el frontend de WSLg siguio mostrando una ventana
  gris; por ello no se considera escritorio usable.
- `preview-13` completo OCI, inventario de 1193 RPM, conversion `qcow2` y
  arranque QEMU. Su serial confirmo que Virtio DRM rechazo el karg
  `video=Virtual-1:1920x1080@60` y que la sesion no supero el probe real.
- El marcador antiguo `AUREON_DESKTOP_READY` era un falso positivo: se emitia
  al iniciar `greetd`, antes de comprobar KWin y Plasma.
- Dos archivos `.pyc` locales fueron incluidos en `preview-10`. La proxima
  build los excluye del contexto y del digest mediante reglas coincidentes.
- El tag recuperable de fuente mas reciente es `aureon-liquid-glass-v0.2.0`.
  Los cambios del lote 2-6 permanecen en la rama de trabajo hasta su
  validacion runtime.

## Lote de fases 2-6 implementado en fuente

- Fase 2: filtrado determinista de fuentes, digest, inventario RPM por build y
  diagnostico `aureonctl reproducibility`.
- Fase 3: baseline ampliado con CPU, carga, actividad de red/disco, errores y
  temperatura local cuando esta disponible.
- Fase 4: `aureonctl core doctor` verifica los paquetes minimos y que Steam,
  Wine, Gamescope y OBS no entren automaticamente en Core.
- Fase 5: Liquid Glass, wallpaper vectorial 1920x1080, EDID Full HD, KScreen
  JSON a 60 Hz/escala 1, backend GTK/X11 configurable, sesion D-Bus oficial
  de Fedora y captura QMP directa del framebuffer.
- Fase 6: `aureonctl services doctor` comprueba solo las unidades declaradas de
  Gaming, Streaming e Integrity, sin enumerar una lista general de procesos.
- El guest emite los informes `baseline`, `core` y `services` por la consola
  serial; el launcher los incorpora a la evidencia JSON de una build nueva.

## Evidencia pendiente

1. Construir una imagen nueva (siguiente ID sugerido: `preview-14`).
2. Observar `display_state=observed-1920x1080@60` y un framebuffer QMP
   1920x1080 no uniforme.
3. Confirmar los tres informes del guest, el inventario RPM y el cierre limpio.
4. Repetir despues desde un checkout limpio y comparar inventarios/manifiestos.
5. Revisar por separado los AVC de SELinux antes de cualquier perfil release.

El protocolo exacto esta en
[`docs/testing/phase-2-6-validation.md`](docs/testing/phase-2-6-validation.md).
