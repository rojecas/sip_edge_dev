/**
 * Tests para AdminAnomalias.svelte — Historial de anomalías paginado.
 * Cubre: R7, R8 (carga y paginación).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminAnomalias from "../AdminAnomalias.svelte";
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

const mockAnomalyItems = [
  {
    id: 1,
    record_id: 101,
    layer: "zscore",
    z_score: 4.52,
    metric_value: 250.0,
    threshold: 3.0,
    llm_report: "Anomalía detectada en peso muestra del vagón V5.",
    sent_sms: true,
    created_at: "2026-06-19T10:00:00",
  },
  {
    id: 2,
    record_id: 102,
    layer: "relacional",
    z_score: null,
    metric_value: 0.65,
    threshold: 0.5,
    llm_report: null,
    sent_sms: false,
    created_at: "2026-06-18T10:00:00",
  },
];

async function waitForLoaded() {
  await waitFor(
    () => {
      const heading = screen.queryByRole("heading", { name: "Anomalías" });
      const loading = screen.queryByText("Cargando historial de anomalías...");
      if (heading) return true;
      if (!loading) {
        const table = document.querySelector("table");
        const empty = screen.queryByText("No hay anomalías registradas");
        const error = screen.queryByText(/Error de conexión/i);
        if (table || empty || error) return true;
      }
      throw new Error("Component did not finish loading");
    },
    { timeout: 5000 }
  );
}

describe("AdminAnomalias", () => {
  // ─── T17: test_admin_anomalias_pagination (R7, R8) ─────────────
  describe("carga de historial (R7)", () => {
    it("llama GET /api/anomalies/history con paginacion al montar", async () => {
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 2,
        total_pages: 1,
        page: 1,
        page_size: 20,
      });
      render(AdminAnomalias);
      await waitForLoaded();
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("/api/anomalies/history?")
      );
    });

    it("muestra indicador de carga mientras carga", () => {
      api.get.mockReturnValue(new Promise(() => {}));
      render(AdminAnomalias);
      expect(screen.getByText("Cargando historial de anomalías...")).toBeInTheDocument();
    });

    it("renderiza tabla con datos de anomalías", async () => {
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 2,
        total_pages: 1,
        page: 1,
        page_size: 20,
      });
      render(AdminAnomalias);
      await waitForLoaded();

      const table = document.querySelector("table");
      expect(table).toBeInTheDocument();

      // Column headers (R7)
      expect(screen.getByText("Capa")).toBeInTheDocument();
      expect(screen.getByText("Z-Score")).toBeInTheDocument();
      expect(screen.getByText("Valor Métrica")).toBeInTheDocument();
      expect(screen.getByText("Umbral")).toBeInTheDocument();
      expect(screen.getByText("Reporte LLM")).toBeInTheDocument();
      expect(screen.getByText("SMS Enviado")).toBeInTheDocument();
      expect(screen.getByText("Fecha")).toBeInTheDocument();

      // Anomaly data
      expect(screen.getByText("zscore")).toBeInTheDocument();
      expect(screen.getByText("Sí")).toBeInTheDocument();
      expect(screen.getByText("No")).toBeInTheDocument();
    });
  });

  // ─── Paginacion (R8) ──────────────────────────────────────────
  describe("paginacion (R8)", () => {
    it("muestra controles de paginacion cuando hay mas paginas", async () => {
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 50,
        total_pages: 3,
        page: 1,
        page_size: 20,
      });
      render(AdminAnomalias);
      await waitForLoaded();
      expect(screen.getByText("Anterior")).toBeInTheDocument();
      expect(screen.getByText("Siguiente")).toBeInTheDocument();
    });

    it("oculta controles cuando hay una sola pagina", async () => {
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 2,
        total_pages: 1,
      });
      render(AdminAnomalias);
      await waitForLoaded();
      expect(screen.queryByText("Anterior")).toBeNull();
      expect(screen.queryByText("Siguiente")).toBeNull();
    });

    it("boton Anterior deshabilitado en primera pagina", async () => {
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 50,
        total_pages: 3,
        page: 1,
        page_size: 20,
      });
      render(AdminAnomalias);
      await waitForLoaded();
      const prevBtn = screen.getByText("Anterior");
      expect(prevBtn).toBeDisabled();
    });

    it("cambiar page size resetea a page=1", async () => {
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 50,
        total_pages: 3,
        page: 1,
        page_size: 20,
      });
      render(AdminAnomalias);
      await waitForLoaded();

      api.get.mockClear();
      api.get.mockResolvedValue({
        items: mockAnomalyItems,
        total: 50,
        total_pages: 5,
        page: 1,
        page_size: 10,
      });

      const select = document.querySelector(".page-size-select");
      await fireEvent.change(select, { target: { value: "10" } });
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("page_size=10")
      );
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("page=1")
      );
    });
  });

  // ─── Lista vacia (R7) ──────────────────────────────────────────
  describe("lista vacia", () => {
    it("muestra 'No hay anomalías registradas' si items esta vacio", async () => {
      api.get.mockResolvedValue({ items: [], total: 0, total_pages: 1 });
      render(AdminAnomalias);
      await waitForLoaded();
      expect(screen.getByText("No hay anomalías registradas")).toBeInTheDocument();
    });
  });

  // ─── Error de carga (R7) ──────────────────────────────────────
  describe("error de carga", () => {
    it("muestra mensaje de error si GET falla", async () => {
      api.get.mockRejectedValue(new Error("Error de conexión"));
      render(AdminAnomalias);
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
    });
  });

  // ─── Panel Detectar Ahora (R13) ───────────────────────────────
  describe("panel Detectar Ahora (R13)", () => {
    it("muestra panel al pulsar 'Detectar Ahora'", async () => {
      api.get.mockResolvedValue({
        items: [],
        total: 0,
        total_pages: 1,
      });
      render(AdminAnomalias);
      await waitForLoaded();

      screen.getByRole("button", { name: "Detectar Ahora" }).click();
      await waitFor(() => {
        expect(screen.getByText("Detección bajo demanda")).toBeInTheDocument();
      });
    });
  });

  // ─── Detectar Ahora con resultados vacíos (R15) ────────────────
  describe("deteccion sin resultados (R15)", () => {
    it("muestra mensaje de no deteccion cuando el resultado es array vacio", async () => {
      // First load: empty history (no anomalies yet)
      api.get.mockResolvedValueOnce({
        items: [],
        total: 0,
        total_pages: 1,
      });
      render(AdminAnomalias);
      await waitForLoaded();

      // Open detection panel
      screen.getByRole("button", { name: "Detectar Ahora" }).click();
      await waitFor(() => {
        expect(screen.getByText("Detección bajo demanda")).toBeInTheDocument();
      });

      // Mock the detection API: empty array response
      api.get.mockResolvedValueOnce([]);

      // Click "Ejecutar Detección"
      screen.getByRole("button", { name: "Ejecutar Detección" }).click();

      // Wait for the empty result message
      await waitFor(() => {
        expect(
          screen.getByText(
            "No se detectaron anomalías con los parámetros seleccionados."
          )
        ).toBeInTheDocument();
      });
    });
  });
});
