# Contrato de seguridad del instalador

La primera imagen USB ofrece dos caminos separados:

- **Probar Aureon sin instalar** inicia el escritorio y
  `aureon-laptop-check` sin escribir en discos internos.
- **Instalar Aureon (modo texto)** abre Anaconda y exige que el usuario elija
  almacenamiento, particiones, usuario y cargador.

El kickstart de Aureon no contiene `clearpart`, `autopart`, `ignoredisk`,
`zerombr` ni un disco objetivo. La herramienta de construcción tampoco acepta
una unidad física como argumento. No reduce particiones, formatea, cambia el
orden de arranque ni enrola claves de firmware automáticamente.

Para usar Aureon como segundo sistema se debe liberar espacio desde Windows
antes de arrancar el USB y seleccionar únicamente ese espacio libre dentro del
instalador. Una copia de seguridad sigue siendo obligatoria: ningún instalador
puede eliminar el riesgo de seleccionar manualmente el volumen equivocado.

`aureonctl installer plan` permanece como diagnóstico `manual-only`; no actúa
como instalador oculto.

La imagen instaladora mantiene su espacio temporal pesado fuera del root Live
respaldado por RAM. Cuando Anaconda ejecuta `bootc install to-filesystem`, el
envoltorio exclusivo del ISO usa `var/tmp/aureon-bootc-install` dentro del
sistema de archivos destino y publica actividad cada cinco segundos. Esto evita
dimensionar el Live para el tamaño descomprimido del payload y no cambia el
contenido ni el tamaño final del sistema instalado.

La red es opcional porque el payload ya está incluido en el ISO. El usuario
descartable de **Probar Aureon** puede gestionar NetworkManager para las pruebas
de compatibilidad, pero esa autorización no forma parte del payload instalado.
Asimismo, `bootloader-update.service` se omite únicamente cuando existe el
marcador `/run/initramfs/live`; en un sistema instalado conserva su conducta
normal.
