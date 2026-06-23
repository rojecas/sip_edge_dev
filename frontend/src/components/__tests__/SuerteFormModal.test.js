/**
 * Tests para SuerteFormModal.svelte — Modal crear/editar suerte.
 * Cubre: R14.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import SuerteFormModal from "../SuerteFormModal.svelte";

const mockHaciendas = [
  { id: 1, nombre: "Hacienda A", codigo: "HA" },
  { id: 2, nombre: "Hacienda B", codigo: "HB" },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("SuerteFormModal", () => {
  describe("Create mode (R14)", () => {
    it("muestra campos: Hacienda (select) y Codigo Suerte", () => {
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas, haciendaId: 1 },
      });
      // The Hacienda select and Codigo Suerte input should be present
      expect(screen.getByPlaceholderText("Código (máx. 4 caracteres)")).toBeInTheDocument();
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("muestra titulo 'Nueva Suerte'", () => {
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas },
      });
      expect(screen.getByText("Nueva Suerte")).toBeInTheDocument();
    });

    it("tiene botones Guardar y Cancelar", () => {
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas },
      });
      expect(screen.getByRole("button", { name: "Guardar" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
    });

    it("valida que Codigo Suerte es requerido", async () => {
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas, haciendaId: 1 },
      });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(screen.getByText("El código de suerte es requerido.")).toBeInTheDocument();
    });

    it("valida que Codigo Suerte no exceda 4 caracteres", async () => {
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas, haciendaId: 1 },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 4 caracteres)");
      await fireEvent.input(codigoInput, { target: { value: "12345" } });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(screen.getByText("El código debe tener máximo 4 caracteres.")).toBeInTheDocument();
    });

    it("llama onSave con payload al guardar en create", async () => {
      const onSave = vi.fn();
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas, haciendaId: 1, onSave },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 4 caracteres)");
      await fireEvent.input(codigoInput, { target: { value: "S001" } });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(onSave).toHaveBeenCalledTimes(1);
      expect(onSave).toHaveBeenCalledWith({
        hacienda_id: 1,
        codigo_suerte: "S001",
      });
    });

    it("llama onClose al pulsar Cancelar", async () => {
      const onClose = vi.fn();
      render(SuerteFormModal, {
        props: { show: true, mode: "create", haciendas: mockHaciendas, onClose },
      });
      await fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("Edit mode (R14)", () => {
    const mockSuerte = {
      id: 1,
      hacienda_id: 2,
      codigo_suerte: "S001",
      hacienda_nombre: "Hacienda B",
    };

    it("pre-puebla Codigo Suerte con el valor actual", () => {
      render(SuerteFormModal, {
        props: {
          show: true,
          mode: "edit",
          suerte: mockSuerte,
          haciendas: mockHaciendas,
          haciendaId: 2,
        },
      });
      const codigoInput = screen.getByPlaceholderText("Código (máx. 4 caracteres)");
      expect(codigoInput.value).toBe("S001");
    });

    it("muestra titulo 'Editar Suerte'", () => {
      render(SuerteFormModal, {
        props: {
          show: true,
          mode: "edit",
          suerte: mockSuerte,
          haciendas: mockHaciendas,
        },
      });
      expect(screen.getByText("Editar Suerte")).toBeInTheDocument();
    });

    it("llama onSave solo con codigo_suerte en edit", async () => {
      const onSave = vi.fn();
      render(SuerteFormModal, {
        props: {
          show: true,
          mode: "edit",
          suerte: mockSuerte,
          haciendas: mockHaciendas,
          haciendaId: 2,
          onSave,
        },
      });
      await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
      expect(onSave).toHaveBeenCalledWith({
        codigo_suerte: "S001",
      });
    });

    it("no renderiza cuando show es false", () => {
      const { container } = render(SuerteFormModal, {
        props: { show: false },
      });
      expect(container.querySelector(".modal-overlay")).toBeNull();
    });
  });
});
