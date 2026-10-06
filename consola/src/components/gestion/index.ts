// Componentes comunes de las pantallas de gestión (EN-06). Usan las clases de styles/prototipo.css.
export { Pestanas } from "./Pestanas";
export type { Pestana } from "./Pestanas";
export { Buscador } from "./Buscador";
export { ChipsFiltro } from "./ChipsFiltro";
export type { OpcionChip } from "./ChipsFiltro";
export { TablaDatos } from "./TablaDatos";
export type { Columna } from "./TablaDatos";
export { CampoEntrada, CampoSelector } from "./Campo";
export { FormularioDinamico } from "./FormularioDinamico";
export { useFiltroLista, normalizar } from "./useFiltroLista";
export { validarCampos, parsearNumero } from "./validacion";
export type { DefCampo, Errores, Valores, OpcionCampo, TipoCampo } from "./validacion";
