# Firmware

Dos proyectos PlatformIO independientes. Ambos hablan el contrato de mensajes v1.0 (`docs/contrato/`). Cada uno separa la **lógica pura** (`lib/`, sin Arduino, probada en PC) de la parte que depende del hardware (`src/`).

| Carpeta | Placa | Qué hace |
| --- | --- | --- |
| `velocista/` | ESP32-S3 DevKitC | Robot: control a 1000 Hz en el núcleo 1; Wi-Fi y WebSocket en el núcleo 0 |
| `cronometro/` | ESP32 DevKit | Cronómetro de meta: barrera IR con interrupción y cálculo de cada vuelta |

```
<proyecto>/
├── platformio.ini     entornos: el de la placa y "native" (pruebas en PC)
├── include/           config.example.h → copiar como config.h (no se sube)
├── lib/               lógica pura (linea/ en el robot, vueltas/ en el cronómetro)
├── src/main.cpp       tareas, Wi-Fi, WebSocket e interrupciones
└── test/              pruebas Unity de lib/
```

## Arranque

1. Instala VS Code y la extensión **PlatformIO IDE**.
2. Abre **solo la carpeta del proyecto** (`firmware/velocista` o `firmware/cronometro`).
3. Copia `include/config.example.h` como `include/config.h` y completa Wi-Fi, IP de la laptop servidor y token (el script `scripts/setup` lo crea por ti).
4. Conecta la placa por USB y usa **Upload** y **Monitor** (115 200 baudios).

La primera compilación descarga la plataforma ESP32 (una vez, con internet).

## Comandos

| Qué | Comando (dentro de la carpeta del proyecto) |
| --- | --- |
| Compilar | `pio run` |
| Cargar a la placa | `pio run -t upload` |
| Monitor serial | `pio device monitor` |
| Pruebas en PC | `pio test -e native` |

## Pendiente por ítem

| Ítem | Qué falta |
| --- | --- |
| EN-12 | Listos y probados en PC (`velocista/lib/vueltas_guardadas`): la cola de vueltas sin Wi-Fi, el armado del mensaje `sync` (validado con los modelos de la API) y una simulación de la caída del Wi-Fi (`pio test -e native -v`). Falta conectarlos en `main.cpp`: guardar en `cerrarVuelta` si no hay enlace, enviar `sync` al reconectar y borrar las vueltas cuando llega el ack; y medir que la consola conecta en menos de 5 s |
| EN-09 | Lectura de batería |
| EN-10 | Lectura de la regleta por el multiplexor y controlador |
| EN-13 / EN-15 | Calibrar la barrera y validar la precisión de ± 5 ms |
