# Prueba de laptop desde el Live USB

Arranca **Probar Aureon sin instalar**. Esta opción usa el sistema desde el USB
y no inicia el instalador.

Ejecuta **Compatibilidad de laptop** desde el menú o:

```bash
aureon-laptop-check
aureon-laptop-check --json > ~/aureon-laptop.json
```

El reporte inspecciona, sin modificar el equipo:

- Wi-Fi, Bluetooth y bloqueos físicos de radio;
- salidas y entradas PipeWire;
- cámara V4L2 y dispositivos libinput;
- capacidad declarada de suspensión;
- batería y control de brillo;
- GPU PCI y disponibilidad de Vulkan.

Después realiza las pruebas manuales indicadas en el reporte: conexión de
radios, reproducción/grabación de audio, cámara, gestos, suspensión/reanudación,
cierre de tapa, brillo, perfil de energía, un juego corto y una grabación OBS.

## Recursos durante la instalación

El Live no reserva en RAM el tamaño descomprimido del payload. Durante
`bootc install`, los blobs temporales se escriben bajo
`var/tmp/aureon-bootc-install` en el sistema de archivos destino y se eliminan
al terminar. Anaconda conserva en pantalla un pulso de actividad cada cinco
segundos con tiempo transcurrido y espacio usado/disponible. La instalación es
autocontenida y no exige activar Wi-Fi o Ethernet.

## Gráficos

Intel y AMD usan la pila abierta Mesa incluida. NVIDIA puede iniciar con el
controlador abierto y también dispone de la entrada **gráficos básicos** para
diagnóstico. El controlador propietario no se instala automáticamente porque
su módulo y firma deben coincidir con el kernel y con la política de Secure
Boot del equipo.

## Secure Boot

La imagen conserva el kernel y shim firmados de Fedora. La validación de release
debe arrancar el ISO tanto con OVMF UEFI normal como con OVMF Secure Boot. Si el
firmware particular no acepta la cadena, desactiva Secure Boot temporalmente
para la prueba; Aureon nunca cambia esa opción ni enrola claves por sí mismo.
