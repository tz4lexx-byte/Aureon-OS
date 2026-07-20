# ADR-0002: Toolchain reproducible y aislamiento de pruebas

- Estado: propuesto (decisión provisional de Fase 0)
- Fecha: 2026-07-18
- Decisores: equipo de Aureon OS

## Contexto

El desarrollo puede realizarse desde Windows 11, mientras que la imagen de Aureon OS es un sistema Linux. La herramienta de build y las pruebas deben ser repetibles en un entorno Linux y no pueden modificar el disco, bootloader, drivers ni particiones del host. El primer hito es una VM QEMU aislada con consola serial y smoke test; no es una instalación en hardware físico.

## Decisión

1. Los builds se ejecutarán en un entorno Linux definido (WSL2 o un host Linux de CI) y, cuando sea viable para el componente, dentro de contenedores reproducibles. Windows actúa como host y orquestador; no es el destino del sistema construido.
2. La herramienta de alto nivel es `aureon-dev`. En el bootstrap de Fase 0, `doctor` es una inspección de solo lectura y los demás subcomandos fallan cerrados hasta que existan sus controles de seguridad. Sus implementaciones posteriores deberán ser idempotentes, mostrar las rutas que van a usar y rechazar rutas fuera del espacio de trabajo configurado.
3. Las imágenes de prueba, overlays, snapshots, discos `qcow2`, firmware de VM, logs y capturas se crearán únicamente bajo directorios de build o trabajo del repositorio. Cada ejecución tendrá un identificador de build.
4. QEMU arrancará discos virtuales explícitos. No se aceptarán dispositivos de bloque físicos, rutas como `/dev/sd*` o `/dev/nvme*`, ni discos de Windows como destino predeterminado.
5. La consola serial será un artefacto obligatorio de cada prueba de arranque. Un marcador de readiness del guest y el resultado del smoke test se registrarán por separado para no confundir “el proceso QEMU inició” con “el sistema alcanzó el estado esperado”.
6. Se usarán perfiles separados `dev`, `test`, `beta` y `release`. Los depuradores y opciones de diagnóstico solo podrán estar en perfiles que los declaren; los artefactos de release no heredan esos extras por accidente.
7. Las credenciales, claves privadas y tokens no se almacenarán en el repositorio ni en imágenes de prueba. Los artefactos publicables deberán registrar procedencia, hash y, cuando corresponda, SBOM y firma fuera del flujo local de desarrollo.

## Invariantes de seguridad

| Invariante | Aplicación esperada |
| --- | --- |
| El host no es un objetivo de instalación. | No se reparticiona, formatea, monta automáticamente ni cambia su bootloader. |
| Todo almacenamiento de pruebas es virtual y localizado. | Se validan rutas antes de crear, convertir o eliminar archivos de VM. |
| Las operaciones privilegiadas son excepcionales. | Se documentan el motivo, el alcance y el comando exacto; se evita privilegiar contenedores sin necesidad. |
| Una prueba debe poder inspeccionarse. | Se conservan manifiesto, logs seriales, salida de smoke y metadatos de la imagen, especialmente ante fallo. |
| La red no es implícita. | Las pruebas sin necesidad de red se ejecutan sin red; cualquier forwarding o descarga se declara en la configuración de la prueba. |
| El resultado es atribuible. | Build ID, commit o fuente, versiones de herramientas, hash de imagen y acelerador se registran juntos. |

## Alternativas descartadas por ahora

- **Build directo y mutable en el host Windows:** no reproduce de forma natural el entorno Linux objetivo y aumenta la superficie de cambios del host.
- **Usar un disco físico para acelerar las pruebas:** viola el aislamiento requerido y no aporta una ventaja aceptable en Fase 0.
- **Crear una VM manual y conservar su estado como fuente de verdad:** impide demostrar que una imagen procede de un checkout limpio.
- **Instalar todas las herramientas de depuración en la imagen base:** aumenta superficie, tamaño y ambigüedad entre perfiles. Se usarán imágenes o contenedores de desarrollo separados cuando hagan falta.

## Consecuencias

- El primer pipeline puede ser más lento que una instalación manual, pero sus fallos dejan evidencia y no dependen del estado personal del desarrollador.
- La virtualización disponible varía por host. `aureon-dev doctor` deberá detectar y reportar si se usa WHPX, KVM o TCG; no asumirá que alguno está instalado o habilitado.
- Los scripts de limpieza requerirán la misma validación de rutas que los de creación. Una limpieza no puede derivar en borrado fuera del árbol de artefactos.
- La verificación inicial cubre consola y servicios mínimos. La aceleración gráfica, el login y las pruebas UI se añadirán en fases posteriores.

## Criterios de aceptación de la decisión

Antes de marcar Fase 0 como completada, el repositorio debe demostrar al menos una ejecución desde un checkout limpio que produzca una imagen aislada, arranque QEMU, capture logs seriales, confirme el target de systemd pactado, ejecute un smoke test y apague la VM limpiamente. La salida debe declarar explícitamente qué acelerador se utilizó y qué rutas de artefactos se tocaron.

No se afirmará que el toolchain está listo hasta contar con esa evidencia. Si la implementación requiere una excepción a cualquiera de las invariantes, se debe detener el flujo y crear o actualizar una ADR antes de continuar.
