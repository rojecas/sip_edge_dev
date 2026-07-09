/**
 * Tests para AdminConfig.svelte — Configuracion del Sistema
 * Cubre: R1, R2, R3, R4, R5, R6, R11
 */
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/svelte";
import AdminConfig from "../AdminConfig.svelte";
import { api } from "../../lib/api.js";

// ── Mock api.js — factory must be self-contained ────────────────
vi.mock("../../lib/api.js", () => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn() },
  ApiError: class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  },
}));

// ── Fixtures ────────────────────────────────────────────────────
const mockConfig = {
  rs485: { path: "/dev/rs485", baudrate: 115200, parity: "N", data_bits: 8, stop_bits: 1.0 },
  rs232: { path: "/dev/rs232", baudrate: 9600, parity: "E", data_bits: 7, stop_bits: 2.0 },
  gsm: { modem_index: 0 },
  session_timeout_minutes: 30,
  scale_timeout_seconds: 5,
};

const mockConfigMinimal = {
  rs485: { path: "", baudrate: 9600, parity: "N", data_bits: 8, stop_bits: 1.0 },
  rs232: { path: "", baudrate: 9600, parity: "N", data_bits: 8, stop_bits: 1.0 },
  gsm: { modem_index: 0 },
};

// ── Cleanup ─────────────────────────────────────────────────────
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// ── Helpers ─────────────────────────────────────────────────────
async function waitForLoaded() {
  await waitFor(
    () => {
      expect(screen.getByRole("heading", { name: "Timeouts" })).toBeInTheDocument();
    },
    { timeout: 5000 }
  );
}

