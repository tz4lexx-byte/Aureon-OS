# Seguridad de Aureon OS

## Regla de seguridad para desarrollo

Las herramientas del repositorio solo pueden crear, leer o eliminar artefactos dentro de rutas explícitas de build, imágenes y logs del proyecto. Nunca deben usar un disco físico, una partición del host, el bootloader de Windows ni una ruta de dispositivo como destino predeterminado.

## Alcance inicial

- Imagen base atómica y actualizable.
- SELinux enforcing como objetivo de la imagen, sujeto a validación en build.
- Flatpak, portales XDG, systemd y polkit en fases posteriores.
- No hay credenciales, claves de firma ni telemetría externa en este repositorio.

## Reportar vulnerabilidades

**Aún no se aceptan reportes externos**: el proyecto no tiene remoto, correo o canal privado verificable configurado. No publiques secretos ni exploits funcionales en issues. Antes de abrir contribuciones públicas se establecerá un canal de reporte privado y un plazo de respuesta.

## Material sensible

No se versionan claves privadas, tokens, imágenes de usuarios, volcados con datos privados ni diagnósticos no revisados. Los certificados y firmas públicas pueden versionarse solo con procedencia y revisión explícitas. Antes de exportar logs, elimina identificadores y rutas personales cuando no sean necesarios.
