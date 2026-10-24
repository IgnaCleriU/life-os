// Carga una librería `.pragma library` de QML en un contexto vm de node.
//
// Las libs del tablero son JavaScript plano sin imports de Qt: la única
// sintaxis propia de QML es la línea `.pragma library`, que se quita antes
// de evaluar. Lo que la lib declara a nivel superior queda en el contexto.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const LIB_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "omarchy-plugin", "lib");

export function loadLib(name) {
  const source = readFileSync(join(LIB_DIR, name), "utf8").replace(/^\.pragma library\s*$/m, "");
  const context = vm.createContext({});
  vm.runInContext(source, context, { filename: name });
  return context;
}

// Los valores creados dentro del contexto vm son de otro "realm": un array de
// ahí no es deepStrictEqual a uno de acá aunque tenga lo mismo. Para
// comparar, se copian a valores planos.
export const plain = (value) => JSON.parse(JSON.stringify(value));
