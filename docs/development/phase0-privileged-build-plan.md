# Plan de ejecución privilegiada — Aureon Fase 0

Estado: **validado una vez con `phase0-f44-20260718`; runner `test-smoke --execute` implementado y pendiente de su primera ejecución real**. Este documento describe la conversión que requiere aprobación humana explícita por invocación.

## Alcance y almacenamiento

| Recurso | Ruta prevista | Regla |
| --- | --- | --- |
| Store Podman dedicado | `/var/lib/aureon-phase0-podman/storage` dentro de Ubuntu WSL | Disco virtual de WSL; separado del store global de Podman. |
| Estado temporal Podman | `/run/aureon-phase0-podman` dentro de Ubuntu WSL | Efímero dentro de la distribución WSL. |
| Salida del conversor | `images/<build-id>/` | Único mount Windows-visible escribible de salida; contiene solo artefactos virtuales de la build. |
| Imagen base de VM | `images/<build-id>/aureon-base.qcow2` | Se obtiene del output del conversor y se abre de solo lectura en QEMU. |
| Estado de arranque | `work/qemu/<build-id>/` | Overlay qcow2, copia de variables OVMF y logs; no se reutiliza entre builds. |

No se pasan a QEMU ni al conversor `/dev`, un `PhysicalDrive`, una partición Windows, `/mnt/c` como carpeta compartida del guest, el directorio personal ni credenciales. El único directorio Windows-visible que llega al contenedor conversor es su salida de artefactos declarada; nunca se monta dentro del guest de QEMU.

## Entradas aprobables por digest

La inspección de metadatos y la comprobación aislada del CLI registraron estas referencias seleccionadas, ambas `linux/amd64`:

```text
quay.io/fedora/fedora-bootc@sha256:86cd97f1e7962e30f52f35ae1c0719299df4f681492b133ea4bcdb74d154fb92
ghcr.io/osbuild/image-builder-cli@sha256:700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5
```

`system/Containerfile` y `packaging/phase0-image-manifest.template.yaml` ya contienen esas mismas referencias inmutables, la versión `1` y commit `08ccdf050b4a5b190f0c500122e6c5763e56ccd8` del CLI. Antes de comunicar éxito se creará además un manifiesto específico de `build-id`. Nunca se usará un tag mutable al construir o convertir. El candidato histórico `quay.io/centos-bootc/bootc-image-builder@sha256:afeffdb5a7ab6bb9d0593b5765412c4d821a9492dbaf26bb5a494e27181d2019` queda excluido porque informó `build_tainted: true`.

## Secuencia propuesta

1. **Completado:** auditar y deshabilitar el timer/socket/servicio de paquetes de Podman/QEMU dentro de Ubuntu WSL. No cambió ningún servicio de Windows.
2. **Completado:** crear el store Podman dedicado, descargar mediante TLS las referencias fijadas y registrar sus versiones/digests locales. El CLI unificado ya inspeccionó la base con red deshabilitada.
3. **Completado:** construir el derivado de `system/` con `--pull=never --network=none --http-proxy=false`; no instaló paquetes ni incluyó usuarios, contraseñas o secretos.
4. **Completado:** ejecutar el conversor fijado por digest, con red deshabilitada, `--privileged`, store dedicado, configuración de solo lectura y output por `build-id`. El primer intento se detuvo sin artefacto por una ruta interna de storage; el segundo mount del mismo store validó el manifiesto y la conversión finalizó correctamente.
5. **Completado:** comprobar formato, hash y rutas del `qcow2`; crear un overlay nuevo para el arranque de prueba.
6. **Completado:** arrancar QEMU con KVM, red deshabilitada, OVMF de código de solo lectura y consola serie. Se observó `AUREON_PHASE0_READY` y apagado limpio; se conservaron logs y hashes.

## Comandos de referencia que el runner revisa antes de ejecutar

