# Registro de verificación — 18–19 de julio de 2026

## Alcance

Esta evidencia cubre el bootstrap seguro de Fase 0, los comandos de planificación `aureon-dev` y la primera ejecución manual controlada. No se usó un disco físico, un `PhysicalDrive`, una partición, bootloader ni firmware del host como destino de Aureon.

La preparación posterior del entorno está separada del comportamiento de los planes del CLI: `Ubuntu-24.04` se configuró como WSL2 y dispone de Podman, QEMU, `qemu-img` y OVMF dentro de su disco virtual. La ejecución documentada sí demuestra un arranque de Aureon en una VM aislada, pero no sustituye un runner reproducible.

## Resultados aprobados

| Comprobación | Resultado |
| --- | --- |
| Pruebas unitarias del CLI y receta | 38 pruebas aprobadas con Python 3.12; 1 omitida por privilegio de symlink de Windows. |
| `aureon-dev build --dry-run` | Sale con `0`, emite un manifiesto JSON determinista y no crea el directorio de build planeado. |
| `aureon-dev image --dry-run` | Sale con `0`, valida un destino `.qcow2` local y no crea el directorio de imagen planeado. |
| Entradas inseguras | Rutas externas, IDs inválidos, discos físicos y extensiones que no sean `.qcow2` se rechazan antes de usar herramientas externas. |
| `build --execute` e `image --execute` | Salen con `2` y fallan cerradamente sin builder, WSL, red, archivos, imágenes ni discos. |
| `test-smoke --dry-run` | Emite un plan determinista con límites de red, almacenamiento y QEMU sin crear artefactos. |
| `test-smoke --execute` | Implementado y cubierto por pruebas unitarias; la primera ejecución real mediante el runner aún no se realizó en esta evidencia. |
| Enlaces Markdown locales | Aprobados para la documentación actualizada. |
| Formato Markdown | No se detectaron espacios finales en los archivos `.md`. |

## Ejecución manual controlada — `phase0-f44-20260718`

| Comprobación | Resultado |
| --- | --- |
| OCI derivada | Construida con `--pull=never --network=none --http-proxy=false`; digest local `sha256:a1a941807af32f1f9ce57f37189befc69a930cc60e889b1c00961ea966fc0d76`. |
| Conversión | `image-builder` unificado, red deshabilitada y store dedicado; `aureon-base.qcow2` válido, SHA-256 `9fe48914e1f461d1c77fc54a6900625f65cbb95189a18e4332f6c18f17f04ac4`. |
| Integridad de disco | `qemu-img check` aprobó tanto la base como el overlay. |
| Arranque | QEMU 8.2.2 con OVMF, 2 vCPU, 4096 MiB, KVM y `-nic none`; el log confirma `kvm: exiting hardware virtualization`. |
| Readiness | El serial contiene `AUREON_PHASE0_READY` a los 38.85 s de guest. |
| Apagado | El serial contiene `systemd-shutdown: Powering off.` y `reboot: Power down`; QEMU salió con `0` antes del timeout. |
| Aislamiento de disco | El hash de `aureon-base.qcow2` fue idéntico antes y después; QEMU escribió solo `smoke-overlay.qcow2`. |

La evidencia estructurada es `build/phase0-f44-20260718/derived-oci.json`, `build/phase0-f44-20260718/qcow2.json`, `work/qemu/phase0-f44-20260718/smoke.json` y el serial completo. Durante el apagado se observaron AVC de SELinux de `mdadm`; no impidieron el cierre limpio, pero se conservan como observación abierta antes de release.

## Comandos de prueba ejecutados

En esta sesión se usó el runtime Python aislado de Codex para evitar depender del launcher del host:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& '<runtime-python>' -m unittest discover -s tests/unit -p 'test_*.py' -v
& '<runtime-python>' tools/aureon-dev build --build-id documentation-review --dry-run
& '<runtime-python>' tools/aureon-dev image --build-id documentation-review --dry-run
& '<runtime-python>' tools/aureon-dev test-smoke --build-id documentation-review --dry-run
```

Antes y después de los tres comandos de *dry-run* se comprobó que no existían `build/documentation-review`, `images/documentation-review` ni `work/qemu/documentation-review`; seguían ausentes al terminar. Las pruebas unitarias comprueban que `build --execute` e `image --execute` permanecen cerrados y que `test-smoke --dry-run` no crea artefactos.

## Estado del entorno que no valida un build

- Podman, QEMU, `qemu-img` y OVMF están instalados dentro de `Ubuntu-24.04` WSL2, no como binarios o firmware de Windows.
- `/dev/kvm` estuvo disponible para la ejecución documentada; esa disponibilidad y tiempo no constituyen un benchmark ni una garantía para futuras sesiones WSL.
- La receta Fedora bootc usa una base `linux/amd64` fijada por digest y el CLI unificado Image Builder, también fijado. La autorización para crear artefactos sigue siendo explícita por operación; la OCI, el `qcow2` y el smoke existentes son evidencia manual. El runner está implementado, pero todavía requiere una ejecución real nueva.
- La instalación de paquetes creó enlaces systemd de Podman y `qemu-kvm` dentro del guest. Se auditó el estado y se detuvieron/deshabilitaron `podman-auto-update.timer`, `podman.socket` y `qemu-kvm.service`; no hay cambios a servicios de Windows.

Por tanto, esta evidencia valida el bootstrap seguro, los planes del CLI, pruebas unitarias del runner y una ejecución manual completa de bootc → `qcow2` → QEMU → systemd → apagado. Aún no valida una repetición real del runner, instalación física, hardware real, escritorio ni rendimiento.
