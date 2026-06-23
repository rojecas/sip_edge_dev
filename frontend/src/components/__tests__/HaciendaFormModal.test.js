/**
 * Tests para HaciendaFormModal.svelte — Modal crear/editar hacienda.
 * Cubre: R8.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import HaciendaFormModal from "../HaciendaFormModal.svelte";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("HaciendaFormModal", () => {
  describe("Create mode (R8)", () => {
    it("muestra campos: Codigo y Nombre", () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      expect(screen.getByPlaceholderText("Código (máx. 8 caracteres)")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("Nombre (máx. 255 caracteres)")).toBeInTheDocument();
    });

    it("muestra titulo 'Nueva Hacienda'", () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      expect(screen.getByText("Nueva Hacienda")).toBeInTheDocument();
    });

    it("tiene botones Guardar y Cancelar", () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      expect(screen.getByRole("button", { name: "Guardar" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
    });

    it("valida que Codigo es requerido", async () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(screen.getByText("El código es requerido.")).toBeInTheDocument();
    });

    it("valida que Codigo no exceda 8 caracteres", async () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
      await fireEvent.input(codigoInput, { target: { value: "123456789" } });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(screen.getByText("El código debe tener máximo 8 caracteres.")).toBeInTheDocument();
    });

    it("valida que Nombre es requerido", async () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
      await fireEvent.input(codigoInput, { target: { value: "HC001" } });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(screen.getByText("El nombre es requerido.")).toBeInTheDocument();
    });

    it("valida que Nombre no exceda 255 caracteres", async () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "create" },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
      const nombreInput = screen.getByPlaceholderText("Nombre (máx. 255 caracteres)");
      await fireEvent.input(codigoInput, { target: { value: "HC001" } });
      const longName = "A".repeat(256);
      await fireEvent.input(nombreInput, { target: { value: longName } });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(screen.getByText("El nombre debe tener máximo 255 caracteres.")).toBeInTheDocument();
    });

    it("llama onSave con payload al guardar exitosamente", async () => {
      const onSave = vi.fn();
      render(HaciendaFormModal, {
        props: { show: true, mode: "create", onSave },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
      const nombreInput = screen.getByPlaceholderText("Nombre (máx. 255 caracteres)");
      await fireEvent.input(codigoInput, { target: { value: "HC001" } });
      await fireEvent.input(nombreInput, { target: { value: "Hacienda Test" } });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(onSave).toHaveBeenCalledTimes(1);
      expect(onSave).toHaveBeenCalledWith({
        codigo: "HC001",
        nombre: "Hacienda Test",
      });
    });
  });

  describe("Edit mode (R8)", () => {
    const mockHacienda = { id: 1, codigo: "HC001", nombre: "Hacienda Original" };

    it("pre-puebla campos con datos de la hacienda", () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "edit", hacienda: mockHacienda },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 8 caracteres)");
      const nombreInput = screen.getByPlaceholderText("Nombre (máx. 255 caracteres)");
      expect(codigoInput.value).toBe("HC001");
      expect(nombreInput.value).toBe("Hacienda Original");
    });

    it("muestra titulo 'Editar Hacienda'", () => {
      render(HaciendaFormModal, {
        props: { show: true, mode: "edit", hacienda: mockHacienda },
      });
      expect(screen.getByText("Editar Hacienda")).toBeInTheDocument();
    });

    it("no renderiza cuando show es false", () => {
      const { container } = render(HaciendaFormModal, {
        props: { show: false },
      });
      expect(container.querySelector(".modal-overlay")).toBeNull();
    });

    it("muestra mensaje de error si se pasa via prop", () => {
      render(HaciendaFormModal, {
        props: {
          show: true,
          mode: "create",
          error: "El código ya existe.",
        },
      });
      expect(screen.getByText("El código ya existe.")).toBeInTheDocument();
    });
  });
});
