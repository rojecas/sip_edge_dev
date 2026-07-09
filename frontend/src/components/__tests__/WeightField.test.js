/**
 * Tests para WeightField.svelte — Campo de peso con botones Tara/Leer/Reset.
 * Cubre: R1 (botón Reset se renderiza), R2 (solo ese campo se limpia).
 * CORREGIDO (T38): Botones Tara/Leer usan api.post en lugar de scaleStore.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import WeightField from "../WeightField.svelte";

// Mock del api para que el componente no intente fetch real
vi.mock("../../lib/api.js", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn().mockResolvedValue({ result: "ok" }),
    put: vi.fn(),
    del: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  },
  buildQuery: vi.fn(() => ""),
}));

vi.mock("../../lib/constants.js", () => ({
  ENDPOINTS: {
    SCALE_COMMAND: "/api/scale/command",
  },
  CONFIG: {},
  ROLES: {},
  LS_KEYS: {},
  HARVEST_TYPES: [],
}));

// Mock del scaleStore para evitar dependencia de WebSocket
vi.mock("../../lib/ws.js", () => ({
  scaleStore: {
    connected: false,
    net_weight: 0,
    is_stable: false,
    unit: "kg",
  },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("WeightField", () => {
  describe("boton Reset (Feature 24)", () => {
    it("muestra boton Reset cuando onReset es proporcionado", () => {
      const onReset = vi.fn();
      render(WeightField, {
        props: {
          fieldName: "Peso Muestra",
          value: 1.250,
          onReset,
        },
      });
      expect(screen.getByRole("button", { name: /Reset/i })).toBeInTheDocument();
    });

    it("no muestra boton Reset cuando onReset es null", () => {
      render(WeightField, {
        props: {
          fieldName: "Peso Muestra",
          value: 1.250,
        },
      });
      expect(screen.queryByRole("button", { name: /Reset/i })).toBeNull();
    });

    it("llama a onReset al hacer clic en el boton Reset", async () => {
      const onReset = vi.fn();
      render(WeightField, {
        props: {
          fieldName: "Peso Muestra",
          value: 1.250,
          onReset,
        },
      });
      const resetBtn = screen.getByRole("button", { name: /Reset/i });
      await fireEvent.click(resetBtn);
      expect(onReset).toHaveBeenCalledTimes(1);
    });
  });
});
