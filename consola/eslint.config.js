import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: { ecmaVersion: 2022, globals: globals.browser },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // La consola no llama a fetch ni a WebSocket fuera de src/services (DO-02, sección 6).
      "no-restricted-globals": ["error", { name: "fetch", message: "Usa src/services/api.ts" }, { name: "WebSocket", message: "Usa src/services/ws.ts" }],
    },
  },
  {
    files: ["src/services/**/*.ts"],
    rules: { "no-restricted-globals": "off" },
  },
);
