# Aureon OS

Aureon OS es un sistema operativo de escritorio basado en Linux, diseñado para ser rápido, elegante, confiable y recuperable. El proyecto reutiliza componentes maduros de Linux; no pretende reescribir el kernel, controladores ni un compositor desde cero.

> Estado: Fase 0 — una imagen mínima ya arrancó y se apagó en una VM aislada. El runner reproducible `test-smoke` está implementado y cubierto por pruebas unitarias; aún necesita su primera repetición real desde el WSL del propietario antes de declararse reproducible.

## Principios de desarrollo

- Todas las imágenes y discos de prueba viven dentro de este repositorio, en archivos virtuales aislados.
- Ninguna herramienta de este repositorio escribe discos físicos, modifica el bootloader del host ni reinicia Windows.
- Las acciones que necesiten privilegios, red, instalación de dependencias o virtualización se documentan antes de ejecutarse.
- Un resultado solo se marca como funcional cuando hay comando, artefacto y log reproducibles.

## Ruta de Fase 0

La ruta objetivo es:

```text
contenedor bootc derivado -> imagen qcow2 aislada -> QEMU/OVMF -> consola serial
-> smoke test -> logs y apagado limpio
```

El contrato del primer hito es `aureon-dev test-smoke`. Por defecto imprime un plan sin escribir nada. Su modo `--execute` se limita a Linux/WSL con root, referencias fijadas, red deshabilitada, un store Podman dedicado, un disco `qcow2` nuevo y un overlay de VM; no acepta discos físicos ni eleva Windows automáticamente.

## Vista previa de escritorio

También hay una preview interactiva de KDE Plasma que vive exclusivamente en
una VM QEMU: [guía de escritorio](docs/testing/desktop-preview.md). La imagen
mínima de Fase 0 no cambia ni se instala en Windows. La primera creación de la
preview descarga los paquetes Fedora explícitamente listados dentro de Ubuntu
WSL; su VM no tiene red, carpetas compartidas ni discos físicos.

## Fundamentos de las fases maestras

El control local `aureonctl` materializa los contratos de las fases 0–32 sin
convertirse en un instalador oculto. Sus comandos son solo de diagnóstico o de
plan: no instalan paquetes, no cambian cgroups, no inician streaming, no
exportan datos ni aceptan discos como entrada.

```bash
python3 tools/aureonctl validate
python3 tools/aureonctl status
python3 tools/aureonctl baseline
python3 tools/aureonctl resource plan --mode gaming
python3 tools/aureonctl hardware doctor
python3 tools/aureonctl integrity doctor
```

Consulta el [mapa de fases](docs/aureon-phase-map.md) y el
[contrato de autoridad](docs/aureon-user-authority.md). Las fases que requieren
hardware, firmware, particiones o consentimiento por juego permanecen
explícitamente bloqueadas hasta tener evidencia y aprobación del usuario.

## Primeros comandos seguros

El CLI de bootstrap ya está disponible. `doctor` solo inspecciona y puede devolver un código distinto de cero cuando el entorno aún no está listo; eso es el resultado esperado antes de instalar las dependencias. Estos comandos no instalan software ni modifican discos:

```powershell
wsl.exe -d Ubuntu-24.04 -- /usr/bin/python3 /mnt/c/RUTA/DEL/CHECKOUT/tools/aureon-dev doctor
```

Dentro de WSL o CI Linux se usa `python3` (versión 3.10 o superior):

```bash
python3 tools/aureon-dev doctor
python3 -m unittest discover -s tests/unit -p 'test_*.py'
python3 tools/aureon-dev test-smoke --build-id phase0-review --dry-run

# Operación explícita dentro de la VM WSL; crea solo artefactos virtuales nuevos.
sudo python3 tools/aureon-dev test-smoke --build-id phase0-run-01 --execute
```

El último comando no instala Aureon en Windows, no modifica BIOS ni usa discos físicos. Conserva los logs aunque una etapa falle.

Consulta [STATUS.md](STATUS.md), [ROADMAP.md](ROADMAP.md) y [docs/testing/phase-0.md](docs/testing/phase-0.md) antes de intentar un build.

## Estructura

Los directorios del repositorio separan el sistema base, componentes del escritorio, servicios, imágenes, pruebas y documentación. Los directorios vacíos conservan únicamente su estructura inicial; no representan componentes implementados.

## Licencia y contribuciones

La licencia definitiva está pendiente de decisión explícita. No se aceptan recursos propietarios ni claves privadas. Consulta [LICENSES.md](LICENSES.md), [SECURITY.md](SECURITY.md) y [CONTRIBUTING.md](CONTRIBUTING.md).
