/**
 * Tests para Corporate Branding (F43) — Identidad Corporativa Mayagüez.
 * Cubre: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17.
 */
import { vi, describe, it, expect, afterEach } from "vitest";
import { render, cleanup, fireEvent, waitFor } from "@testing-library/svelte";
import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import AuthModal from "../AuthModal.svelte";
import KioskLayout from "../KioskLayout.svelte";
import AdminLayout from "../AdminLayout.svelte";
import AboutModal from "../AboutModal.svelte";

// Read CSS and HTML source files for content verification
const __dirname = dirname(fileURLToPath(import.meta.url));
const appCssPath = resolve(__dirname, "../../app.css");
const indexPath = resolve(__dirname, "../../../index.html");
const faviconPath = resolve(__dirname, "../../../public/favicon.png");
const adminLayoutPath = resolve(__dirname, "../AdminLayout.svelte");
const appCssContent = readFileSync(appCssPath, "utf-8");
const indexHtmlContent = readFileSync(indexPath, "utf-8");
const adminLayoutContent = readFileSync(adminLayoutPath, "utf-8");

// ===================== MOCKS =====================

vi.mock("../../stores/auth.js", () => ({
  authStore: {
    subscribe: vi.fn((cb) => {
      cb({
        token: "fake-token",
        role: "admin",
        username: "admin",
        isAuthenticated: true,
        isOperator: false,
        isAdmin: true,
        jwtPayload: { sub: "admin", role: "admin" },
      });
      return () => {};
    }),
    get token() { return "fake-token"; },
    get role() { return "admin"; },
    get username() { return "admin"; },
    get isAuthenticated() { return true; },
    get isOperator() { return false; },
    get isAdmin() { return true; },
    get jwtPayload() { return { sub: "admin", role: "admin" }; },
    login: vi.fn(),
    logout: vi.fn(),
    decodeJwtPayload: vi.fn(() => ({ sub: "admin", role: "admin" })),
    getSessionTimeout: vi.fn(() => 30),
  },
}));

vi.mock("../../stores/emergency.js", () => ({
  emergencyStore: {
    subscribe: vi.fn((cb) => {
      cb({ active: false });
      return () => {};
    }),
    get isEmergencyMode() { return false; },
    set isEmergencyMode(_v) {},
  },
}));

vi.mock("../../lib/api.js", () => ({
  api: {
    get: vi.fn().mockResolvedValue({ active: false }),
    post: vi.fn().mockResolvedValue({ access_token: "t", role: "admin" }),
    put: vi.fn(),
    del: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  },
  buildQuery: vi.fn(() => ""),
}));

