// REST uses descriptive English fields; existing screens keep their domain models.
import type { Componente, RobotDef, Version, Specs } from "../types/dominio";
import type {
  ComponenteCrearDTO,
  ComponenteSalidaDTO,
  RobotSalidaDTO,
  VersionSalidaDTO,
} from "../types/rest";

const specKeys: Record<string, string> = {
  logic: "logica",
  terminals: "bornes",
  commercial: "comercial",
  channels: "canales",
  output: "salida",
  pitch: "paso",
  type: "tipo",
  family: "familia",
  cells: "celdas",
  width: "ancho",
  length: "largo",
  axes: "ejes",
};

function renameSpecs(specs: Specs, keys: Record<string, string>): Specs {
  return Object.fromEntries(Object.entries(specs).map(([key, value]) => [keys[key] ?? key, value]));
}

export function componenteDesdeApi(dto: ComponenteSalidaDTO): Componente {
  return {
    id: dto.id,
    t: dto.type_id,
    nm: dto.name,
    precio: dto.price,
    masa: dto.mass_g,
    tienda: dto.store,
    stock: dto.stock,
    i: dto.current_a ?? undefined,
    s: renameSpecs(dto.specifications, specKeys),
  };
}

export function componenteParaApi(
  component: Omit<Componente, "id" | "t"> & { t: ComponenteCrearDTO["type_id"] },
): ComponenteCrearDTO {
  return {
    type_id: component.t,
    name: component.nm,
    price: component.precio,
    mass_g: component.masa,
    store: component.tienda,
    stock: component.stock,
    current_a: component.i ?? null,
    specifications: renameSpecs(
      component.s,
      Object.fromEntries(Object.entries(specKeys).map(([a, b]) => [b, a])),
    ),
  };
}

// Keep the immutable snapshots alongside the legacy fields for historical views.
export function versionDesdeApi(dto: VersionSalidaDTO): Version & { api: VersionSalidaDTO } {
  return {
    v: dto.label,
    fecha: dto.date,
    nota: dto.note,
    estado: dto.status,
    parts: Object.fromEntries(
      Object.entries(dto.parts).map(([slot, piece]) => [
        slot,
        { id: piece.component_id, q: piece.quantity },
      ]),
    ),
    api: dto,
  };
}

export function robotDesdeApi(
  dto: RobotSalidaDTO,
  versions: VersionSalidaDTO[],
): RobotDef & { api: RobotSalidaDTO } {
  return {
    id: dto.id,
    nm: dto.name,
    short: dto.short_code,
    tipo: dto.type,
    fw: dto.firmware,
    ver: versions.map(versionDesdeApi),
    api: dto,
  };
}
