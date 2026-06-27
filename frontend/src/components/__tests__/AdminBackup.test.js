/**
 * Tests para AdminBackup.svelte — Panel de Backups
 * Cubre: R7, R8, R9, R10
 */
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminBackup from "../AdminBackup.svelte";
import { api } from "../../lib/api.js";

// ── Mock api.js ─────────────────────────────────────────────────
vi.mock("../../lib/api.js", () => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn() },
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

// ── Fixtures ────────────────────────────────────────────────────
const mockBackupItems = [
  {
    id: 1,
    filename: "dump_2026-06-19.sql.gz",
    file_size: 1024000,
    local_checksum: "abc123def456",
    usb_copied: true,
    usb_checksum: "abc123def456",
    error_message: null,
    created_at: "2026-06-19T10:00:00",
  },
  {
    id: 2,
    filename: "dump_2026-06-18.sql.gz",
    file_size: 512000,
    local_checksum: "fed987cba654",
    usb_copied: false,
    usb_checksum: null,
    error_message: "USB no disponible",
    created_at: "2026-06-18T10:00:00",
  },
];

// ── Cleanup ─────────────────────────────────────────────────────
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// ── Helpers ─────────────────────────────────────────────────────
async function waitForLoaded() {
  await waitFor(
    () => {
      const h1 = screen.queryByRole("heading", { name: "Backup" });
      if (h1) return true;
      // Sometimes the component shows loading first
      expect(screen.queryByText("Cargando historial de backups...")).toBeNull();
      // If neither loading nor heading, check for table or empty message
      const table = document.querySelector("table");
      const empty = screen.queryByText("No hay registros de backup.");
      const error = screen.queryByText(/Error de conexión/i);
      if (table || empty || error) return true;
      throw new Error("Component did not finish loading");
    },
    { timeout: 5000 }
  );
}

