/**
 * Tests para AdminUsers.svelte — CRUD de usuarios con paginacion.
 * Cubre: R1, R3, R5, R6.
 * NOTA: Los modales se prueban en UserFormModal.test.js en aislamiento.
 * Aqui probamos flujo de API y UI del componente padre.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminUsers from "../AdminUsers.svelte";
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

const mockUsers = [
  {
    id: 1, username: "admin", full_name: "Administrador", employee_code: "11111", phone: "573001111111",
    role: "admin", is_active: true,
    created_at: "2026-01-01T10:00:00", updated_at: "2026-06-01T10:00:00",
  },
  {
    id: 2, username: "oper1", full_name: "Operador Uno", employee_code: "22222", phone: null,
    role: "operator", is_active: true,
    created_at: "2026-02-01T10:00:00", updated_at: "2026-06-01T10:00:00",
  },
  {
    id: 3, username: "corr1", full_name: "Corresponsal Uno", employee_code: "", phone: null,
    role: "corresponsal", is_active: false,
    created_at: "2026-03-01T10:00:00", updated_at: "2026-06-01T10:00:00",
  },
];

const mockPaginatedResponse = {
  items: mockUsers,
  total: 3,
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
      const h1 = screen.queryByRole("heading", { name: "Usuarios" });
      if (h1) return true;
      expect(screen.queryByText("Cargando usuarios...")).toBeNull();
      const table = document.querySelector("table");
      const empty = screen.queryByText("No hay usuarios registrados.");
      const error = screen.queryByText(/Error de conexión/i);
      if (table || empty || error) return true;
      throw new Error("Component did not finish loading");
    },
    { timeout: 5000 }
  );
}

describe("AdminUsers — carga de usuarios (R1)", () => {
  it("llama GET /api/users con paginacion al montar", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("/api/users?")
    );
  });

  it("muestra tabla con columnas correctas", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Usuario")).toBeInTheDocument();
    expect(screen.getByText("Nombre Completo")).toBeInTheDocument();
    expect(screen.getByText("Código Empresa")).toBeInTheDocument();
    expect(screen.getByText("Teléfono")).toBeInTheDocument();
    expect(screen.getByText("Rol")).toBeInTheDocument();
    expect(screen.getByText("Activo")).toBeInTheDocument();
    expect(screen.getByText("Creado")).toBeInTheDocument();
    expect(screen.getByText("Acciones")).toBeInTheDocument();
  });

  it("muestra datos de usuarios en la tabla", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    // "admin" appears both as username and as role tag — use getAllByText
    const adminEls = screen.getAllByText("admin");
    expect(adminEls.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Administrador")).toBeInTheDocument();
    expect(screen.getByText("oper1")).toBeInTheDocument();
  });

  it("muestra 'No hay usuarios registrados' si lista vacia", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, total_pages: 0 });
    render(AdminUsers);
    await waitForLoaded();
    expect(screen.getByText("No hay usuarios registrados.")).toBeInTheDocument();
  });

  it("muestra indicador de carga mientras carga", () => {
    api.get.mockReturnValue(new Promise(() => {}));
    render(AdminUsers);
    expect(screen.getByText("Cargando usuarios...")).toBeInTheDocument();
  });

  it("muestra error con boton Reintentar si falla la carga (R19)", async () => {
    api.get.mockRejectedValue(new Error("Network error"));
    render(AdminUsers);
    await waitFor(() => {
      expect(screen.getByText(/Error de conexión/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });
});

describe("AdminUsers — paginacion (C1, R1)", () => {
  it("muestra controles de paginacion cuando hay mas paginas", async () => {
    api.get.mockResolvedValue({
      items: mockUsers,
      total: 50,
      total_pages: 3,
      page: 1,
      page_size: 20,
    });
    render(AdminUsers);
    await waitForLoaded();
    expect(screen.getByText("Anterior")).toBeInTheDocument();
    expect(screen.getByText("Siguiente")).toBeInTheDocument();
  });

  it("boton Anterior deshabilitado en primera pagina", async () => {
    api.get.mockResolvedValue({
      items: mockUsers,
      total: 50,
      total_pages: 3,
      page: 1,
      page_size: 20,
    });
    render(AdminUsers);
    await waitForLoaded();
    const prevBtn = screen.getByText("Anterior");
    expect(prevBtn).toBeDisabled();
  });

  it("permite cambiar page size", async () => {
    api.get.mockResolvedValue({
      items: mockUsers,
      total: 50,
      total_pages: 3,
      page: 1,
      page_size: 20,
    });
    render(AdminUsers);
    await waitForLoaded();
    const select = document.querySelector(".page-size-select");
    expect(select).toBeInTheDocument();
  });

  it("cambiar page size resetea a page=1 (R17)", async () => {
    api.get.mockResolvedValue({
      items: mockUsers,
      total: 50,
      total_pages: 3,
      page: 1,
      page_size: 20,
    });
    render(AdminUsers);
    await waitForLoaded();

    api.get.mockClear();
    api.get.mockResolvedValue({
      items: mockUsers,
      total: 50,
      total_pages: 2,
      page: 1,
      page_size: 50,
    });

    const select = document.querySelector(".page-size-select");
    await fireEvent.change(select, { target: { value: "50" } });
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("page_size=50")
    );
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("page=1")
    );
  });
});

describe("AdminUsers — crear usuario (R3)", () => {
  it("abre modal al pulsar '+ Nuevo Usuario'", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nuevo Usuario" }));
    expect(screen.getByText("Nuevo Usuario")).toBeInTheDocument();
  });

  it("POST /api/users se llama con payload correcto al guardar", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.post.mockResolvedValue({ id: 4 });
    render(AdminUsers);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nuevo Usuario" }));
    // Fill the create form fields
    const userInput = screen.getByPlaceholderText("Nombre de usuario");
    const passInput = screen.getByPlaceholderText("Contraseña");
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(userInput, { target: { value: "nuevo" } });
    await fireEvent.input(passInput, { target: { value: "pass123" } });
    await fireEvent.input(nombreInput, { target: { value: "Usuario Nuevo" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(api.post).toHaveBeenCalledWith(
      "/api/users",
      expect.objectContaining({
        username: "nuevo",
        password: "pass123",
        full_name: "Usuario Nuevo",
      })
    );
  });

  it("HTTP 201 cierra modal y muestra exito", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.post.mockResolvedValue({ id: 4 });
    render(AdminUsers);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nuevo Usuario" }));
    const userInput = screen.getByPlaceholderText("Nombre de usuario");
    const passInput = screen.getByPlaceholderText("Contraseña");
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(userInput, { target: { value: "nuevo" } });
    await fireEvent.input(passInput, { target: { value: "pass123" } });
    await fireEvent.input(nombreInput, { target: { value: "Usuario Nuevo" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    await waitFor(() => {
      expect(screen.getByText("Usuario creado exitosamente.")).toBeInTheDocument();
    });
  });

  it("HTTP 409 muestra error y modal NO se cierra (C3)", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    const duplicateError = new ApiError("El usuario ya existe.", 409);
    api.post.mockRejectedValue(duplicateError);
    render(AdminUsers);
    await waitForLoaded();
    await fireEvent.click(screen.getByRole("button", { name: "+ Nuevo Usuario" }));
    const userInput = screen.getByPlaceholderText("Nombre de usuario");
    const passInput = screen.getByPlaceholderText("Contraseña");
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(userInput, { target: { value: "admin" } });
    await fireEvent.input(passInput, { target: { value: "pass123" } });
    await fireEvent.input(nombreInput, { target: { value: "Admin Duplicado" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    await waitFor(() => {
      expect(screen.getByText("El usuario ya existe.")).toBeInTheDocument();
    });
    // Modal debe seguir abierto
    expect(screen.getByText("Nuevo Usuario")).toBeInTheDocument();
  });
});

describe("AdminUsers — editar usuario (R5)", () => {
  it("abre modal de edicion al pulsar Editar", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    const editBtns = screen.getAllByText("Editar");
    await fireEvent.click(editBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Editar Usuario")).toBeInTheDocument();
    });
  });

  it("PUT /api/users/{id} se llama al guardar edicion", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.put.mockResolvedValue({});
    render(AdminUsers);
    await waitForLoaded();
    const editBtns = screen.getAllByText("Editar");
    await fireEvent.click(editBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Editar Usuario")).toBeInTheDocument();
    });
    // Fill required fields and click Guardar
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(nombreInput, { target: { value: "Updated Name" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/api/users/1"),
      expect.objectContaining({ full_name: "Updated Name" })
    );
  });

  it("HTTP 200 cierra modal y muestra exito", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.put.mockResolvedValue({});
    render(AdminUsers);
    await waitForLoaded();
    const editBtns = screen.getAllByText("Editar");
    await fireEvent.click(editBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Editar Usuario")).toBeInTheDocument();
    });
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(nombreInput, { target: { value: "Updated" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    await waitFor(() => {
      expect(screen.getByText("Usuario actualizado exitosamente.")).toBeInTheDocument();
    });
  });

  it("HTTP 404 muestra 'Usuario no encontrado'", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    const notFoundError = new ApiError("Not found", 404);
    api.put.mockRejectedValue(notFoundError);
    render(AdminUsers);
    await waitForLoaded();
    const editBtns = screen.getAllByText("Editar");
    await fireEvent.click(editBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Editar Usuario")).toBeInTheDocument();
    });
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(nombreInput, { target: { value: "Updated" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    await waitFor(() => {
      expect(screen.getByText("Usuario no encontrado.")).toBeInTheDocument();
    });
  });
});

describe("AdminUsers — desactivar usuario (R6)", () => {
  it("muestra ConfirmModal al pulsar Desactivar", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    // Click first table row's Desactivar (getAllByText includes table buttons and potentially modal)
    const rowBtns = document.querySelectorAll(".btn-delete");
    await fireEvent.click(rowBtns[0]);
    expect(screen.getByText("Desactivar Usuario")).toBeInTheDocument();
    expect(screen.getByText(/¿Está seguro de desactivar al usuario admin?/)).toBeInTheDocument();
  });

  it("DELETE exitoso cierra confirmacion y recarga", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    api.del.mockResolvedValue({});
    render(AdminUsers);
    await waitForLoaded();
    const rowBtns = document.querySelectorAll(".btn-delete");
    await fireEvent.click(rowBtns[0]);
    // Click the confirm modal's Desactivar button (the .btn-confirm button)
    const confirmBtns = document.querySelectorAll(".modal-actions .btn-confirm");
    await fireEvent.click(confirmBtns[0]);
    await waitFor(() => {
      expect(screen.getByText("Usuario desactivado exitosamente.")).toBeInTheDocument();
    });
  });

  it("Cancelar no llama DELETE", async () => {
    api.get.mockResolvedValue(mockPaginatedResponse);
    render(AdminUsers);
    await waitForLoaded();
    const rowBtns = document.querySelectorAll(".btn-delete");
    await fireEvent.click(rowBtns[0]);
    // Click Cancelar
    await fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(api.del).not.toHaveBeenCalled();
  });
});
