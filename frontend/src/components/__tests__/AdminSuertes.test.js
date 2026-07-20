/**
 * Tests para AdminSuertes.svelte — CRUD de suertes filtrable por hacienda.
 * Cubre: R12, R13, R15, R16, R17.
 * NOTA: Los modales se prueban en SuerteFormModal.test.js en aislamiento.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminSuertes from "../AdminSuertes.svelte";
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
  { id: 1, codigo: "HA", nombre: "Hacienda A" },
  { id: 2, codigo: "HB", nombre: "Hacienda B" },
];

const mockSuertes = [
  { id: 1, hacienda_id: 1, codigo_suerte: "S001", created_at: "2026-01-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
  { id: 2, hacienda_id: 1, codigo_suerte: "S002", created_at: "2026-02-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function waitForHaciendasLoaded() {
  await waitFor(
    () => {
      expect(screen.getByRole("heading", { name: "Suertes" })).toBeInTheDocument();
    },
    { timeout: 5000 }
  );
}

async function selectHacienda(index = 1) {
  const select = document.querySelector(".selector-row select");
  expect(select).toBeInTheDocument();
  await fireEvent.change(select, { target: { value: String(index) } });
}

describe("AdminSuertes — dropdown y carga (R12, R13)", () => {
  it("carga haciendas para dropdown al montar", async () => {
    api.get.mockResolvedValue({ items: mockHaciendas });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
  });

  it("muestra mensaje inicial 'Seleccione una hacienda para ver sus suertes' (R12)", async () => {
    api.get.mockResolvedValue({ items: mockHaciendas });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    expect(screen.getByText("Seleccione una hacienda para ver sus suertes")).toBeInTheDocument();
  });

  it("al seleccionar hacienda, carga suertes via GET /api/suertes?hacienda_id=X (R13)", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("hacienda_id=1")
    );
  });

  it("maneja respuesta como array directo (bug #20 fix)", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
  });

  it("maneja respuesta como {items: [...]} (paginated format)", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve({ items: mockSuertes });
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
  });

  it("muestra 'No hay suertes registradas para esta hacienda' si no hay suertes (R13)", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve([]);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(2);
    await waitFor(() => {
      expect(screen.getByText("No hay suertes registradas para esta hacienda.")).toBeInTheDocument();
    });
  });

  it("muestra columna Hacienda ID en la tabla", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("Hacienda ID")).toBeInTheDocument();
    });
  });
});

describe("AdminSuertes — crear suerte (R15)", () => {
  async function setupAndSelect() {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
  }

  it("POST /api/suertes se llama con payload correcto", async () => {
    await setupAndSelect();
    api.post.mockResolvedValue({ id: 3 });
    await fireEvent.click(screen.getByRole("button", { name: "+ Nueva Suerte" }));
    const codigoInput = screen.getByPlaceholderText("Código (máx. 4 caracteres)");
    await fireEvent.input(codigoInput, { target: { value: "S003" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(api.post).toHaveBeenCalledWith(
      "/api/suertes",
      expect.objectContaining({ codigo_suerte: "S003" })
    );
    await waitFor(() => {
      expect(screen.getByText("Suerte creada exitosamente.")).toBeInTheDocument();
    });
  });

  it("HTTP 409 muestra error en modal SIN cerrarlo (M2)", async () => {
    await setupAndSelect();
    const duplicateError = new ApiError("El código ya existe en esta hacienda.", 409);
    api.post.mockRejectedValue(duplicateError);
    await fireEvent.click(screen.getByRole("button", { name: "+ Nueva Suerte" }));
    const codigoInput = screen.getByPlaceholderText("Código (máx. 4 caracteres)");
    await fireEvent.input(codigoInput, { target: { value: "S001" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    await waitFor(() => {
      expect(screen.getByText("El código ya existe en esta hacienda.")).toBeInTheDocument();
    });
    expect(screen.getByText("Nueva Suerte")).toBeInTheDocument();
  });
});

describe("AdminSuertes — editar suerte (R16)", () => {
  async function setupAndSelect() {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
  }

  it("PUT /api/suertes/{id} se llama al guardar edicion", async () => {
    await setupAndSelect();
    api.put.mockResolvedValue({});
    const editBtns = document.querySelectorAll(".btn-edit");
    await fireEvent.click(editBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Editar Suerte")).toBeInTheDocument();
    });
    const codigoInput = screen.getByPlaceholderText("Código (máx. 4 caracteres)");
    await fireEvent.input(codigoInput, { target: { value: "S01X" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/api/suertes/1"),
      expect.objectContaining({ codigo_suerte: "S01X" })
    );
    await waitFor(() => {
      expect(screen.getByText("Suerte actualizada exitosamente.")).toBeInTheDocument();
    });
  });
});

describe("AdminSuertes — eliminar suerte (R17)", () => {
  async function setupAndSelect() {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
  }

  it("DELETE /api/suertes/{id} se ejecuta con confirmacion", async () => {
    await setupAndSelect();
    api.del.mockResolvedValue({});
    const deleteBtns = document.querySelectorAll(".btn-delete");
    await fireEvent.click(deleteBtns[0]);
    expect(screen.getByText("Eliminar Suerte")).toBeInTheDocument();
    const confirmBtns = document.querySelectorAll(".modal-actions .btn-confirm");
    await fireEvent.click(confirmBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Suerte eliminada exitosamente.")).toBeInTheDocument();
    });
  });
});

describe("AdminSuertes — allowDelete prop (F38 R3)", () => {
  async function setupAndSelect() {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes, { allowDelete: false });
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
  }

  it("oculta boton eliminar cuando allowDelete=false", async () => {
    await setupAndSelect();
    expect(screen.queryByTitle("Eliminar")).toBeNull();
  });

  it("muestra boton eliminar por defecto (allowDelete=true)", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/haciendas")) return Promise.resolve({ items: mockHaciendas });
      if (url.includes("/api/suertes")) return Promise.resolve(mockSuertes);
      return Promise.resolve({});
    });
    render(AdminSuertes);
    await waitForHaciendasLoaded();
    await selectHacienda(1);
    await waitFor(() => {
      expect(screen.getByText("S001")).toBeInTheDocument();
    });
    const deleteBtns = screen.getAllByTitle("Eliminar");
    expect(deleteBtns.length).toBeGreaterThan(0);
  });
});