vi.mock("../../lib/router.js", () => ({
  navigate: vi.fn(),
  getRoute: vi.fn(() => "/admin"),
  isRoute: vi.fn(() => true),
  onRouteChange: vi.fn(),
  replaceRoute: vi.fn(),
  router: {
    subscribe: vi.fn((cb) => {
      cb("/admin");
      return () => {};
    }),
  },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// ===================== T21 — CSS Custom Properties (R1, R2, R3) =====================
// Verificamos el contenido del archivo app.css directamente (jsdom no resuelve
// custom properties via getComputedStyle ni expone :root en styleSheets).

describe("Corporate Branding — T21: CSS Custom Properties (R1, R2, R3)", () => {
  it("R1: :root declara --color-primary como #FDB814", () => {
    expect(appCssContent).toMatch(/--color-primary\s*:\s*#FDB814/);
  });

  it("R1: :root declara --color-accent como #32373c (fondo oscuro)", () => {
    expect(appCssContent).toMatch(/--color-accent\s*:\s*#32373c/);
  });

  it("R1: :root declara --color-gray como #f4f4f4", () => {
    expect(appCssContent).toMatch(/--color-gray\s*:\s*#f4f4f4/);
  });

  it("R1: :root declara --color-gray-dark como #878787", () => {
    expect(appCssContent).toMatch(/--color-gray-dark\s*:\s*#878787/);
  });

  it("R1: :root declara --color-gray-darker como #646464", () => {
    expect(appCssContent).toMatch(/--color-gray-darker\s*:\s*#646464/);
  });

  it("R2: --accent funcional se reasigna a var(--color-primary)", () => {
    // --accent is defined as var(--color-primary)
    expect(appCssContent).toMatch(/--accent\s*:\s*var\(--color-primary\)/);
  });

  it("R2: --accent-hover funcional se reasigna a var(--color-primary-hover)", () => {
    expect(appCssContent).toMatch(/--accent-hover\s*:\s*var\(--color-primary-hover\)/);
  });

  it("R2: --bg-primary se reasigna a #32373c (o var(--color-accent))", () => {
    const ok = /--bg-primary\s*:\s*#32373c/.test(appCssContent) ||
               /--bg-primary\s*:\s*var\(--color-accent\)/.test(appCssContent);
    expect(ok).toBe(true);
  });

  it("R2: --text-primary se reasigna a #f4f4f4", () => {
    expect(appCssContent).toMatch(/--text-primary\s*:\s*#f4f4f4/);
  });

  it("R3: --success NO fue alterado (sigue siendo #51cf66)", () => {
    expect(appCssContent).toMatch(/--success\s*:\s*#51cf66/);
  });

  it("R3: --error NO fue alterado (sigue siendo #ff6b6b)", () => {
    expect(appCssContent).toMatch(/--error\s*:\s*#ff6b6b/);
  });

  it("R3: --warning NO fue alterado (sigue siendo #ffd43b)", () => {
    expect(appCssContent).toMatch(/--warning\s*:\s*#ffd43b/);
  });
});

// ===================== T22 — Logo in Views (R6, R7, R8, R10, R13) =====================

describe("Corporate Branding — T22: Logo corporativo en vistas (R6, R7, R8, R10, R13)", () => {
  it("R6: AuthModal muestra logo con src /static/logo-mayaguez.png", () => {
    render(AuthModal);
    const logo = document.querySelector(".auth-logo");
    expect(logo).not.toBeNull();
    expect(logo.getAttribute("src")).toBe("/static/logo-mayaguez.png");
  });

  it("R7: KioskLayout usa logo en header-center (reemplaza texto Sip-Edge)", () => {
    render(KioskLayout);
    const logo = document.querySelector(".header-center .app-name");
    expect(logo).not.toBeNull();
    expect(logo.tagName).toBe("IMG");
    expect(logo.getAttribute("src")).toBe("/static/logo-mayaguez.png");
  });

  it("R8/R13: AdminLayout muestra logo 64x64 en sidebar-header", () => {
    render(AdminLayout);
    const logo = document.querySelector(".sidebar-logo");
    expect(logo).not.toBeNull();
    expect(logo.getAttribute("src")).toBe("/static/logo-mayaguez.png");
    expect(logo.getAttribute("width")).toBe("64");
    expect(logo.getAttribute("height")).toBe("64");
    const title = document.querySelector(".sidebar-title");
    expect(title).not.toBeNull();
    expect(title.textContent).toBe("SIP-Edge Admin");
  });

  it("R10: AboutModal usa logo corporativo 64x64 (no favicon placeholder)", () => {
    render(AboutModal, { props: { show: true } });
    const logo = document.querySelector(".about-logo img");
    expect(logo).not.toBeNull();
    expect(logo.getAttribute("src")).toBe("/static/logo-mayaguez.png");
    expect(logo.getAttribute("width")).toBe("64");
    expect(logo.getAttribute("height")).toBe("64");
  });

  it("R9/R10: AboutModal muestra información corporativa completa", () => {
    render(AboutModal, { props: { show: true } });
    // Razón social (R9)
    expect(document.querySelector(".about-card h2")?.textContent).toBe("Ingenio Mayagüez S.A.");
    // Versión del sistema (R9)
    expect(document.querySelector(".about-subtitle")?.textContent).toBe("SIP-Edge v1.0");
    // Copyright (R9)
    expect(document.querySelector(".about-copy")?.textContent?.trim()).toBe(
      "© 2026 Ingenio Mayagüez S.A. Todos los derechos reservados."
    );
    // Disclaimer legal (R9)
    const disclaimer = document.querySelector(".about-disclaimer")?.textContent?.trim() || "";
    expect(disclaimer).toContain("Sistema de uso exclusivo");
    expect(disclaimer).toContain("Ingenio Mayagüez S.A.");
  });
});

// ===================== T23 — Typography Montserrat (R4, R5) =====================

describe("Corporate Branding — T23: Tipografía Montserrat (R4, R5)", () => {
  it("R4: index.html incluye Google Fonts Montserrat (weights 300,400,600,700)", () => {
    expect(indexHtmlContent).toMatch(/fonts\.googleapis\.com\/css2\?family=Montserrat:wght@300;400;600;700/);
  });

  it("R5: app.css body usa Montserrat como font-family principal", () => {
    // Check the body rule in app.css
    const bodyMatch = appCssContent.match(/body\s*\{[^}]*font-family\s*:\s*([^;}]+)/);
    expect(bodyMatch).not.toBeNull();
    expect(bodyMatch[1]).toContain("Montserrat");
  });
});

// ===================== T16/R17 — Fix ⓘ visibility in AdminLayout =====================

describe("Corporate Branding — T16/R17: ⓘ visible en AdminLayout", () => {
  it("R17: botón ⓘ (sidebar-about) existe en AdminLayout", () => {
    render(AdminLayout);
    const aboutBtn = document.querySelector(".sidebar-about");
    expect(aboutBtn).not.toBeNull();
    expect(aboutBtn.textContent).toBe("ⓘ");
  });

  it("R17: sidebar-about está dentro del flujo de header-right", () => {
    render(AdminLayout);
    const headerRight = document.querySelector(".header-right");
    expect(headerRight).not.toBeNull();
    const aboutBtn = headerRight.querySelector(".sidebar-about");
    expect(aboutBtn).not.toBeNull();
  });

  it("R17: al clickear ⓘ se abre AboutModal", async () => {
    render(AdminLayout);
    const aboutBtn = document.querySelector(".sidebar-about");
    expect(aboutBtn).not.toBeNull();
    await fireEvent.click(aboutBtn);
    await waitFor(() => {
      const overlay = document.querySelector(".about-overlay");
      expect(overlay).not.toBeNull();
    }, { timeout: 2000 });
  });
});

// ===================== T24 — Favicon (R11) =====================

describe("Corporate Branding — T24: Favicon corporativo (R11)", () => {
  it("R11: frontend/public/favicon.png existe en disco", () => {
    expect(existsSync(faviconPath)).toBe(true);
  });

  it("R11: favicon.png es un archivo PNG válido", () => {
    const buf = readFileSync(faviconPath);
    // PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
    const pngSignature = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
    expect(buf.slice(0, 8).equals(pngSignature)).toBe(true);
  });

  it("R11: favicon.png tiene dimensiones de ícono (16–64px)", () => {
    const buf = readFileSync(faviconPath);
    // IHDR chunk: width at bytes 16–19, height at bytes 20–23 (big-endian)
    const width = buf.readUInt32BE(16);
    const height = buf.readUInt32BE(20);
    expect(width).toBeGreaterThanOrEqual(16);
    expect(width).toBeLessThanOrEqual(64);
    expect(height).toBeGreaterThanOrEqual(16);
    expect(height).toBeLessThanOrEqual(64);
    // Favicon should be square
    expect(width).toBe(height);
  });
});

// ===================== T25 — CSS Rule Verification (R12, R14, R15, R16) =====================

describe("Corporate Branding — T25: Reglas CSS usan paleta corporativa (R12, R14, R15, R16)", () => {
  it("R12: .sidebar en AdminLayout.svelte usa background: var(--color-accent)", () => {
    expect(adminLayoutContent).toMatch(
      /\.sidebar\s*\{[^}]*background\s*:\s*var\(--color-accent\)/
    );
  });

  it("R12: .sidebar-link.active en AdminLayout.svelte usa background: var(--color-primary)", () => {
    expect(adminLayoutContent).toMatch(
      /\.sidebar-link\.active\s*\{[^}]*background\s*:\s*var\(--color-primary\)/
    );
  });

  it("R13: .sidebar-title en AdminLayout.svelte usa color: var(--color-primary)", () => {
    expect(adminLayoutContent).toMatch(
      /\.sidebar-title\s*\{[^}]*color\s*:\s*var\(--color-primary\)/
    );
  });

  it("R14: .btn-primary en app.css usa background: var(--color-primary)", () => {
    expect(appCssContent).toMatch(
      /\.btn-primary\s*\{[^}]*background\s*:\s*var\(--color-primary\)/
    );
  });

  it("R15: input:focus en app.css usa border-color: var(--color-primary)", () => {
    expect(appCssContent).toMatch(
      /input:focus[^{]*\{[^}]*border-color\s*:\s*var\(--color-primary\)/
    );
  });

  it("R16: a en app.css usa color: var(--accent)", () => {
    expect(appCssContent).toMatch(
      /^a\s*\{[^}]*color\s*:\s*var\(--accent\)/m
    );
  });
});
