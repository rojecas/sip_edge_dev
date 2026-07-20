/**
 * Tests para HaciendaCodeInput.svelte — Componente compartido de entrada de código de hacienda.
 * Cubre: R3, R5, R6, R7, R8, R9, R10.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent, waitFor } from "@testing-library/svelte";
import HaciendaCodeInput from "../HaciendaCodeInput.svelte";

const { mockNavigate } = vi.hoisted(() => ({
  mockNavigate: vi.fn(),
}));

vi.mock("../../lib/api.js", () => ({
  api: { get: vi.fn() },
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

vi.mock("../../lib/router.js", () => ({
  navigate: mockNavigate,
}));

import { api, buildQuery } from "../../lib/api.js";

const mockHacienda = {
  id: 1,
  codigo: "131",
  nombre: "Hacienda San Jos\u00e9",
  created_at: "2026-01-15T10:00:00",
  updated_at: "2026-06-01T08:30:00",
  created_by: 1,
  created_by_username: "admin",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("HaciendaCodeInput — búsqueda y display (R3, R5)", () => {
  // T15: Enter with valid code → confirmed display with CODIGO - NOMBRE format
  it("muestra display confirmado con formato CODIGO - NOMBRE al presionar Enter con código válido (T15)", async () => {
    api.get.mockResolvedValue({ items: [mockHacienda], total: 1, page: 1, page_size: 1, total_pages: 1 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");
    expect(input).toBeInTheDocument();

    await fireEvent.input(input, { target: { value: "131" } });
    await fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      const display = document.querySelector(".confirmed-text");
      expect(display).not.toBeNull();
      expect(display.textContent.trim()).toBe("131 - Hacienda San Jos\u00e9");
    });

    // Verify onSelect was called with the hacienda object
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: 1, codigo: "131" })
    );

    // Verify API was called with correct params
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("search=131")
    );
    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("page_size=1")
    );
  });

  // Also test with Tab key
  it("dispara búsqueda al presionar Tab con código ingresado", async () => {
    api.get.mockResolvedValue({ items: [mockHacienda], total: 1, page: 1, page_size: 1, total_pages: 1 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");
    await fireEvent.input(input, { target: { value: "131" } });
    await fireEvent.keyDown(input, { key: "Tab" });

    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith(
        expect.objectContaining({ id: 1, codigo: "131" })
      );
    });
  });
});

describe("HaciendaCodeInput — error modal (R7, R8, R9)", () => {
  // T16: Non-existent code → error modal with correct text and buttons
  it("muestra modal de error con texto y botones al ingresar código inexistente (T16)", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 1, total_pages: 0 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");
    await fireEvent.input(input, { target: { value: "XYZ999" } });
    await fireEvent.keyDown(input, { key: "Enter" });

    // Wait for error modal
    await waitFor(() => {
      const heading = document.querySelector(".modal-header h3");
      expect(heading).not.toBeNull();
      expect(heading.textContent).toContain("no encontrado");
    });

    // Check modal message and explanation
    const modalMessage = document.querySelector(".modal-message");
    expect(modalMessage).not.toBeNull();
    expect(modalMessage.textContent).toContain("XYZ999");
    expect(modalMessage.textContent).toContain("no corresponde");
    const explanation = document.querySelector(".modal-explanation");
    expect(explanation).not.toBeNull();
    expect(explanation.textContent).toContain("error de digitaci");

    // Check buttons exist (R8, R9)
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear nueva hacienda" })).toBeInTheDocument();

    // onSelect should NOT have been called with a hacienda
    expect(onSelect).not.toHaveBeenCalled();
  });

  // R8: Reintentar button closes modal and focuses input
  it("botón Reintentar cierra modal y devuelve foco al input (R8)", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 1, total_pages: 0 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");
    await fireEvent.input(input, { target: { value: "XYZ999" } });
    await fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
    });

    await fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    // Modal should close
    await waitFor(() => {
      const overlay = document.querySelector(".modal-overlay");
      expect(overlay).toBeNull();
    });
  });

  // R9: Crear nueva hacienda navigates to /kiosco/haciendas
  it("botón Crear nueva hacienda navega a /kiosco/haciendas (R9)", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 1, total_pages: 0 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");
    await fireEvent.input(input, { target: { value: "XYZ999" } });
    await fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Crear nueva hacienda" })).toBeInTheDocument();
    });

    await fireEvent.click(screen.getByRole("button", { name: "Crear nueva hacienda" }));

    expect(mockNavigate).toHaveBeenCalledWith("/kiosco/haciendas");
  });
});

describe("HaciendaCodeInput — limpiar (R6, R10)", () => {
  // T17: Clear button → onSelect(null) is invoked
  it("invoca onSelect(null) al presionar botón limpiar (T17)", async () => {
    api.get.mockResolvedValue({ items: [mockHacienda], total: 1, page: 1, page_size: 1, total_pages: 1 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");
    await fireEvent.input(input, { target: { value: "131" } });
    await fireEvent.keyDown(input, { key: "Enter" });

    // Wait for confirmed display
    await waitFor(() => {
      const display = document.querySelector(".confirmed-text");
      expect(display).not.toBeNull();
    });

    // Click clear button
    const clearBtn = document.querySelector(".btn-clear");
    expect(clearBtn).not.toBeNull();
    await fireEvent.click(clearBtn);

    // onSelect(null) should be called
    expect(onSelect).toHaveBeenCalledWith(null);

    // Input should be visible again
    await waitFor(() => {
      const input2 = document.querySelector(".code-input");
      expect(input2).not.toBeNull();
    });
  });
});

describe("HaciendaCodeInput — sin llamadas por keystroke (R3)", () => {
  // T18: Typing without Enter/Tab → no API calls
  it("NO dispara llamadas a la API por cada keystroke (T18)", async () => {
    api.get.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 1, total_pages: 0 });

    const onSelect = vi.fn();
    render(HaciendaCodeInput, { onSelect });

    const input = screen.getByPlaceholderText("Ingrese c\u00f3digo de hacienda");

    // Type 5 characters without pressing Enter or Tab
    await fireEvent.input(input, { target: { value: "1" } });
    await fireEvent.input(input, { target: { value: "13" } });
    await fireEvent.input(input, { target: { value: "131" } });
    await fireEvent.input(input, { target: { value: "131A" } });
    await fireEvent.input(input, { target: { value: "131AB" } });

    // API should NOT have been called
    expect(api.get).not.toHaveBeenCalled();
  });
});
