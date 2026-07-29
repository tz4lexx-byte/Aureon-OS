# Política de actualizaciones

Las actualizaciones se preparan como despliegues verificables y no modifican
parcialmente un sistema en uso. Descargar sin activar puede ser nivel B cuando
la red fue autorizada; activar requiere el reinicio que el usuario aprueba.

No hay reinicios forzados. Un rollback automático solo es aceptable después de
un fallo de arranque o de gráficos demostrado y debe informarse al usuario.

El sistema instalado ofrece **Actualizar Aureon** en el menú de aplicaciones.
La acción solicita autenticación administrativa, prepara un despliegue bootc
atómico y actualiza las aplicaciones Flatpak del sistema con progreso visible.
Nunca reinicia automáticamente; el usuario decide cuándo activar el nuevo
despliegue desde el menú normal de apagado. Tras actualizar aplicaciones,
elimina únicamente runtimes Flatpak que ninguna aplicación instalada utiliza.

La interfaz también conserva `aureon-update status`, `check`, `apply` y
`rollback` para soporte local. `rollback` requiere confirmación y solo prepara
el despliegue anterior para el próximo arranque.

Para que la parte del sistema reciba versiones posteriores, cada release debe
publicar la imagen Aureon en un registro OCI y construir el instalador con esa
referencia remota estable. Una referencia `localhost/...` sirve para validar
la ISO, pero no constituye un canal remoto de actualización.

El canal estable configurado es
`ghcr.io/tz4lexx-byte/aureon-os:stable`, asociado al repositorio
`https://github.com/tz4lexx-byte/Aureon-OS` y declarado en
`packaging/update-channel.json`. Su visibilidad prevista es pública para que
los equipos instalados puedan descargar actualizaciones sin almacenar una
credencial personal de GitHub.

Las nuevas imágenes se publican mediante el flujo manual
`.github/workflows/publish-aureon-update.yml`. El flujo valida primero las
pruebas y contratos, construye la imagen bootc y solo entonces publica el canal
`stable` o `testing`. No tiene temporizador ni se ejecuta por cada push. La
primera vez, el propietario debe marcar el paquete `aureon-os` como público en
GitHub Packages; después los equipos pueden actualizar sin token personal.
