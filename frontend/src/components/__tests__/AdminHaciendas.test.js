/**
 * Tests para AdminHaciendas.svelte — CRUD de haciendas con paginacion.
 * Cubre: R7, R9, R10, R11.
 * NOTA: Los modales se prueban en HaciendaFormModal.test.js en aislamiento.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminHaciendas from "../AdminHaciendas.svelte";
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

const mockHaciendas = [
  { id: 1, codigo: "HC001", nombre: "Hacienda A", created_at: "2026-01-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
  { id: 2, codigo: "HC002", nombre: "Hacienda B", created_at: "2026-02-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
];

const mockPaginatedResponse = {
  items: mockHaciendas,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function waitForLoaded() {
  await waitFor(
    () => {
      const h1 = screen.queryByRole("heading", { name: "Haciendas" });
      if (h1) return true;
      expect(screen.queryByText("Cargando haciendas...")).toBeNull();
      const table = document.querySelector("table");
      const empty = screen.queryByText("No hay haciendas registradas.");
      const error = screen.queryByText(/Error de conexión/i);
      if (table || empty || error) return true;
      throw new Error("Component did not finish loading");
    },
    { timeout: 5000 }
  );
}

describe("AdminHaciendas — carga (R7)", () => {
  it("llama GET /api/haciendas con paginacion al montar", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas);
    await waitForLoaded();
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("/api/haciendas?")
    );
  });

  it("muestra tabla con columnas correctas", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas);
    await waitForLoaded();
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Código")).toBeInTheDocument();
    expect(screen.getByText("Nombre")).toBeInTheDocument();
    expect(screen.getByText("Creado")).toBeInTheDocument();
    expect(screen.getByText("Actualizado")).toBeInTheDocument();
    expect(screen.getByText("Acciones")).toBeInTheDocument();
  });

  it("muestra datos en la tabla", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas);
    await waitForLoaded();
    expect(screen.getByText("HC001")).toBeInTheDocument();
    expect(screen.getByText("Hacienda A")).toBeInTheDocument();
  });

  it("muestra 'No hay haciendas registradas' si lista vacia", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, total_pages: 0 });
    render(AdminHaciendas);
    await waitForLoaded();
    expect(screen.getByText("No hay haciendas registradas.")).toBeInTheDocument();
  });
});

describe("AdminHaciendas — crear hacienda (R9)", () => {
  it("abre modal al pulsar '+ Nueva Hacienda'", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nueva Hacienda" }));
    expect(screen.getByText("Nueva Hacienda")).toBeInTheDocument();
  });

  it("POST /api/haciendas con payload y HTTP 201 cierra modal", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.post.mockResolvedValue({ id: 3 });
    render(AdminHaciendas);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nueva Hacienda" }));
    const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
    const nombreInput = screen.getByPlaceholderText("Nombre (máx. 255 caracteres)");
    await fireEvent.input(codigoInput, { target: { value: "HC003" } });
    await fireEvent.input(nombreInput, { target: { value: "Hacienda C" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(api.post).toHaveBeenCalledWith(
      "/api/haciendas",
      expect.objectContaining({ codigo: "HC003", nombre: "Hacienda C" })
    );
    await waitFor(() => {
      expect(screen.getByText("Hacienda creada exitosamente.")).toBeInTheDocument();
    });
  });

  it("HTTP 409 muestra error en modal SIN cerrarlo (M1)", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    const duplicateError = new ApiError("El código ya existe.", 409);
    api.post.mockRejectedValue(duplicateError);
    render(AdminHaciendas);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nueva Hacienda" }));
    const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
    const nombreInput = screen.getByPlaceholderText("Nombre (máx. 255 caracteres)");
    await fireEvent.input(codigoInput, { target: { value: "HC001" } });
    await fireEvent.input(nombreInput, { target: { value: "Duplicada" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    await waitFor(() => {
      expect(screen.getByText("El código ya existe.")).toBeInTheDocument();
    });
    expect(screen.getByText("Nueva Hacienda")).toBeInTheDocument();
  });
});

describe("AdminHaciendas — editar hacienda (R10)", () => {
  it("PUT /api/haciendas/{id} se llama al guardar edicion", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.put.mockResolvedValue({});
    render(AdminHaciendas);
    await waitForLoaded();
    const editBtns = document.querySelectorAll(".btn-edit");
    await fireEvent.click(editBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Editar Hacienda")).toBeInTheDocument();
    });
    const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
    const nombreInput = screen.getByPlaceholderText("Nombre (máx. 255 caracteres)");
    await fireEvent.input(codigoInput, { target: { value: "HC001X" } });
    await fireEvent.input(nombreInput, { target: { value: "Updated" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/api/haciendas/1"),
      expect.objectContaining({ codigo: "HC001X" })
    );
    await waitFor(() => {
      expect(screen.getByText("Hacienda actualizada exitosamente.")).toBeInTheDocument();
    });
  });
});

describe("AdminHaciendas — eliminar hacienda (R11)", () => {
  it("muestra ConfirmModal con mensaje de eliminacion logica", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas);
    await waitForLoaded();
    const deleteBtns = document.querySelectorAll(".btn-delete");
    await fireEvent.click(deleteBtns[0]);
    expect(screen.getByText("Eliminar Hacienda")).toBeInTheDocument();
    expect(screen.getByText(/eliminación lógica/)).toBeInTheDocument();
  });

  it("DELETE exitoso cierra modal y recarga", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.del.mockResolvedValue({});
    render(AdminHaciendas);
    await waitForLoaded();
    const deleteBtns = document.querySelectorAll(".btn-delete");
    await fireEvent.click(deleteBtns[0]);
    const confirmBtns = document.querySelectorAll(".modal-actions .btn-confirm");
    await fireEvent.click(confirmBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Hacienda eliminada exitosamente.")).toBeInTheDocument();
    });
  });
});

describe("AdminHaciendas — allowDelete prop (F38 R2)", () => {
  it("oculta boton eliminar cuando allowDelete=false", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas, { allowDelete: false });
    await waitForLoaded();
    expect(screen.queryByTitle("Eliminar")).toBeNull();
  });

  it("muestra boton eliminar por defecto (allowDelete=true)", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminHaciendas);
    await waitForLoaded();
    const deleteBtns = screen.getAllByTitle("Eliminar");
    expect(deleteBtns.length).toBeGreaterThan(0);
  });
});