El runner implementado valida rutas, rechaza artefactos existentes y no interpola entradas no confiables. La ayuda local del CLI fijado confirmó `build <image-type>`, `--bootc-ref`, `--bootc-default-fs`, `--image-size`, `--output-name`, `--with-manifest` y `--with-buildlog`. La conversión usa el patrón siguiente, con valores fijados, `--pull=never` y un límite de disco virtual de 10 GiB:

```bash
podman --root /var/lib/aureon-phase0-podman/storage \
  --runroot /run/aureon-phase0-podman run --rm --privileged --pull=never \
  --network=none \
  -e CONTAINERS_STORAGE_CONF=/etc/containers/storage.conf \
  -v /var/lib/aureon-phase0-podman/config/storage.conf:/etc/containers/storage.conf:ro \
  -v /var/lib/aureon-phase0-podman/config/containers.conf:/etc/containers/containers.conf:ro \
  -v /var/lib/aureon-phase0-podman/storage:/var/lib/aureon-phase0-podman/storage:rw \
  -v /var/lib/aureon-phase0-podman/storage:/var/lib/containers/storage:rw \
  -v /mnt/c/.../aureon-os/images/<build-id>:/output:rw \
  ghcr.io/osbuild/image-builder-cli@sha256:700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5 \
  --output-dir /output build qcow2 \
  --bootc-ref localhost/aureon-phase0@sha256:<derived-oci-digest> \
  --bootc-default-fs ext4 \
  --image-size 10737418240 \
  --output-name aureon-base \
  --with-manifest --with-buildlog --progress verbose
```

El flag `--privileged` es un requisito documentado para la ruta rootful del conversor. Amplía la capacidad del contenedor **dentro de la distribución WSL**; por eso se limita a una imagen fijada, un store dedicado, un output declarado y red deshabilitada. No es una instalación de Aureon ni una operación sobre discos físicos, pero se debe tratar como una operación sensible y no se ejecutará sin confirmación.

La ruta seleccionada es el CLI unificado `ghcr.io/osbuild/image-builder-cli` con `build qcow2 --bootc-ref ... --bootc-default-fs ext4`, que el upstream recomienda para trabajo nuevo. El store dedicado se monta en su ruta absoluta original y se configura mediante `packaging/phase0-container-storage.conf`; `packaging/phase0-containers.conf` fuerza `netns = "none"` en el Podman interno. El mismo store dedicado se monta además en `/var/lib/containers/storage` exclusivamente para el lector `containers-storage` usado durante la generación de manifiesto. Ambos destinos internos señalan al mismo origen dedicado de WSL; no se usa ni se monta el store global de Podman, y no se crea una red bridge.

La documentación upstream describe el CLI unificado como ruta de migración y la conversión de una referencia bootc a `qcow2`; Fedora puede requerir un filesystem raíz explícito. Véanse la [guía oficial de bootc Image Builder](https://osbuild.org/docs/bootc/) y la [nota de deprecación](https://osbuild.org/docs/bootc/deprecation-notice/).

## Ejecución documentada

`phase0-f44-20260718` usó la OCI local `sha256:a1a941807af32f1f9ce57f37189befc69a930cc60e889b1c00961ea966fc0d76` y produjo `images/phase0-f44-20260718/aureon-base.qcow2`. `qemu-img check` no encontró errores. QEMU arrancó con KVM, sin red y con un overlay de 24,182,784 bytes; el serial registró el marcador a los 38.85 segundos de guest y `reboot: Power down` a los 57.33 segundos. Véanse `build/phase0-f44-20260718/` y `work/qemu/phase0-f44-20260718/smoke.json`.

## Criterios de parada

El runner se detiene y conserva evidencia si ocurre cualquiera de estas situaciones:

- un digest o plataforma no coincide con el manifiesto;
- aparece un path fuera del `build-id` o un dispositivo de bloque;
- el conversor requiere red en el primer intento;
- no aparece un único `qcow2` bajo el output declarado, su formato no es qcow2 o su hash no se puede calcular;
- el log serie no contiene el marcador;
- QEMU no se apaga de forma limpia dentro del límite declarado.
