/**
 * Tests para TemplateFormModal.svelte — Validación de formulario de plantilla.
 * Cubre: R5 (validación de nombre vacío).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import TemplateFormModal from "../TemplateFormModal.svelte";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("TemplateFormModal", () => {
  // ─── T16: test_template_form_modal_validation (R5) ─────────────
  describe("validacion de nombre (R5)", () => {
    it("muestra error si nombre esta vacio al guardar", async () => {
      const onSave = vi.fn();
      const onClose = vi.fn();

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

      // Find and click the Guardar button without filling name
      const saveBtn = screen.getByRole("button", { name: "Guardar" });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText("El nombre de la plantilla es requerido.")).toBeInTheDocument();
      });

      // onSave should NOT have been called
      expect(onSave).not.toHaveBeenCalled();
    });

    it("llama onSave si el nombre esta completo", async () => {
      const onSave = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

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
    });

    it("modo edit pre-puebla campos desde plantilla", async () => {
      const onSave = vi.fn();
      const onClose = vi.fn();

      const plantilla = {
        id: 1,
        name: "Reporte Existente",
        schedule: ["06:00", "14:00"],
        recipients: ["573001234567", "573007654321"],
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

      const nameInput = screen.getByPlaceholderText("Nombre de la plantilla");
      expect(nameInput.value).toBe("Reporte Existente");

      // recipients should be pre-filled as comma-separated
      const recipientsInput = screen.getByPlaceholderText(/Teléfonos separados por coma/);
      expect(recipientsInput.value).toContain("573001234567");
      expect(recipientsInput.value).toContain("573007654321");
    });
  });
});
