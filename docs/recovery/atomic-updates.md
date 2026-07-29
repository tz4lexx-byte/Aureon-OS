# Actualizaciones y recuperación atómica

El flujo propuesto es: comprobar, descargar, validar, crear un despliegue,
dejar que el usuario elija reiniciar y confirmar o revertir. `aureonctl update
plan` solo muestra este flujo; no consulta red ni modifica una imagen.

Una actualización de controlador necesita además probar módulos, Vulkan 32/64,
gráficos, suspensión y vídeo en el hardware objetivo. Si un despliegue no
inicia o pierde gráficos, un rollback local recuperable puede ser nivel B; el
cambio de canal, un downgrade y el reinicio siguen siendo nivel C.

La implementación instalada expone `aureon-update apply`: autentica al
administrador, ejecuta `bootc upgrade`, actualiza Flatpaks del sistema y deja el
reinicio en manos del usuario. El despliegue previo permanece como recuperación.
`aureon-update rollback` selecciona explícitamente ese despliegue anterior y
tampoco fuerza el reinicio.
