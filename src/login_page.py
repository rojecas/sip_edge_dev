"""Login page for SIP-Edge with password reset via SMS."""

LOGIN_PAGE_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SIP-Edge - Login</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e; color: #e0e0e0;
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh;
}
.container {
  background: #16213e; padding: 2rem; border-radius: 12px;
  width: 100%; max-width: 400px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
h1 { text-align: center; margin-bottom: 1.5rem; color: #0f3460; }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: 0.25rem; font-size: 0.9rem; color: #a0a0b0; }
input {
  width: 100%; padding: 0.75rem; border: 1px solid #333;
  border-radius: 6px; background: #0f3460; color: #e0e0e0;
  font-size: 1rem;
}
input:focus { outline: none; border-color: #e94560; }
button {
  width: 100%; padding: 0.75rem; border: none; border-radius: 6px;
  background: #e94560; color: white; font-size: 1rem; font-weight: bold;
  cursor: pointer; margin-top: 0.5rem;
}
button:hover { background: #c73652; }
button:disabled { background: #666; cursor: not-allowed; }
.error { color: #ff6b6b; font-size: 0.85rem; margin-top: 0.5rem; display: none; }
.success { color: #51cf66; font-size: 0.85rem; margin-top: 0.5rem; display: none; }
.link { text-align: center; margin-top: 1rem; }
.link a { color: #e94560; cursor: pointer; text-decoration: underline; font-size: 0.9rem; }

/* Modal */
.modal-overlay {
  display: none; position: fixed; top: 0; left: 0;
  width: 100%; height: 100%; background: rgba(0,0,0,0.7);
  justify-content: center; align-items: center; z-index: 1000;
}
.modal-overlay.active { display: flex; }
.modal {
  background: #16213e; padding: 2rem; border-radius: 12px;
  width: 100%; max-width: 380px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.modal h2 { margin-bottom: 1rem; color: #e0e0e0; text-align: center; }
.modal .close {
  float: right; background: none; border: none; color: #a0a0b0;
  font-size: 1.5rem; cursor: pointer; margin: -1rem -0.5rem 0 0; padding: 0;
  width: auto;
}
.modal .close:hover { color: #e94560; background: none; }
.pin-input { letter-spacing: 0.5rem; text-align: center; font-size: 1.5rem; }
</style>
</head>
<body>
<div class="container">
  <h1>SIP-Edge</h1>
  <div id="login-form">
    <div class="form-group">
      <label for="username">Usuario</label>
      <input type="text" id="username" placeholder="Nombre de usuario" autocomplete="username">
    </div>
    <div class="form-group">
      <label for="password">Contrasena</label>
      <input type="password" id="password" placeholder="Contrasena" autocomplete="current-password">
    </div>
    <div id="login-error" class="error"></div>
    <button onclick="doLogin()">Iniciar Sesion</button>
    <div class="link">
      <a id="forgot-link" onclick="showPinModal()">Olvido su contrasena</a>
    </div>
  </div>
  <div id="login-success" class="success"></div>
</div>

<!-- Modal 1: Verificar PIN -->
<div id="pin-modal" class="modal-overlay">
  <div class="modal">
    <button class="close" onclick="hideModals()">&times;</button>
    <h2>Restablecer Contrasena</h2>
    <p style="margin-bottom:1rem;font-size:0.85rem;color:#a0a0b0;">
      Ingrese su usuario y el PIN de 4 digitos que recibio por SMS.
    </p>
    <div class="form-group">
      <label for="pin-username">Usuario</label>
      <input type="text" id="pin-username" placeholder="Nombre de usuario">
    </div>
    <div class="form-group">
      <label for="pin-code">PIN (4 digitos)</label>
      <input type="text" id="pin-code" class="pin-input" maxlength="4"
             inputmode="numeric" pattern="[0-9]*" placeholder="0000">
    </div>
    <div id="pin-error" class="error"></div>
    <button id="verify-btn" onclick="verifyPin()">Verificar PIN</button>
  </div>
</div>

<!-- Modal 2: Cambiar Contrasena -->
<div id="password-modal" class="modal-overlay">
  <div class="modal">
    <h2>Nueva Contrasena</h2>
    <div class="form-group">
      <label for="new-password">Nueva contrasena</label>
      <input type="password" id="new-password" placeholder="Nueva contrasena">
    </div>
    <div class="form-group">
      <label for="confirm-password">Confirmar contrasena</label>
      <input type="password" id="confirm-password" placeholder="Repita la contrasena">
    </div>
    <div id="password-error" class="error"></div>
    <div id="password-success" class="success"></div>
    <button id="change-btn" onclick="completeReset()">Cambiar Contrasena</button>
  </div>
</div>

<script>
let resetToken = '';

function showError(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.style.display = 'block';
}

function clearErrors() {
  document.querySelectorAll('.error').forEach(e => e.style.display = 'none');
  document.querySelectorAll('.success').forEach(e => e.style.display = 'none');
}

function hideModals() {
  document.getElementById('pin-modal').classList.remove('active');
  document.getElementById('password-modal').classList.remove('active');
  clearErrors();
}

async function doLogin() {
  clearErrors();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  try {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password}),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError('login-error', data.detail || 'Error de inicio de sesion');
      return;
    }
    document.getElementById('login-success').textContent =
      'Inicio de sesion exitoso. Token: ' + data.access_token.substring(0, 20) + '...';
    document.getElementById('login-success').style.display = 'block';
  } catch (e) {
    showError('login-error', 'Error de conexion');
  }
}

function showPinModal() {
  clearErrors();
  document.getElementById('pin-modal').classList.add('active');
}

async function verifyPin() {
  clearErrors();
  const username = document.getElementById('pin-username').value;
  const pin = document.getElementById('pin-code').value;

  if (pin.length !== 4 || !/^\d{4}$/.test(pin)) {
    showError('pin-error', 'El PIN debe ser de 4 digitos numericos');
    return;
  }

  try {
    const resp = await fetch('/api/auth/verify-reset-pin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, pin}),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError('pin-error', data.detail || 'PIN invalido');
      return;
    }
    resetToken = data.reset_token;
    // Transicionar a modal de cambio de contrasena
    document.getElementById('pin-modal').classList.remove('active');
    document.getElementById('password-modal').classList.add('active');
  } catch (e) {
    showError('pin-error', 'Error de conexion');
  }
}

async function completeReset() {
  clearErrors();
  const newPassword = document.getElementById('new-password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  if (!newPassword || !confirmPassword) {
    showError('password-error', 'Ambos campos son obligatorios');
    return;
  }

  try {
    const resp = await fetch('/api/auth/complete-reset', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        reset_token: resetToken,
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError('password-error', data.detail || 'Error al cambiar contrasena');
      return;
    }
    showError('password-success', data.message || 'Contrasena actualizada exitosamente');
    document.getElementById('password-success').style.display = 'block';
    // Permitir cerrar despues de 2 segundos
    setTimeout(() => {
      hideModals();
    }, 2000);
  } catch (e) {
    showError('password-error', 'Error de conexion');
  }
}
</script>
</body>
</html>"""
