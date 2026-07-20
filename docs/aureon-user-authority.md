# Autoridad del usuario en Aureon

La regla de Aureon es simple: automatiza solo lo local, reversible y seguro.
El usuario conserva toda decisión que pueda cambiar el sistema, sus datos, su
privacidad o su arranque.

| Nivel | Regla | Ejemplos |
| --- | --- | --- |
| A | Automático, local y reversible | Posponer mantenimiento, restaurar un perfil temporal, recopilar una métrica local. |
| B | Corrección recuperable; se informa después | Volver al despliegue anterior tras un fallo de arranque comprobado. |
| C | Confirmación antes de actuar | Instalar un controlador propietario, reiniciar, activar Integrity competitivo o actualizar firmware. |
| D | Manual y explícito | Formatear, particionar, exportar diagnósticos, cambiar claves de firmware o borrar datos personales. |

## Reglas no negociables

- El modo predeterminado es silencioso: no hay telemetría ni red no solicitada.
- Ningún juego, cámara, micrófono, controlador propietario, anticheat o
  firmware se instala o activa automáticamente.
- Una acción de nivel C explica qué cambia, impacto, reinicio y cómo volver
  atrás antes de que el usuario la apruebe.
- Una acción de nivel D nunca se transforma en automática por una preferencia
  antigua.
- Los diagnósticos permanecen locales hasta que el usuario los revise y los
  exporte manualmente.

El catálogo verificable de estas reglas es
[`packaging/aureon-control-plane.json`](../packaging/aureon-control-plane.json).
`aureonctl authority` lo expone dentro de la preview sin efectuar acciones.

## Modos

- **Stable:** comportamiento conservador y sin política temporal fuera de una
  sesión elegida.
- **Gaming:** pospone trabajo diferible mientras exista una sesión autorizada;
  no modifica voltajes, mitigaciones ni controladores.
- **Streaming:** reserva la planificación de recursos, pero no inicia OBS ni
  accede a cámara, micrófono o claves de una plataforma.
- **Competitive:** reservado para un consentimiento por juego; actualmente no
  está implementado.
- **Development:** permite diagnósticos locales adicionales, nunca privilegios
  automáticos.
