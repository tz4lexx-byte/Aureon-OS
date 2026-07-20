# Sistema base

Esta carpeta contiene la definición bootc mínima de Fase 0, sus overlays y las unidades que emiten el marcador serial y solicitan apagado dentro de una VM. Usa solo la base Fedora fijada por digest; no incluye usuarios, contraseñas, claves, red ni instrucciones para discos físicos.

La imagen se verificó manualmente una vez y el runner `test-smoke --execute` vuelve a construirla únicamente dentro de un entorno Linux/WSL aprobado. No representa aún un escritorio ni un instalador.
