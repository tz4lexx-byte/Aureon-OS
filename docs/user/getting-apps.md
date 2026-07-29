# Aplicaciones en Aureon OS

Aureon incluye Discover y Flatpak para que las aplicaciones grandes se
actualicen separadas de la imagen inmutable del sistema. El navegador Firefox,
LibreOffice y las utilidades esenciales sí forman parte de la imagen.

`Plasma System Monitor` forma parte del sistema y cumple la función del
Administrador de tareas: muestra procesos, consumo de CPU y memoria, red,
almacenamiento y permite finalizar procesos del usuario.

La edición Gaming incluye `com.valvesoftware.Steam` desde Flathub. Es un
paquete mantenido por la comunidad de Flathub y no está verificado, afiliado ni
soportado oficialmente por Valve. Steam sigue administrando sus propias
actualizaciones, juegos y versiones de Proton.

Aureon instala en el host las reglas `steam-devices` de Valve, fijadas por
commit y verificadas por SHA-256. Estas reglas permiten que Steam Input acceda
a mandos compatibles; las reglas viven en `/usr/lib/udev/rules.d`, fuera del
sandbox Flatpak.

## Activar Flathub

Al usar una instalación con red, abre Konsole y ejecuta una sola vez:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

Después puedes buscar en Discover o instalar directamente:

```bash
flatpak install flathub com.obsproject.Studio
flatpak install flathub com.heroicgameslauncher.hgl
flatpak install flathub org.kde.kdenlive
```

Steam administra Proton desde su propia interfaz. Aureon no activa
automáticamente controladores propietarios, firmware ni ajustes específicos de
un juego: primero debe detectarse el hardware real y pedir consentimiento.

La VM de validación del proyecto arranca deliberadamente sin una tarjeta de
red. Esa restricción protege el entorno de pruebas y no representa la
configuración prevista para una instalación en hardware.
