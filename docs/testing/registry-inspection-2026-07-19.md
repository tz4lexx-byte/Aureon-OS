# Inspección remota de entradas bootc — 2026-07-19 UTC

Esta evidencia resolvió entradas inmutables para la puerta de build. No representa una imagen construida ni autoriza por sí misma operaciones futuras; el `FROM` y el manifiesto se activaron después de verificar el CLI unificado en una inspección privilegiada aislada.

## Método

Desde `Ubuntu-24.04` en WSL2 se ejecutaron consultas TLS de solo metadatos:

```text
podman manifest inspect --tls-verify=true quay.io/fedora/fedora-bootc:44
podman manifest inspect --tls-verify=true quay.io/centos-bootc/bootc-image-builder:latest
podman manifest inspect --tls-verify=true ghcr.io/osbuild/image-builder-cli:latest
```

La hora de la inspección fue `2026-07-19T01:29:42Z`. Los tags se usaron solo para resolver una lista de manifiestos; no son referencias aceptables para un build. No se creó una imagen OCI derivada, `qcow2`, VM ni artefacto de Aureon.

## Resultados x86_64

| Entrada | Tag consultado | Plataforma verificada | Digest de manifiesto hijo fijado o excluido |
| --- | --- | --- | --- |
| Base Fedora bootc | `quay.io/fedora/fedora-bootc:44` | `linux/amd64` | `sha256:86cd97f1e7962e30f52f35ae1c0719299df4f681492b133ea4bcdb74d154fb92` |
| CLI unificado `image-builder` (seleccionado) | `ghcr.io/osbuild/image-builder-cli:latest` | `linux/amd64` | `sha256:700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5` |
| Conversor histórico `bootc-image-builder` (excluido) | `quay.io/centos-bootc/bootc-image-builder:latest` | `linux/amd64` | `sha256:afeffdb5a7ab6bb9d0593b5765412c4d821a9492dbaf26bb5a494e27181d2019` |

La base candidata completa sería:

```text
quay.io/fedora/fedora-bootc@sha256:86cd97f1e7962e30f52f35ae1c0719299df4f681492b133ea4bcdb74d154fb92
```

El CLI unificado seleccionado es:

```text
ghcr.io/osbuild/image-builder-cli@sha256:700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5
```

El conversor histórico excluido es:

```text
quay.io/centos-bootc/bootc-image-builder@sha256:afeffdb5a7ab6bb9d0593b5765412c4d821a9492dbaf26bb5a494e27181d2019
```

## Verificación local tras descarga

Las tres referencias se descargaron por digest en el store dedicado `/var/lib/aureon-phase0-podman/storage` de `Ubuntu-24.04` WSL. No se creó una imagen derivada, `qcow2` ni VM.

| Entrada | Digest local | Arquitectura/SO | Versión o revisión reportada | Tamaño local |
| --- | --- | --- | --- | --- |
| Fedora bootc | `sha256:86cd97f1e7962e30f52f35ae1c0719299df4f681492b133ea4bcdb74d154fb92` | `amd64` / `linux` | `44.20260718.0`; `bootc 1.16.3-1.fc44` en metadatos de imagen | 1,980,666,939 bytes |
| CLI unificado `image-builder` (seleccionado) | `sha256:700368cfa3e78b25fb4fe02a87cedf1a5bc0cb142d7287c8c6fff72fd09228f5` | `amd64` / `linux` | versión `1`; commit `08ccdf050b4a5b190f0c500122e6c5763e56ccd8`; `osbuild 188` | aproximadamente 598 MB de capas comprimidas |
| bootc-image-builder | `sha256:afeffdb5a7ab6bb9d0593b5765412c4d821a9492dbaf26bb5a494e27181d2019` | `amd64` / `linux` | etiqueta `42`; revisión `a686afed6dde14fa5444a3d3be0f269acc783470` | 963,691,231 bytes |

La verificación fue `podman image inspect` sobre referencias locales por digest. Además, se ejecutó únicamente `bootc-image-builder --version` en un contenedor efímero, sin red, sin privilegios y de solo lectura. Informó:

```text
build_revision: a686afe
build_time: 2026-06-18T11:23:37Z
build_tainted: true
```

El flag `build_tainted: true` no se interpreta como una vulnerabilidad por sí mismo, pero impide considerar este conversor una entrada limpia para release sin una explicación upstream o una alternativa verificada. Por ello se excluyó del experimento y se seleccionó el CLI unificado `image-builder`.

El CLI unificado se ejecutó además en un contenedor efímero, con red deshabilitada y almacenamiento dedicado, para inspeccionar la base por digest. Informó Fedora 44, SELinux `targeted`, kernel `7.1.3-201.fc44.x86_64`, arquitectura `amd64` y filesystem raíz por defecto vacío. Por ello la conversión de Fase 0 fija `ext4` de manera explícita. Esta comprobación no construyó una OCI derivada ni un disco.

## Pendientes antes de declarar éxito

1. Construir la imagen OCI derivada con `--pull=never` y registrar su digest local.
2. Ejecutar la conversión `qcow2` con el CLI unificado, `--privileged`, red deshabilitada y únicamente los mounts declarados.
3. Guardar manifiesto, buildlog, hash del qcow2 y evidencia del arranque.
4. Usar `--pull=never` durante la construcción y conversión para impedir sustituciones por tags.

El proyecto upstream indica que el contenedor `bootc-image-builder` continúa soportado, aunque está en transición hacia el CLI unificado `image-builder`. Para este experimento se eligió el CLI unificado; esa selección debe revalidarse antes de una ruta release. Véanse la [guía de migración de Image Builder](https://osbuild.org/docs/bootc/) y la [nota de deprecación](https://osbuild.org/docs/bootc/deprecation-notice/).
