/**
 * Tests para UserFormModal.svelte — Modal crear/editar usuario.
 * Cubre: R2, R4.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/svelte";
import UserFormModal from "../UserFormModal.svelte";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("UserFormModal — Create mode (R2)", () => {
  it("muestra campos: Usuario, Contrasena, Nombre Completo, Documento, Rol", () => {
    render(UserFormModal, {
      props: { show: true, mode: "create" },
    });
    expect(screen.getByPlaceholderText("Nombre de usuario")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Contraseña")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Nombre completo")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Documento (opcional)")).toBeInTheDocument();
    // Rol select está presente
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("muestra titulo 'Nuevo Usuario' en modo create", () => {
    render(UserFormModal, {
      props: { show: true, mode: "create" },
    });
    expect(screen.getByText("Nuevo Usuario")).toBeInTheDocument();
  });

  it("tiene botones Guardar y Cancelar", () => {
    render(UserFormModal, {
      props: { show: true, mode: "create" },
    });
    expect(screen.getByRole("button", { name: "Guardar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
  });

  it("valida que Usuario sea requerido en create", async () => {
    render(UserFormModal, {
      props: { show: true, mode: "create" },
    });
    // Fill only full_name to pass that check, leave username and password empty
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(nombreInput, { target: { value: "Juan" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(screen.getByText("El usuario es requerido.")).toBeInTheDocument();
  });

  it("valida que Contrasena sea requerida en create", async () => {
    render(UserFormModal, {
      props: { show: true, mode: "create" },
    });
    const userInput = screen.getByPlaceholderText("Nombre de usuario");
    await fireEvent.input(userInput, { target: { value: "juan" } });
    // Leave password empty
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    // After username passes, password check fails or full_name check fails first
    // Validation order: username → password → full_name
    expect(screen.getByText("La contraseña es requerida.")).toBeInTheDocument();
  });

  it("valida que Nombre Completo sea requerido", async () => {
    render(UserFormModal, {
      props: { show: true, mode: "create" },
    });
    const userInput = screen.getByPlaceholderText("Nombre de usuario");
    const passInput = screen.getByPlaceholderText("Contraseña");
    await fireEvent.input(userInput, { target: { value: "juan" } });
    await fireEvent.input(passInput, { target: { value: "pass123" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(screen.getByText("El nombre completo es requerido.")).toBeInTheDocument();
  });

  it("llama onSave con payload al guardar en create", async () => {
    const onSave = vi.fn();
    render(UserFormModal, {
      props: { show: true, mode: "create", onSave },
    });
    const userInput = screen.getByPlaceholderText("Nombre de usuario");
    const passInput = screen.getByPlaceholderText("Contraseña");
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    await fireEvent.input(userInput, { target: { value: "juan" } });
    await fireEvent.input(passInput, { target: { value: "pass123" } });
    await fireEvent.input(nombreInput, { target: { value: "Juan Perez" } });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        username: "juan",
        password: "pass123",
        full_name: "Juan Perez",
        role: "operator",
        document: null,
      })
    );
  });

  it("llama onClose al pulsar Cancelar", async () => {
    const onClose = vi.fn();
    render(UserFormModal, {
      props: { show: true, mode: "create", onClose },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("no renderiza cuando show es false", () => {
    const { container } = render(UserFormModal, {
      props: { show: false, mode: "create" },
    });
    expect(container.querySelector(".modal-overlay")).toBeNull();
  });
});

describe("UserFormModal — Edit mode (R4)", () => {
  const mockUser = {
    id: 1,
    username: "juanperez",
    full_name: "Juan Perez",
    document: "12345678",
    role: "operator",
    is_active: true,
  };

  it("muestra titulo 'Editar Usuario' en modo edit", () => {
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: mockUser },
    });
    expect(screen.getByText("Editar Usuario")).toBeInTheDocument();
  });

  it("pre-puebla campos con datos del usuario (R4)", () => {
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: mockUser },
    });
    const nombreInput = screen.getByPlaceholderText("Nombre completo");
    const docInput = screen.getByPlaceholderText("Documento (opcional)");
    expect(nombreInput.value).toBe("Juan Perez");
    expect(docInput.value).toBe("12345678");
  });

  it("muestra username como texto informativo en modo edit (M4)", () => {
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: mockUser },
    });
    // El username debe mostrarse como texto informativo no editable
    expect(screen.getByText("juanperez")).toBeInTheDocument();
    expect(screen.getByText("Usuario:")).toBeInTheDocument();
  });

  it("muestra '—' si el usuario no tiene username", () => {
    const userNoUsername = { ...mockUser, username: "" };
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: userNoUsername },
    });
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("muestra checkbox Activo en modo edit", () => {
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: mockUser },
    });
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
    expect(screen.getByText("Activo")).toBeInTheDocument();
  });

  it("muestra campo Nueva Contrasena (opcional) en modo edit", () => {
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: mockUser },
    });
    expect(screen.getByPlaceholderText("Dejar vacío para no cambiar")).toBeInTheDocument();
  });

  it("llama onSave con payload al guardar en edit", async () => {
    const onSave = vi.fn();
    render(UserFormModal, {
      props: { show: true, mode: "edit", user: mockUser, onSave },
    });
    await fireEvent.click(screen.getByRole("button", { name: "Guardar" }));
    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        full_name: "Juan Perez",
        document: "12345678",
        role: "operator",
        is_active: true,
      })
    );
  });

  it("muestra mensaje de error si se pasa via prop", () => {
    render(UserFormModal, {
      props: {
        show: true,
        mode: "edit",
        user: mockUser,
        error: "Usuario no encontrado.",
      },
    });
    expect(screen.getByText("Usuario no encontrado.")).toBeInTheDocument();
  });
});