// ── Tests ───────────────────────────────────────────────────────
describe("AdminBackup", () => {
  // ─── T15.1: carga historial al montar ─────────────────────────
  describe("carga de historial (R7)", () => {
    it("llama GET /api/backup/status con paginacion al montar", async () => {
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });
      render(AdminBackup);
      await waitForLoaded();
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("/api/backup/status?")
      );
    });

    it("muestra indicador de carga mientras carga", () => {
      api.get.mockReturnValue(new Promise(() => {}));
      render(AdminBackup);
      expect(screen.getByText("Cargando historial de backups...")).toBeInTheDocument();
    });
  });

  // ─── T15.2: renderiza tabla con datos ─────────────────────────
  describe("tabla de backups (R7)", () => {
    it("renderiza tabla con los field names corregidos", async () => {
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });
      render(AdminBackup);
      await waitForLoaded();

      // Verifica que la tabla existe
      const table = document.querySelector("table");
      expect(table).toBeInTheDocument();

      // Verifica columnas del header (R7)
      expect(screen.getByText("ID")).toBeInTheDocument();
      expect(screen.getByText("Archivo")).toBeInTheDocument();
      expect(screen.getByText("Tamaño")).toBeInTheDocument();
      expect(screen.getByText("Checksum Local")).toBeInTheDocument();
      expect(screen.getByText("Copia USB")).toBeInTheDocument();
      expect(screen.getByText("Checksum USB")).toBeInTheDocument();
      expect(screen.getByText("Error")).toBeInTheDocument();
      expect(screen.getByText("Fecha")).toBeInTheDocument();

      // Verifica que usa los field names ingleses (T6a fix confirmado)
      // filename
      expect(screen.getByText("dump_2026-06-19.sql.gz")).toBeInTheDocument();
      // file_size — formatted as "1000.0 KB" (1024000 bytes)
      expect(screen.getByText("1000.0 KB")).toBeInTheDocument();
      // local_checksum & usb_checksum — both show same value, use getAllByText
      const checksums = screen.getAllByText("abc123def456");
      expect(checksums.length).toBeGreaterThanOrEqual(2);
      // usb_copied: true → "Sí"
      expect(screen.getByText("Sí")).toBeInTheDocument();
      // usb_copied: false → "No"
      expect(screen.getByText("No")).toBeInTheDocument();
      // error_message
      expect(screen.getByText("USB no disponible")).toBeInTheDocument();
    });
  });

  // ─── T15.3: lista vacía ───────────────────────────────────────
  describe("lista vacia (R7)", () => {
    it("muestra 'No hay registros de backup' si items esta vacio", async () => {
      api.get.mockResolvedValue({ items: [], total: 0, total_pages: 1 });
      render(AdminBackup);
      await waitForLoaded();
      expect(screen.getByText("No hay registros de backup.")).toBeInTheDocument();
    });

    it("maneja respuesta sin propiedad items (fallback)", async () => {
      // Fallback: result.items || result || [] - empty object has no items
      api.get.mockResolvedValue({ total: 0, total_pages: 1 });
      render(AdminBackup);
      await waitForLoaded();
      expect(screen.getByText("No hay registros de backup.")).toBeInTheDocument();
    });

    it("muestra mensaje si la respuesta es null/undefined", async () => {
      // null triggers TypeError on .items, caught as loadError
      api.get.mockResolvedValue(null);
      render(AdminBackup);
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
    });
  });

  // ─── T15.4: ejecutar backup ───────────────────────────────────
  describe("ejecutar backup (R8, R9)", () => {
    it("envia POST /api/backup/run al pulsar Ejecutar Backup", async () => {
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });
      api.post.mockResolvedValue({});
      render(AdminBackup);
      await waitForLoaded();
      screen.getByRole("button", { name: "Ejecutar Backup" }).click();
      expect(api.post).toHaveBeenCalledWith("/api/backup/run");
    });

    it("tras 202, muestra mensaje y deshabilita el boton 30s", async () => {
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });
      api.post.mockResolvedValue({}); // HTTP 202 success
      render(AdminBackup);
      await waitForLoaded();
      screen.getByRole("button", { name: "Ejecutar Backup" }).click();
      await waitFor(() => {
        expect(screen.getByText("Backup iniciado en segundo plano.")).toBeInTheDocument();
      });
      // Boton muestra "Procesando... (Xs)" y esta deshabilitado
      await waitFor(() => {
        const btn = screen.getByRole("button", { name: /Procesando/i });
        expect(btn).toBeDisabled();
      });
    });

    it("error 4xx/5xx NO deshabilita el boton", async () => {
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });
      // Regular Error (not ApiError) → component shows "Error de conexión."
      api.post.mockRejectedValue(new Error("Server error"));
      render(AdminBackup);
      await waitForLoaded();
      screen.getByRole("button", { name: "Ejecutar Backup" }).click();
      // Wait for error message — component maps non-ApiError to "Error de conexión."
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
      // El boton debe seguir habilitado (R9)
      // Despues del error, el boton vuelve a "Ejecutar Backup" (running=false, runDisabled=false)
      await waitFor(() => {
        const btn = screen.getByRole("button", { name: "Ejecutar Backup" });
        expect(btn).not.toBeDisabled();
      });
    });
  });

  // ─── T15.6: boton Refrescar ──────────────────────────────────
  describe("boton Refrescar (R10)", () => {
    it("recarga la tabla al pulsar Refrescar", async () => {
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });
      render(AdminBackup);
      await waitForLoaded();

      // Clear the mock call record to verify second call
      api.get.mockClear();
      api.get.mockResolvedValue({ items: mockBackupItems, total: 2, total_pages: 1 });

      screen.getByRole("button", { name: "Refrescar" }).click();
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("/api/backup/status?")
      );
    });
  });

  // ─── Paginacion (T19) ──────────────────────────────────────
  describe("paginacion (R11, R12, R13, R14)", () => {
    it("muestra controles de paginacion cuando hay mas paginas", async () => {
      api.get.mockResolvedValue({
        items: mockBackupItems,
        total: 50,
        total_pages: 5,
        page: 1,
        page_size: 10,
      });
      render(AdminBackup);
      await waitForLoaded();
      expect(screen.getByText("Anterior")).toBeInTheDocument();
      expect(screen.getByText("Siguiente")).toBeInTheDocument();
    });

    it("oculta controles cuando hay una sola pagina", async () => {
      api.get.mockResolvedValue({
        items: mockBackupItems,
        total: 2,
        total_pages: 1,
      });
      render(AdminBackup);
      await waitForLoaded();
      expect(screen.queryByText("Anterior")).toBeNull();
      expect(screen.queryByText("Siguiente")).toBeNull();
    });

    it("boton Anterior deshabilitado en primera pagina", async () => {
      api.get.mockResolvedValue({
        items: mockBackupItems,
        total: 50,
        total_pages: 5,
        page: 1,
        page_size: 10,
      });
      render(AdminBackup);
      await waitForLoaded();
      const prevBtn = screen.getByText("Anterior");
      expect(prevBtn).toBeDisabled();
    });

    it("boton Siguiente deshabilitado en ultima pagina", async () => {
      api.get.mockResolvedValue({
        items: mockBackupItems,
        total: 50,
        total_pages: 5,
        page: 5,
        page_size: 10,
      });
      render(AdminBackup);
      await waitForLoaded();
      const nextBtn = screen.getByText("Siguiente");
      expect(nextBtn).toBeDisabled();
    });

    it("cambiar page size resetea a page=1", async () => {
      api.get.mockResolvedValue({
        items: mockBackupItems,
        total: 50,
        total_pages: 5,
        page: 1,
        page_size: 10,
      });
      render(AdminBackup);
      await waitForLoaded();

      api.get.mockClear();
      api.get.mockResolvedValue({
        items: mockBackupItems,
        total: 50,
        total_pages: 3,
        page: 1,
        page_size: 20,
      });

      const select = document.querySelector(".page-size-select");
      await fireEvent.change(select, { target: { value: "20" } });
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("page_size=20")
      );
      expect(api.get).toHaveBeenCalledWith(
        expect.stringContaining("page=1")
      );
    });
  });

  // ─── T15.extra: error de carga ───────────────────────────────
  describe("error de carga", () => {
    it("muestra mensaje de error si GET /api/backup/status falla", async () => {
      api.get.mockRejectedValue(new Error("Error de conexión"));
      render(AdminBackup);
      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
      });
    });

    it("muestra boton Reintentar en el error", async () => {
      api.get.mockRejectedValue(new Error("timeout"));
      render(AdminBackup);
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
      });
    });
  });
});