// ── Tests ───────────────────────────────────────────────────────
describe("AdminConfig", () => {
  // ─── T14.1: carga config al montar ────────────────────────────
  describe("carga de configuracion (R2, R6)", () => {
    it("llama GET /api/config al montar", async () => {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
      expect(api.get).toHaveBeenCalledWith("/api/config");
    });

    it("pre-popula campo RS485 path con valor del backend", async () => {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
      const input = screen.getByPlaceholderText("/dev/ttyACM0");
      expect(input).toHaveValue("/dev/rs485");
    });

    it("pre-popula campo RS232 path con valor del backend", async () => {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
      const input = screen.getByPlaceholderText("/dev/ttyACM1");
      expect(input).toHaveValue("/dev/rs232");
    });

    it("pre-popula session timeout desde la respuesta", async () => {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
      const section = screen.getByRole("heading", { name: "Timeouts" }).closest("section");
      const inputs = section.querySelectorAll("input[type='number']");
      expect(inputs[0]).toHaveValue(30);
    });

    it("pre-popula scale timeout desde la respuesta", async () => {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
      const section = screen.getByRole("heading", { name: "Timeouts" }).closest("section");
      const inputs = section.querySelectorAll("input[type='number']");
      expect(inputs[1]).toHaveValue(5);
    });
  });

  // ─── T14.2: loading indicator ─────────────────────────────────
  describe("indicador de carga (R2)", () => {
    it("muestra 'Cargando configuración...' mientras loading=true", () => {
      api.get.mockReturnValue(new Promise(() => {}));
      render(AdminConfig);
      expect(screen.getByText("Cargando configuración...")).toBeInTheDocument();
    });
  });

  // ─── T14.3: error de carga ────────────────────────────────────
  describe("error de carga (R2)", () => {
    it("muestra mensaje de error si GET /api/config falla", async () => {
      api.get.mockRejectedValue(new Error("Error de conexión al cargar"));
      render(AdminConfig);
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión al cargar/i)).toBeInTheDocument();
      });
    });

    it("muestra boton Reintentar cuando falla la carga", async () => {
      api.get.mockRejectedValue(new Error("timeout"));
      render(AdminConfig);
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
      });
    });
  });

  // ─── T14.4: guardar config ────────────────────────────────────
  describe("guardar configuracion (R3)", () => {
    async function setupAndSave() {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
    }

    it("envia PUT /api/config al pulsar Guardar Configuración", async () => {
      api.put.mockResolvedValue({});
      await setupAndSave();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      expect(api.put).toHaveBeenCalledWith("/api/config", expect.objectContaining({
        rs485: expect.any(Object),
        rs232: expect.any(Object),
        gsm: expect.any(Object),
      }));
    });

    it("muestra mensaje de exito tras guardado exitoso", async () => {
      api.put.mockResolvedValue({});
      await setupAndSave();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      await waitFor(() => {
        expect(screen.getByText("Configuración guardada exitosamente.")).toBeInTheDocument();
      });
    });

    it("muestra error si PUT /api/config falla con ApiError", async () => {
      const { ApiError } = await import("../../lib/api.js");
      // Set put mock BEFORE component renders
      api.put.mockRejectedValue(new ApiError("Datos inválidos", 422));
      await setupAndSave();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      await waitFor(() => {
        expect(screen.getByText("Datos inválidos")).toBeInTheDocument();
      });
    });
  });

  // ─── T14.5: test de puerto ────────────────────────────────────
  describe("test de puerto (R4)", () => {
    async function setupForTest() {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
    }

    it("llama POST /api/config/test/rs485 al pulsar Test RS485", async () => {
      api.post.mockResolvedValue({ status: "ok" });
      await setupForTest();
      screen.getByRole("button", { name: "Test RS485" }).click();
      expect(api.post).toHaveBeenCalledWith("/api/config/test/rs485");
    });

    it("muestra 'Prueba exitosa' tras test ok", async () => {
      api.post.mockResolvedValue({ status: "ok" });
      await setupForTest();
      screen.getByRole("button", { name: "Test RS485" }).click();
      await waitFor(() => {
        expect(screen.getByText("Prueba exitosa")).toBeInTheDocument();
      });
    });

    it("muestra mensaje de error si test devuelve status fail", async () => {
      api.post.mockResolvedValue({ status: "fail", detail: "Port not found" });
      await setupForTest();
      screen.getByRole("button", { name: "Test RS485" }).click();
      await waitFor(() => {
        expect(screen.getByText("Port not found")).toBeInTheDocument();
      });
    });

    it("deshabilita el boton mientras prueba en curso", async () => {
      api.post.mockReturnValue(new Promise(() => {}));
      await setupForTest();
      screen.getByRole("button", { name: "Test RS485" }).click();
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Probando..." })).toBeDisabled();
      });
    });
  });

  // ─── T14.7: session timeout ────────────────────────────────────
  describe("session timeout (R5)", () => {
    async function setupTimeouts() {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
    }

    it("envia PUT /api/setup/session al guardar", async () => {
      api.put.mockResolvedValue({});
      await setupTimeouts();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      expect(api.put).toHaveBeenCalledWith("/api/setup/session", {
        session_timeout_minutes: 30,
      });
    });

    it("muestra mensaje de exito", async () => {
      api.put.mockResolvedValue({});
      await setupTimeouts();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      await waitFor(() => {
        expect(screen.getByText(/Configuración guardada/i)).toBeInTheDocument();
      });
    });
  });

  // ─── T14.8: scale timeout ──────────────────────────────────────
  describe("scale timeout (R5)", () => {
    async function setupTimeouts() {
      api.get.mockResolvedValue(mockConfig);
      render(AdminConfig);
      await waitForLoaded();
    }

    it("envia PUT /api/setup/scale al guardar", async () => {
      api.put.mockResolvedValue({});
      await setupTimeouts();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      expect(api.put).toHaveBeenCalledWith("/api/setup/scale", {
        timeout_seconds: 5,
      });
    });

    it("muestra mensaje de exito", async () => {
      api.put.mockResolvedValue({});
      await setupTimeouts();
      screen.getByRole("button", { name: "Guardar Configuración" }).click();
      await waitFor(() => {
        expect(screen.getByText(/Configuración guardada/i)).toBeInTheDocument();
      });
    });
  });

  // ─── R11: selects con valores predefinidos ────────────────────
  describe("selects con valores predefinidos (R11)", () => {
    it("tiene selects para configuracion de puertos (no texto libre)", async () => {
      api.get.mockResolvedValue(mockConfigMinimal);
      render(AdminConfig);
      await waitForLoaded();
      const selects = document.querySelectorAll("select");
      expect(selects.length).toBeGreaterThanOrEqual(8);
    });

    it("select de baudrate tiene 10 opciones predefinidas", async () => {
      api.get.mockResolvedValue(mockConfigMinimal);
      render(AdminConfig);
      await waitForLoaded();
      const selects = document.querySelectorAll("select");
      const baudSelect = selects[0];
      expect(baudSelect.options.length).toBe(10);
      expect(baudSelect.options[0].textContent).toBe("300");
      expect(baudSelect.options[9].textContent).toBe("115200");
    });
  });
});
