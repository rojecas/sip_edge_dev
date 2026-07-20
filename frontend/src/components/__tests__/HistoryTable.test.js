/**
 * Tests para HistoryTable.svelte + WeighingDetailModal.svelte — Feature 37.
 * Cubre: R7 (modal al hacer click en fila), R8 (Sin observaciones cuando no hay notas).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/svelte";
import HistoryTable from "../HistoryTable.svelte";

vi.mock("../../lib/api.js", () => ({
  api: {
    get: vi.fn().mockResolvedValue({
      items: [
        {
          id: 1,
          fecha: "2026-07-20",
          hora: "14:30:00",
          tractomula: "ABC123",
          vagon: "VAG-001",
          numero_guia: "G-001",
          hacienda_id: 1,
          suerte_id: 1,
          peso_muestra: 1.250,
          peso_mineral: 0.800,
          peso_vegetal_extrano: 0.050,
          usuario_id: 2,
          created_at: "2026-07-20T14:30:00",
          enviado_pc: false,
          manual_entry: false,
          tipo_cosecha: "Mecanico - Verde",
          notas: "Problemas con core sampler, muestra muy humeda",
        },
        {
          id: 2,
          fecha: "2026-07-20",
          hora: "15:00:00",
          tractomula: "XYZ999",
          vagon: "VAG-002",
          numero_guia: "G-002",
          hacienda_id: 1,
          suerte_id: 1,
          peso_muestra: 1.500,
          peso_mineral: 0.600,
          peso_vegetal_extrano: 0.100,
          usuario_id: 2,
          created_at: "2026-07-20T15:00:00",
          enviado_pc: false,
          manual_entry: false,
          tipo_cosecha: "Manual - Verde",
          notas: null,
        },
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1,
    }),
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

describe("HistoryTable — Feature 37: Modal de detalle (R7, R8)", () => {
  // T28: Clicking a row opens the modal with the weighing's notes (R7)
  it("al hacer click en una fila abre el modal con las notas del pesaje", async () => {
    render(HistoryTable);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText("VAG-001")).toBeInTheDocument();
    });

    // Click the first row (VAG-001)
    const row = screen.getByText("VAG-001").closest("tr");
    expect(row).not.toBeNull();
    await fireEvent.click(row);

    // Modal should open showing the detail
    await waitFor(() => {
      expect(screen.getByText(/Detalle del Pesaje #1/)).toBeInTheDocument();
    });

    // It should show the notes
    expect(screen.getByText("Problemas con core sampler, muestra muy humeda")).toBeInTheDocument();

    // It should show the pesos section (use getAllByText since values appear in table too)
    const pesoValues = screen.getAllByText("1.250");
    expect(pesoValues.length).toBeGreaterThanOrEqual(2); // table + modal
  });

  // T29: Modal shows "Sin observaciones" when no notes (R8)
  it("muestra 'Sin observaciones' cuando el pesaje no tiene notas", async () => {
    render(HistoryTable);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText("VAG-002")).toBeInTheDocument();
    });

    // Click the second row (VAG-002, notas=null)
    const row = screen.getByText("VAG-002").closest("tr");
    expect(row).not.toBeNull();
    await fireEvent.click(row);

    // Modal should open
    await waitFor(() => {
      expect(screen.getByText(/Detalle del Pesaje #2/)).toBeInTheDocument();
    });

    // It should show "Sin observaciones"
    expect(screen.getByText("Sin observaciones")).toBeInTheDocument();
  });
});
