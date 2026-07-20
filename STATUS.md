# Estado verificado

## Fase actual

**Fase 0 — primera OCI, `qcow2` y smoke de VM completados con éxito; el runner acotado y sus pruebas unitarias están implementados, pero su primera ejecución real y la repetición desde checkout limpio siguen pendientes.**

La base de control de las fases maestras 0–32 también está implementada en
fuente: autoridad A–D, diagnósticos locales, planes reversibles de recursos,
política de controladores/datos y puertas de actualización, integridad e
instalador. Esto no declara concluidas las fases de hardware, firmware,
instalación o compatibilidad: permanecen bloqueadas hasta ser validadas en un
equipo real y con la confirmación correspondiente.

## Hechos confirmados

- El repositorio Git local, la estructura inicial y los ADRs de Fase 0 están creados.
- `Ubuntu-24.04` está inicializado como distribución WSL2 utilizable. La preparación ocurre dentro de su disco virtual; no se ha instalado Aureon OS ni se han particionado discos físicos.
- Dentro de esa distribución están disponibles Podman, `qemu-system-x86_64`, `qemu-img` y OVMF. Se construyó una OCI derivada, se convirtió a `qcow2` y se arrancó con QEMU/OVMF dentro de WSL.
- `/dev/kvm` estuvo disponible para la ejecución documentada y QEMU usó KVM; el log serial registra `kvm: exiting hardware virtualization`. Esta única duración no es un benchmark.
- `aureon-dev build` e `aureon-dev image` ya existen como comandos de planificación: por defecto imprimen un manifiesto JSON determinista de *dry-run* y no crean archivos, invocan WSL, usan red ni llaman a Podman/QEMU. `--execute` falla cerradamente hasta que exista una implementación verificada.
- `aureon-dev test-smoke` ya tiene un plan determinista sin escritura y un modo `--execute` deliberadamente estrecho. Este último exige root dentro de Linux/WSL, un `build-id` nuevo, imágenes locales por digest, red deshabilitada, el store dedicado y rutas de artefactos exclusivamente virtuales; aún no se ha ejecutado en vivo desde este runner.
- La receta bootc se ejecutó una vez de forma manual, explícitamente aprobada y acotada. La OCI derivada quedó fijada en `sha256:a1a941807af32f1f9ce57f37189befc69a930cc60e889b1c00961ea966fc0d76`; el conversor unificado produjo un `qcow2` válido y sin red.
- El `qcow2` validado está en `images/phase0-f44-20260718/aureon-base.qcow2`; QEMU lo abrió mediante un overlay separado, observó `AUREON_PHASE0_READY` y el guest se apagó limpiamente. La evidencia estructurada está bajo `build/phase0-f44-20260718/` y `work/qemu/phase0-f44-20260718/`.
- La preview de escritorio KDE está definida por separado en `system/desktop/` y se abre mediante `tools/aureon-desktop-preview`. Las conversiones `preview-08` y `preview-09` llegaron al target gráfico dentro de QEMU; sigue siendo una VM de desarrollo desechable, no una instalación ni una validación de hardware real.
- Se conservaron conversiones validadas `desktop-preview-08` y
  `desktop-preview-09`. `tools/aureon-desktop-preview --run-existing` permite
  abrir una de ellas mediante un overlay nuevo, sin recompilar ni dar red a la
  VM.
- `tools/aureonctl` valida contratos fuente y expone los diagnósticos y planes
  locales de las fases maestras sin efectuar acciones privilegiadas ni envíos.
- No se ha usado ningún disco físico, `PhysicalDrive`, partición, bootloader ni firmware del host como destino de Aureon.

## Auditoría del entorno (18 de julio de 2026)

| Área | Estado observado | Implicación |
| --- | --- | --- |
| Git y Python | Git disponible en Windows; Python 3.12 disponible en Ubuntu WSL2. | El tooling y las pruebas pueden ejecutarse sin instalar Aureon en el host. |
| WSL2 | `Ubuntu-24.04` está configurado y puede abrir una sesión Linux. | Hay un builder Linux virtual separado del sistema Windows. |
| OCI | Podman `4.9.3` está disponible dentro de Ubuntu WSL2; se verificaron modos rootless y rootful. La base Fedora y el CLI unificado quedaron presentes por digest en un store dedicado. | Se construyó una OCI derivada `linux/amd64` en ese store, con digest y hashes registrados. |
| QEMU y firmware | QEMU `8.2.2`, `qemu-img` y OVMF están disponibles dentro de Ubuntu WSL2. | Se convirtió y arrancó el `qcow2` con OVMF de código de solo lectura y variables copiadas por build ID. |
| Aceleración | `/dev/kvm` se encontró disponible y QEMU arrancó la VM con KVM. | La evidencia es funcional; una sola ejecución no acredita rendimiento ni estabilidad sostenida. |
| Preflight | `aureon-dev doctor` es de solo lectura y, en Windows, consulta explícitamente `Ubuntu-24.04` para revisar arquitectura, Python, Podman, QEMU, `qemu-img`, OVMF y KVM opcional. | La lógica está probada de forma unitaria; debe validarse desde la sesión Windows propietaria de WSL antes de declararla preflight completo del builder. |
| Unidades del guest | `podman-auto-update.timer`, `podman.socket` y `qemu-kvm.service` se auditaron y quedaron detenidos/deshabilitados dentro de Ubuntu WSL. | No afecta servicios de Windows; el CLI de Podman sigue disponible para una ejecución manual y aprobada. |

Consulta [docs/development/environment.md](docs/development/environment.md) para los límites operativos y comandos de diagnóstico seguros.

## Estado de la ejecución controlada

La primera ejecución manual completó el `FROM` inmutable, la build OCI, la conversión, el arranque y el apagado. Conservó los controles de red, mounts y almacenamiento virtual. Aún no satisface por sí sola el criterio de salida de una automatización reproducible:

1. Ejecutar y revisar la primera evidencia del runner `aureon-dev test-smoke --execute`; `build --execute` e `image --execute` permanecen cerrados para evitar un atajo parcial inseguro.
2. Repetir desde un checkout limpio y comparar los digests, hashes y logs por build ID.
3. Completar un preflight que vea la cadena real del guest cuando se invoque desde Windows.
4. Mantener excluido el conversor histórico `bootc-image-builder` mientras su señal `build_tainted: true` no tenga una explicación apta para release.
5. Revisar los AVC de SELinux de `mdadm` observados al final del apagado del guest antes de un perfil release.

## Próxima evidencia requerida

1. Primera ejecución real del runner con rutas/argumentos validados y evidencia por build ID.
2. Segunda ejecución independiente, idealmente desde checkout limpio, que confirme el comportamiento de build y smoke.
3. Revisión de los AVC de cierre y definición de la política de aceleración/benchmark.

La imagen documentada sí arrancó en una VM aislada, pero no debe presentarse como release, instalador ni resultado reproducible automatizado. La evidencia del bootstrap y la ejecución está en [docs/testing/verification-2026-07-18.md](docs/testing/verification-2026-07-18.md), `build/phase0-f44-20260718/` y `work/qemu/phase0-f44-20260718/`.
