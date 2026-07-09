/**
 * Tests para TemplateFormModal.svelte — Validación de formulario de plantilla.
 * Cubre: R5 (validación de nombre vacío), R19 (selector de usuarios con user_ids).
 *
 * Fase 8: Agregados tests para el selector de usuarios (checkboxes)
 * en reemplazo del input de texto de destinatarios.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import TemplateFormModal from "../TemplateFormModal.svelte";

// Mock api.js
vi.mock("../../lib/api.js", () => ({
  api: {
    get: vi.fn(),
  },
  ApiError: class extends Error {
    constructor(message, status) {
      super(message);
      this.status = status;
    }
  },
}));

import { api } from "../../lib/api.js";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const mockUsers = [
  { id: 1, username: "admin1", full_name: "Admin Uno", phone: "+573001111111", role: "admin", is_active: true },
  { id: 2, username: "admin2", full_name: "Admin Dos", phone: "+573002222222", role: "admin", is_active: true },
  { id: 3, username: "corr1", full_name: "Corr Uno", phone: "+573003333333", role: "corresponsal", is_active: true },
  { id: 4, username: "op1", full_name: "Operador Uno", phone: "+573004444444", role: "operator", is_active: true },
  { id: 5, username: "inactive", full_name: "Inactivo", phone: "+573005555555", role: "admin", is_active: false },
];

describe("TemplateFormModal", () => {
  // ─── T16: test_template_form_modal_validation (R5) ─────────────
  describe("validacion de nombre (R5)", () => {
    it("muestra error si nombre esta vacio al guardar", async () => {
      const onSave = vi.fn();
      const onClose = vi.fn();

      // Mock users API
      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose,
          onSave,
        },
      });

      // Should show the modal
      await waitFor(() => {
        expect(screen.getByText("Nueva Plantilla")).toBeInTheDocument();
      });

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });

      // Find and click the Guardar button without filling name
      const saveBtn = screen.getByRole("button", { name: "Guardar" });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText("El nombre de la plantilla es requerido.")).toBeInTheDocument();
      });

      // onSave should NOT have been called
      expect(onSave).not.toHaveBeenCalled();
    });

    it("llama onSave con user_ids si el nombre esta completo", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose,
          onSave,
        },
      });

      await waitFor(() => {
        expect(screen.getByText("Nueva Plantilla")).toBeInTheDocument();
      });

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });

      // Fill in the name
      const nameInput = screen.getByPlaceholderText("Nombre de la plantilla");
      fireEvent.input(nameInput, { target: { value: "Mi Plantilla" } });

      // Click Guardar
      const saveBtn = screen.getByRole("button", { name: "Guardar" });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(onSave).toHaveBeenCalled();
      });

      const payload = onSave.mock.calls[0][0];
      expect(payload.name).toBe("Mi Plantilla");
      // Debe enviar user_ids en lugar de recipients
      expect(payload.user_ids).toBeDefined();
      expect(payload.recipients).toBeUndefined();
    });

    it("modo edit pre-selecciona usuarios desde recipient_ids", async () => {
      const onSave = vi.fn();
      const onClose = vi.fn();

      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      const plantilla = {
        id: 1,
        name: "Reporte Existente",
        schedule: ["06:00", "14:00"],
        recipient_ids: [1, 3],  // Admin Uno (id=1) + Corr Uno (id=3)
        recipients: ["+573001111111", "+573003333333"],
        metrics: ["count", "avg"],
        is_active: true,
      };

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "edit",
          plantilla: plantilla,
          error: "",
          onClose,
          onSave,
        },
      });

      await waitFor(() => {
        expect(screen.getByText("Editar Plantilla")).toBeInTheDocument();
      });

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });

      const nameInput = screen.getByPlaceholderText("Nombre de la plantilla");
      expect(nameInput.value).toBe("Reporte Existente");

      // Verify the active user count label shows 2 selected
      await waitFor(() => {
        expect(screen.getByText("(2 seleccionados)")).toBeInTheDocument();
      });
    });
  });

  // ─── T31: test_user_selector (R19) ─────────────────────────────
  describe("selector de usuarios (R19)", () => {
    it("carga usuarios via GET /api/users al abrir", async () => {
      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose: vi.fn(),
          onSave: vi.fn(),
        },
      });

      // Debe llamar a GET /api/users
      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith("/api/users?page_size=100");
      });

      // Los usuarios cargados deben aparecer
      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });
    });

    it("muestra solo admin y corresponsal activos", async () => {
      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose: vi.fn(),
          onSave: vi.fn(),
        },
      });

      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });

      // Admin activos deben estar
      expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      expect(screen.getByText("Admin Dos")).toBeInTheDocument();
      // Corresponsal activo debe estar
      expect(screen.getByText("Corr Uno")).toBeInTheDocument();

      // Operator NO debe aparecer (no es admin ni corresponsal)
      expect(screen.queryByText("Operador Uno")).not.toBeInTheDocument();

      // Inactivo NO debe aparecer (is_active=false)
      expect(screen.queryByText("Inactivo")).not.toBeInTheDocument();
    });

    it("filtra usuarios por nombre con la busqueda", async () => {
      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose: vi.fn(),
          onSave: vi.fn(),
        },
      });

      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });

      // Type in search box
      const searchInput = screen.getByPlaceholderText("Buscar por nombre...");
      fireEvent.input(searchInput, { target: { value: "Corr" } });

      // Wait for filter - "Corr Uno" should still be visible
      await waitFor(() => {
        expect(screen.getByText("Corr Uno")).toBeInTheDocument();
      });

      // "Admin Uno" should be gone
      expect(screen.queryByText("Admin Uno")).not.toBeInTheDocument();
    });

    it("envia user_ids en el payload al guardar", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);

      api.get.mockResolvedValue({ items: mockUsers, total: 5, page: 1, page_size: 100 });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose: vi.fn(),
          onSave,
        },
      });

      await waitFor(() => {
        expect(screen.getByText("Admin Uno")).toBeInTheDocument();
      });

      // Fill name
      const nameInput = screen.getByPlaceholderText("Nombre de la plantilla");
      fireEvent.input(nameInput, { target: { value: "Test" } });

      // Click on "Seleccionar todos" to select all filtered users (3: Admin Uno, Admin Dos, Corr Uno)
      const selectAllBtn = screen.getByText("Seleccionar todos");
      fireEvent.click(selectAllBtn);

      // Click Guardar
      const saveBtn = screen.getByRole("button", { name: "Guardar" });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(onSave).toHaveBeenCalled();
      });

      const payload = onSave.mock.calls[0][0];
      // Debe enviar user_ids
      expect(payload.user_ids).toBeDefined();
      expect(payload.user_ids).toHaveLength(3);
      expect(payload.user_ids).toContain(1);
      expect(payload.user_ids).toContain(2);
      expect(payload.user_ids).toContain(3);
      // NO debe enviar recipients
      expect(payload.recipients).toBeUndefined();
    });

    it("muestra mensaje si no hay usuarios admin/corresponsal activos", async () => {
      // Return only operator and inactive users
      api.get.mockResolvedValue({
        items: [
          { id: 4, username: "op1", full_name: "Op Uno", phone: "555", role: "operator", is_active: true },
          { id: 5, username: "inactive", full_name: "Inactiv", phone: "666", role: "admin", is_active: false },
        ],
        total: 2, page: 1, page_size: 100,
      });

      render(TemplateFormModal, {
        props: {
          show: true,
          mode: "create",
          plantilla: null,
          error: "",
          onClose: vi.fn(),
          onSave: vi.fn(),
        },
      });

      await waitFor(() => {
        expect(screen.getByText("No hay usuarios admin o corresponsal activos.")).toBeInTheDocument();
      });
    });
  });
});
