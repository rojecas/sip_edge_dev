/**
 * Tests para ConfirmModal.svelte — Modal genérico de confirmación.
 * Cubre: verificación de renderizado, callbacks, y cierre.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import ConfirmModal from "../ConfirmModal.svelte";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ConfirmModal", () => {
  describe("renderizado basico", () => {
    it("muestra titulo y mensaje cuando show es true", () => {
      render(ConfirmModal, {
        props: {
          show: true,
          title: "Eliminar Usuario",
          message: "¿Está seguro de eliminar al usuario admin?",
        },
      });
      expect(screen.getByText("Eliminar Usuario")).toBeInTheDocument();
      expect(screen.getByText("¿Está seguro de eliminar al usuario admin?")).toBeInTheDocument();
    });

    it("no renderiza nada cuando show es false", () => {
      const { container } = render(ConfirmModal, {
        props: {
          show: false,
          title: "Eliminar",
          message: "Mensaje",
        },
      });
      expect(container.querySelector(".modal-overlay")).toBeNull();
    });

    it("muestra botones con textos personalizados", () => {
      render(ConfirmModal, {
        props: {
          show: true,
          title: "Eliminar",
          message: "Mensaje",
          confirmText: "Sí, eliminar",
          cancelText: "No, cancelar",
        },
      });
      expect(screen.getByRole("button", { name: "Sí, eliminar" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "No, cancelar" })).toBeInTheDocument();
    });

    it("usa textos por defecto si no se pasan props", () => {
      render(ConfirmModal, { props: { show: true } });
      expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
    });
  });

  describe("callbacks", () => {
    it("llama onConfirm al pulsar el boton confirmar", async () => {
      const onConfirm = vi.fn();
      render(ConfirmModal, {
        props: { show: true, onConfirm },
      });
      await fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    it("llama onCancel al pulsar el boton cancelar", async () => {
      const onCancel = vi.fn();
      render(ConfirmModal, {
        props: { show: true, onCancel },
      });
      await fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    it("llama onCancel al pulsar el boton cerrar (x)", async () => {
      const onCancel = vi.fn();
      render(ConfirmModal, {
        props: { show: true, onCancel },
      });
      const closeBtn = screen.getByRole("button", { name: "Cerrar" });
      await fireEvent.click(closeBtn);
      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });
});
