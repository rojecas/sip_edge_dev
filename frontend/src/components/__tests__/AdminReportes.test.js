/**
 * Tests para AdminReportes.svelte — CRUD de plantillas de reportes.
 * Cubre: R1 (carga de plantillas).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminReportes from "../AdminReportes.svelte";
import { api, ApiError } from "../../lib/api.js";

vi.mock("../../lib/api.js", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), del: vi.fn() },
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

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const mockTemplates = [
  {
    id: 1,
    name: "Resumen Turno Mañana",
    schedule: ["06:00", "14:00"],
    recipients: ["573001234567"],
    metrics: ["count", "avg", "min_max"],
    is_active: true,
    created_at: "2026-06-15T10:00:00",
    updated_at: null,
  },
  {
    id: 2,
    name: "Reporte Diario",
    schedule: ["22:00"],
    recipients: ["573007654321"],
    metrics: ["breakdown_by_hacienda", "anomaly_count"],
    is_active: false,
    created_at: "2026-06-14T10:00:00",
    updated_at: "2026-06-15T10:00:00",
  },
];

async function waitForLoaded() {
  await waitFor(
    () => {
      const heading = screen.queryByRole("heading", { name: "Reportes Programados" });
      const loading = screen.queryByText("Cargando plantillas de reportes...");
      if (heading) return true;
      if (!loading) {
        const table = document.querySelector("table");
        const empty = screen.queryByText("No hay plantillas de reportes");
        const error = screen.queryByText(/Error de conexión/i);
        if (table || empty || error) return true;
      }
      throw new Error("Component did not finish loading");
    },
    { timeout: 5000 }
  );
}

describe("AdminReportes", () => {
  // ─── T15: test_admin_reportes_loads_templates (R1) ─────────────
  describe("carga de plantillas (R1)", () => {
    it("llama GET /api/reports/templates al montar", async () => {
      api.get.mockResolvedValue(mockTemplates);
      render(AdminReportes);
      await waitForLoaded();
      expect(api.get).toHaveBeenCalledWith("/api/reports/templates");
    });

    it("muestra indicador de carga mientras carga", () => {
      api.get.mockReturnValue(new Promise(() => {}));
      render(AdminReportes);
      expect(screen.getByText("Cargando plantillas de reportes...")).toBeInTheDocument();
    });

    it("renderiza tabla con plantillas", async () => {
      api.get.mockResolvedValue(mockTemplates);
      render(AdminReportes);
      await waitForLoaded();

      const table = document.querySelector("table");
      expect(table).toBeInTheDocument();

      // Column headers
      expect(screen.getByText("ID")).toBeInTheDocument();
      expect(screen.getByText("Nombre")).toBeInTheDocument();
      expect(screen.getByText("Schedule")).toBeInTheDocument();
      expect(screen.getByText("Métricas")).toBeInTheDocument();
      expect(screen.getByText("Activo")).toBeInTheDocument();
      expect(screen.getByText("Acciones")).toBeInTheDocument();

      // Template names
      expect(screen.getByText("Resumen Turno Mañana")).toBeInTheDocument();
      expect(screen.getByText("Reporte Diario")).toBeInTheDocument();
    });

    it("muestra mensaje vacio si no hay plantillas", async () => {
      api.get.mockResolvedValue([]);
      render(AdminReportes);
      await waitForLoaded();
      expect(screen.getByText("No hay plantillas de reportes")).toBeInTheDocument();
    });

    it("maneja respuesta null como error", async () => {
      // null triggers TypeError on .items, caught as generic error
      api.get.mockResolvedValue(null);
      render(AdminReportes);
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
    });
  });

  // ─── R2: error de carga ─────────────────────────────────────────
  describe("error de carga (R2)", () => {
    it("muestra mensaje de error si GET falla", async () => {
      api.get.mockRejectedValue(new Error("Error de conexión"));
      render(AdminReportes);
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
    });

    it("muestra boton Reintentar en el error", async () => {
      api.get.mockRejectedValue(new Error("timeout"));
      render(AdminReportes);
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
      });
    });
  });

  // ─── R5 / R6: crear y eliminar ─────────────────────────────────
  describe("crear plantilla (R5)", () => {
    it("abre modal al pulsar '+ Nueva Plantilla'", async () => {
      api.get.mockResolvedValue(mockTemplates);
      render(AdminReportes);
      await waitForLoaded();

      screen.getByRole("button", { name: "+ Nueva Plantilla" }).click();
      await waitFor(() => {
        expect(screen.getByText("Nueva Plantilla")).toBeInTheDocument();
      });
    });
  });

  // ─── R6: eliminar plantilla con confirmación ───────────────────
  describe("eliminar plantilla (R6)", () => {
    it("muestra ConfirmModal al pulsar boton eliminar", async () => {
      api.get.mockResolvedValue(mockTemplates);
      render(AdminReportes);
      await waitForLoaded();

      // Click the 🗑️ button (found by title "Eliminar")
      const delButtons = screen.getAllByTitle("Eliminar");
      expect(delButtons.length).toBeGreaterThan(0);
      delButtons[0].click();

      await waitFor(() => {
        expect(screen.getByText("Eliminar Plantilla")).toBeInTheDocument();
      });
    });

    it("al confirmar eliminacion, llama api.del y recarga la tabla", async () => {
      api.get.mockResolvedValue(mockTemplates);
      api.del.mockResolvedValue({ ok: true });
      render(AdminReportes);
      await waitForLoaded();

      // Click 🗑️ on first template (id=1, "Resumen Turno Mañana")
      const delButtons = screen.getAllByTitle("Eliminar");
      delButtons[0].click();

      // Wait for ConfirmModal to appear
      await waitFor(() => {
        expect(screen.getByText("Eliminar Plantilla")).toBeInTheDocument();
      });

      // Verify the confirmation message includes the template name
      expect(
        screen.getByText(/¿Eliminar la plantilla "Resumen Turno Mañana"\?/)
      ).toBeInTheDocument();

      // Clear get mock to verify reload call
      api.get.mockClear();
      // Mock the reload response
      api.get.mockResolvedValue([mockTemplates[1]]); // Only second template remains

      // Confirm deletion
      const confirmBtn = screen.getByRole("button", { name: "Eliminar" });
      confirmBtn.click();

      // Verify api.del was called with correct URL
      await waitFor(() => {
        expect(api.del).toHaveBeenCalledWith("/api/reports/templates/1");
      });

      // Verify the table is reloaded (api.get called for reload)
      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith("/api/reports/templates");
      });
    });
  });
});
