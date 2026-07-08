/**
 * Tests para AdminAgente.svelte — Consola de consultas al agente IA.
 * Cubre: R10 (envío de consulta), R11 (loading state), R12 (error).
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/svelte";
import AdminAgente from "../AdminAgente.svelte";
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

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function waitForReady() {
  await waitFor(
    () => {
      const heading = screen.queryByRole("heading", { name: "Agente IA" });
      if (heading) return true;
      throw new Error("Component did not render");
    },
    { timeout: 5000 }
  );
}

describe("AdminAgente", () => {
  // ─── T18: test_admin_agente_send_query (R10) ──────────────────
  describe("envío de consulta (R10)", () => {
    it("muestra mensaje de bienvenida al montar", async () => {
      render(AdminAgente);
      await waitForReady();
      expect(screen.getByText(/Bienvenido a la consola del Agente IA/)).toBeInTheDocument();
    });

    it("envía consulta y muestra respuesta", async () => {
      api.post.mockResolvedValue({
        response: "Los datos del turno mañana muestran 120 pesajes con un promedio de 105kg.",
        dev_mode: false,
      });
      render(AdminAgente);
      await waitForReady();

      // Type query
      const textarea = screen.getByPlaceholderText("Escriba su consulta aquí...");
      fireEvent.input(textarea, { target: { value: "¿Cuántos pesajes hubo hoy?" } });

      // Click send
      const sendBtn = screen.getByRole("button", { name: "Enviar" });
      fireEvent.click(sendBtn);

      // Wait for response to appear
      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith("/api/agent/query", {
          query: "¿Cuántos pesajes hubo hoy?",
        });
      });

      await waitFor(() => {
        expect(screen.getByText(/120 pesajes/)).toBeInTheDocument();
      });
    });

    it("no envía consulta vacía", async () => {
      render(AdminAgente);
      await waitForReady();

      const sendBtn = screen.getByRole("button", { name: "Enviar" });
      expect(sendBtn).toBeDisabled();
    });
  });

  // ─── T19: test_admin_agente_loading_state (R11) ───────────────
  describe("estado de carga (R11)", () => {
    it("muestra 'Pensando...' mientras el agente procesa", async () => {
      // Make post never resolve to test loading state
      api.post.mockReturnValue(new Promise(() => {}));
      render(AdminAgente);
      await waitForReady();

      const textarea = screen.getByPlaceholderText("Escriba su consulta aquí...");
      fireEvent.input(textarea, { target: { value: "Hola" } });

      const sendBtn = screen.getByRole("button", { name: "Enviar" });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(screen.getByText("Pensando...")).toBeInTheDocument();
      });
    });

    it("deshabilita input y boton durante carga", async () => {
      api.post.mockReturnValue(new Promise(() => {}));
      render(AdminAgente);
      await waitForReady();

      const textarea = screen.getByPlaceholderText("Escriba su consulta aquí...");
      fireEvent.input(textarea, { target: { value: "Hola" } });

      const sendBtn = screen.getByRole("button", { name: "Enviar" });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(textarea).toBeDisabled();
        expect(sendBtn).toBeDisabled();
      });
    });
  });

  // ─── R12: error en consulta ────────────────────────────────────
  describe("error en consulta (R12)", () => {
    it("muestra mensaje de error si POST falla", async () => {
      api.post.mockRejectedValue(new Error("Error de conexión"));
      render(AdminAgente);
      await waitForReady();

      const textarea = screen.getByPlaceholderText("Escriba su consulta aquí...");
      fireEvent.input(textarea, { target: { value: "consulta de prueba" } });

      const sendBtn = screen.getByRole("button", { name: "Enviar" });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(screen.getByText(/Error de conexión/)).toBeInTheDocument();
      });
    });

    it("muestra boton Reintentar al fallar", async () => {
      api.post.mockRejectedValue(new Error("timeout"));
      render(AdminAgente);
      await waitForReady();

      const textarea = screen.getByPlaceholderText("Escriba su consulta aquí...");
      fireEvent.input(textarea, { target: { value: "test" } });

      const sendBtn = screen.getByRole("button", { name: "Enviar" });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(screen.getByText("Reintentar")).toBeInTheDocument();
      });
    });
  });
});
