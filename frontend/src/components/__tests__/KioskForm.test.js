/**
 * Tests para KioskForm.svelte — Formulario de pesaje.
 * Cubre: R3 (reset general relegado a accion secundaria),
 *        R2-R4-R6 (notas colapsables — Feature 37).
 */
import { vi, describe, it, expect, afterEach, beforeEach } from "vitest";
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

let _captureCallback = null;

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
  onScaleReading: vi.fn((callback) => {
    _captureCallback = callback;
  }),
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
      expect(screen.getByText("Confirmar Medidas")).toBeInTheDocument();
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

describe("KioskForm — Auto-capture PRINT (T41)", () => {
  it("muestra notificacion temporal al recibir peso sin campo con foco", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Confirmar Medidas")).toBeInTheDocument();
    });

    // Simulate scale_reading arriving when no weight field has focus
    const blurable = document.body;
    if (blurable && document.activeElement && document.activeElement !== document.body) {
      document.activeElement.blur();
    }

    // Invoke the capture callback with a scale reading
    if (_captureCallback) {
      _captureCallback({ net_weight: 125.450, is_stable: true, unit: "kg" });
    }

    await waitFor(() => {
      expect(screen.getByText(/Peso recibido: 125.450 kg/)).toBeInTheDocument();
    });
  });
});

describe("KioskForm — Feature 37: Notas colapsables (R2, R3, R4, R6)", () => {
  // T25: NotesField renders in the form (R2)
  it("renderiza el campo de notas colapsable en el formulario", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Confirmar Medidas")).toBeInTheDocument();
    });
    // The toggle button with label "Notas" should be visible
    const toggleBtn = screen.getByText("Notas");
    expect(toggleBtn).toBeInTheDocument();
  });

  // T26: Expand/collapse shows/hides textarea (R3, R4)
  it("al expandir muestra el textarea y al colapsar lo oculta", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Confirmar Medidas")).toBeInTheDocument();
    });

    // Initially textarea should not be visible
    const textareas = document.querySelectorAll(".notes-textarea");
    expect(textareas.length).toBe(0);

    // Click the toggle to expand
    const toggleBtn = screen.getByText("Notas").closest("button");
    await fireEvent.click(toggleBtn);

    // Now textarea should be visible
    await waitFor(() => {
      const expandedTextareas = document.querySelectorAll(".notes-textarea");
      expect(expandedTextareas.length).toBeGreaterThan(0);
    });

    // Click again to collapse
    await fireEvent.click(toggleBtn);

    // Textarea should be hidden again
    await waitFor(() => {
      const collapsedTextareas = document.querySelectorAll(".notes-textarea");
      expect(collapsedTextareas.length).toBe(0);
    });
  });

  // T27: Reset form clears notes (R6)
  it("al resetear el formulario se limpia el campo notas", async () => {
    render(KioskForm);
    await waitFor(() => {
      expect(screen.getByText("Confirmar Medidas")).toBeInTheDocument();
    });

    // Expand notes and type something
    const toggleBtn = screen.getByText("Notas").closest("button");
    await fireEvent.click(toggleBtn);

    await waitFor(() => {
      const textareas = document.querySelectorAll(".notes-textarea");
      expect(textareas.length).toBeGreaterThan(0);
    });

    const textarea = document.querySelector(".notes-textarea");
    await fireEvent.input(textarea, { target: { value: "Nota de prueba" } });
    expect(textarea.value).toBe("Nota de prueba");

    // Collapse first (doesn't affect value)
    await fireEvent.click(toggleBtn);

    // Click "Limpiar todo"
    const limpiarBtn = screen.getByText("Limpiar todo");
    await fireEvent.click(limpiarBtn);

    // Confirm modal should appear
    await waitFor(() => {
      expect(screen.getByText("Limpiar Formulario")).toBeInTheDocument();
    });

    // Click Limpiar in modal
    const confirmBtn = screen.getByRole("button", { name: "Limpiar" });
    await fireEvent.click(confirmBtn);

    // After reset, notes should be empty
    // Expand again to check
    await waitFor(async () => {
      const toggleAfterReset = screen.getByText("Notas").closest("button");
      await fireEvent.click(toggleAfterReset);
      const textareaAfterReset = document.querySelector(".notes-textarea");
      expect(textareaAfterReset).not.toBeNull();
      expect(textareaAfterReset.value).toBe("");
    });
  });
});
