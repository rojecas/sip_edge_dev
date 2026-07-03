/**
 * Tests para KioskForm.svelte — Formulario de pesaje.
 * Cubre: R3 (reset general relegado a accion secundaria).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/svelte";
import KioskForm from "../KioskForm.svelte";

vi.mock("../../lib/api.js", () => ({
  api: {
    get: vi.fn().mockResolvedValue({
      items: [
        { id: 1, codigo: "H001", nombre: "Hacienda Uno" },
        { id: 2, codigo: "H002", nombre: "Hacienda Dos" },
      ],
      total: 2,
      page: 1,
      page_size: 100,
      total_pages: 1,
    }),
    post: vi.fn().mockResolvedValue({ mensaje: "ok" }),
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
  buildQuery: vi.fn((params) => {
    const parts = [];
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
      }
    }
    return parts.length ? `?${parts.join("&")}` : "";
  }),
}));

vi.mock("../../stores/auth.js", () => ({
  authStore: {
    subscribe: vi.fn(),
    get token() { return "fake-token"; },
    get role() { return "operator"; },
    get username() { return "oper1"; },
    get isAuthenticated() { return true; },
    get isOperator() { return true; },
    get isAdmin() { return false; },
    get jwtPayload() { return { sub: "oper1", role: "operator" }; },
    login: vi.fn(),
    logout: vi.fn(),
    decodeJwtPayload: vi.fn(() => ({ sub: "oper1", role: "operator" })),
    getSessionTimeout: vi.fn(() => 30),
  },
}));

vi.mock("../../stores/emergency.js", () => ({
  emergencyStore: {
    subscribe: vi.fn(),
    get isEmergencyMode() { return false; },
    set isEmergencyMode(_v) {},
  },
}));

vi.mock("../../lib/ws.js", () => ({
  scaleStore: {
    subscribe: vi.fn((cb) => {
      cb({ connected: false, net_weight: 0, is_stable: false, unit: "kg" });
      return () => {};
    }),
    connected: false,
    net_weight: 0,
    is_stable: false,
    unit: "kg",
  },
  connect: vi.fn(),
  disconnect: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("KioskForm — R3: Reset general relegado a accion secundaria", () => {
  it("no muestra boton de reset en el area de acciones primarias (.form-actions)", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Confirmar Pesaje")).toBeInTheDocument();
    });
    const formActions = document.querySelector(".form-actions");
    expect(formActions).not.toBeNull();
    const resetInPrimary = formActions.querySelector(".btn-clear-all");
    expect(resetInPrimary).toBeNull();
  });

  it("muestra boton 'Limpiar todo' como accion secundaria", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Limpiar todo")).toBeInTheDocument();
    });
    const emergencySection = document.querySelector(".emergency-section");
    expect(emergencySection).not.toBeNull();
    const clearAllBtn = emergencySection.querySelector(".btn-clear-all");
    expect(clearAllBtn).not.toBeNull();
    expect(clearAllBtn.textContent.trim()).toBe("Limpiar todo");
  });

  it("muestra ConfirmModal al hacer clic en 'Limpiar todo'", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Limpiar todo")).toBeInTheDocument();
    });
    await fireEvent.click(screen.getByText("Limpiar todo"));
    await waitFor(() => {
      expect(screen.getByText("Limpiar Formulario")).toBeInTheDocument();
    });
    expect(screen.getByText("¿Está seguro de limpiar el formulario?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Limpiar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
  });
});
