/**
 * Tests para KioskLayout.svelte — Barra de navegación del kiosko.
 * Cubre: R1 (4 pestañas: Pesaje, Historial, Haciendas, Suertes).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/svelte";
import KioskLayout from "../KioskLayout.svelte";

vi.mock("../../stores/auth.js", () => ({
  authStore: {
    subscribe: vi.fn((cb) => {
      cb({
        token: "fake-token",
        role: "operator",
        username: "oper1",
        isAuthenticated: true,
        isOperator: true,
        isAdmin: false,
        jwtPayload: { sub: "oper1", role: "operator" },
      });
      return () => {};
    }),
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
    subscribe: vi.fn((cb) => {
      cb({ active: false });
      return () => {};
    }),
    get isEmergencyMode() { return false; },
    set isEmergencyMode(_v) {},
  },
}));

vi.mock("../../lib/api.js", () => ({
  api: {
    get: vi.fn().mockResolvedValue({ active: false }),
    post: vi.fn(),
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

vi.mock("../../lib/router.js", () => ({
  navigate: vi.fn(),
  getRoute: vi.fn(() => "/kiosco"),
  isRoute: vi.fn(() => true),
  onRouteChange: vi.fn(),
  replaceRoute: vi.fn(),
  router: { subscribe: vi.fn() },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("KioskLayout — R1: Pestañas de navegación", () => {
  it("muestra 4 botones de navegacion con clase .nav-btn", () => {
    render(KioskLayout);
    const navBtns = document.querySelectorAll(".nav-btn");
    expect(navBtns.length).toBe(4);
  });

  it("el primer boton es 'Pesaje'", () => {
    render(KioskLayout);
    const navBtns = document.querySelectorAll(".nav-btn");
    expect(navBtns[0].textContent).toBe("Pesaje");
  });

  it("el segundo boton es 'Historial'", () => {
    render(KioskLayout);
    const navBtns = document.querySelectorAll(".nav-btn");
    expect(navBtns[1].textContent).toBe("Historial");
  });

  it("el tercer boton es 'Haciendas'", () => {
    render(KioskLayout);
    const navBtns = document.querySelectorAll(".nav-btn");
    expect(navBtns[2].textContent).toBe("Haciendas");
  });

  it("el cuarto boton es 'Suertes'", () => {
    render(KioskLayout);
    const navBtns = document.querySelectorAll(".nav-btn");
    expect(navBtns[3].textContent).toBe("Suertes");
  });

  it("los botones se renderizan en el orden: Pesaje, Historial, Haciendas, Suertes", () => {
    render(KioskLayout);
    const labels = ["Pesaje", "Historial", "Haciendas", "Suertes"];
    const navBtns = document.querySelectorAll(".nav-btn");
    const actual = Array.from(navBtns).map((btn) => btn.textContent);
    expect(actual).toEqual(labels);
  });
});

describe("KioskLayout — R1: Header muestra username del operador", () => {
  it("muestra el username 'oper1' en el header", () => {
    render(KioskLayout);
    expect(screen.getByText("oper1")).toBeInTheDocument();
  });
});
