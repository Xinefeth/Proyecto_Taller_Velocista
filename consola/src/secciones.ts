// Secciones de la consola, en el mismo orden y con los mismos nombres que el prototipo.
// `pendientes` lista los ítems del Product Backlog v5 que construyen cada pantalla.

export type IdSeccion =
  | "control"
  | "telemetria"
  | "tiempos"
  | "mapa"
  | "catalogo"
  | "armador"
  | "reglamento"
  | "sistema";

export interface Seccion {
  id: IdSeccion;
  titulo: string;
  grupo: "Robot" | "Gestión" | "Sistema";
  pendientes: [string, string][];
}

export const SECCIONES: Seccion[] = [
  {
    id: "control",
    titulo: "Control",
    grupo: "Robot",
    pendientes: [
      ["EN-19", "Migrar el prototipo de la consola a la app"],
      ["HU-13", "Seleccionar el robot"],
      ["HU-14", "Consultar el estado del robot"],
      ["HU-15", "Visualizar la regleta de sensores"],
      ["HU-16", "Calibrar los sensores y arrancar"],
      ["HU-17", "Configurar el controlador"],
      ["HU-18", "Configurar el modo y el color de línea"],
    ],
  },
  {
    id: "telemetria",
    titulo: "Telemetría",
    grupo: "Robot",
    pendientes: [
      ["HU-21", "Visualizar las señales"],
      ["HU-22", "Visualizar la pista en vivo"],
      ["HU-23", "Consultar el registro de eventos"],
    ],
  },
  {
    id: "tiempos",
    titulo: "Corridas y optimización",
    grupo: "Robot",
    pendientes: [
      ["HU-19", "Cronometrar las vueltas"],
      ["HU-20", "Registrar y listar las corridas"],
      ["HU-26", "Consultar el tiempo por corrida y exportarlo"],
      ["HU-27", "Recibir la sugerencia del ingeniero de pista"],
      ["HU-28", "Optimizar el setup con optimización bayesiana"],
      ["HU-29", "Consultar el estudio de optimización"],
    ],
  },
  {
    id: "mapa",
    titulo: "Mapa de pista",
    grupo: "Robot",
    pendientes: [
      ["HU-25", "Consultar la telemetría de la última vuelta"],
      ["HU-30", "Construir el mapa desde la primera vuelta"],
      ["SP-03", "Evaluar el mapa por odometría"],
    ],
  },
  {
    id: "catalogo",
    titulo: "Catálogo de componentes",
    grupo: "Gestión",
    pendientes: [
      ["HU-01", "Listar, buscar y filtrar componentes"],
      ["HU-02", "Registrar un componente manualmente"],
      ["HU-03", "Consultar la ficha de un componente"],
      ["HU-04", "Consultar el inventario del club"],
      ["HU-05", "Registrar un componente desde su enlace"],
    ],
  },
  {
    id: "armador",
    titulo: "Armador de robots",
    grupo: "Gestión",
    pendientes: [
      ["HU-06", "Registrar un robot y sus piezas"],
      ["HU-07", "Consultar el resumen del robot"],
      ["HU-08", "Verificar la compatibilidad de las piezas"],
      ["HU-09", "Comparar versiones del robot"],
    ],
  },
  {
    id: "reglamento",
    titulo: "Perfiles de reglamento",
    grupo: "Gestión",
    pendientes: [
      ["HU-10", "Definir perfiles de reglamento y validar el robot"],
      ["HU-11", "Bloquear en la consola lo que prohíbe el reglamento"],
    ],
  },
  { id: "sistema", titulo: "Estado del sistema", grupo: "Sistema", pendientes: [] },
];
