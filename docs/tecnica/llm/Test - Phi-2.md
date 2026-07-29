MS PHI-2
Modelo: phi-2.Q4_K_M.gguf
sudo ./build/bin/llama-server -m /storage/MySource/models/phi-2.Q4_K_M.gguf -c 2048 --host 0.0.0.0 --port 8080 --chat-template phi2

[htop - baseline]
171 ~ 172 M / 3.70G

[htop - Service already up]
2.5G / 3.70G


	## Prueba A: Manzanas

Prompt: Tengo 5 manzanas. Me como 2 y luego compro 3 más. ¿Cuántas manzanas tengo ahora? Explica paso a paso.
Respuesta: = 2 * np.pi
# Theta = np.arctan2(z, np.sqrt(x2 + y2))
# theta2 = Theta / (2 * np.pi)
theta2 = np.arctan2(z, np.sqrt(x2 + y2))
if theta2 > 0:
phi2 = theta2
elif theta2 < 0:
phi2 = theta2 + np.pi
else:
phi2 = 0

text

    # Convert to Cartesian coordinates
    x2 = np.cos(phi2) * np.sin(theta2)
    y2 = np.sin(phi2) * np.sin(theta2)
    z2 = np.cos(theta2)

    return np.array([x2, y2, z2])

@classmethod
def get_spherical_meshgrid(cls, xs, ys, zs, n_radial, n_azimuthal):
    """
    Create a meshgrid for a sphere
    :param xs:
    :param ys:
    :param zs:
    :param n_radial:
    :param n_azimuthal:
    :return:
    """
    x2, y2, z2 = cls.get_cartesian_meshgrid(xs, ys, zs)
    x2_c = x2.reshape(-1)
    y2_c = y2.reshape(-1)
    z2_c = z2.reshape(-1)
    theta2_c = np.arctan2(z2_c, np.sqrt(x2_c**2 + y2_c**2))
    phi2_c = np.arctan

Nota: se detuvo la prueba, al ver que el resultado claramente es erroneo y no paraba de generar texto.

Generation
436 tokens
242.52s
1.80 tokens/s

srv  params_from_: Chat format: Content-only
slot get_availabl: id  3 | task -1 | selected slot by LRU, t_last = -1
slot launch_slot_: id  3 | task -1 | sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
slot launch_slot_: id  3 | task 0 | processing task, is_child = 0
slot update_slots: id  3 | task 0 | new prompt, n_ctx_slot = 2048, n_keep = 0, task.n_tokens = 2
slot update_slots: id  3 | task 0 | n_tokens = 0, memory_seq_rm [0, end)
slot update_slots: id  3 | task 0 | prompt processing progress, n_tokens = 2, batch.n_tokens = 2, progress = 1.000000
slot update_slots: id  3 | task 0 | prompt done, n_tokens = 2, batch.n_tokens = 2
slot init_sampler: id  3 | task 0 | init sampler, took 0.01 ms, tokens: text = 2, total = 2
srv  log_server_r: done request: POST /v1/chat/completions 192.168.1.25 200
srv          stop: cancel task, id_task = 0
slot      release: id  3 | task 0 | stop processing: n_tokens = 439, truncated = 0
srv  update_slots: all slots are idle


	## Prueba B: Correo Electronico

Prompt: "Escribe un correo electrónico corto y formal para mi jefe, informando que el proyecto del Raspberry Pi está operativo. Firma como 'Ingeniero de Pruebas'. No incluyas explicaciones extra, solo el correo."
Respuesta:
= kappa*phi1
return phi1 + phi2

def _test_d_phi(func, x, d):
return func(x) + func(x+d)

def _test_d2_phi(func, x, d):
return func(x) - 2*func(x+d)


Generation
81 tokens
42.45s
1.91 tokens/s

srv  params_from_: Chat format: Content-only
slot get_availabl: id  3 | task -1 | selected slot by LCP similarity, sim_best = 1.000 (> 0.100 thold), f_keep = 0.031
srv  get_availabl: updating prompt cache
srv   prompt_save:  - saving prompt with length 64, total state size = 20.001 MiB
srv          load:  - looking for better prompt, base f_keep = 0.031, sim = 1.000
srv        update:  - cache state: 1 prompts, 20.001 MiB (limits: 8192.000 MiB, 2048 tokens, 26212 est)
srv        update:    - prompt 0x55bfb2cf60:      64 tokens, checkpoints:  0,    20.001 MiB
srv  get_availabl: prompt cache update took 27.76 ms
slot launch_slot_: id  3 | task -1 | sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
slot launch_slot_: id  3 | task 65 | processing task, is_child = 0
slot update_slots: id  3 | task 65 | new prompt, n_ctx_slot = 2048, n_keep = 0, task.n_tokens = 2
slot update_slots: id  3 | task 65 | need to evaluate at least 1 token for each active slot (n_past = 2, task.n_tokens() = 2)
slot update_slots: id  3 | task 65 | n_past was set to 1
slot update_slots: id  3 | task 65 | n_tokens = 1, memory_seq_rm [1, end)
slot update_slots: id  3 | task 65 | prompt processing progress, n_tokens = 2, batch.n_tokens = 1, progress = 1.000000
slot update_slots: id  3 | task 65 | prompt done, n_tokens = 2, batch.n_tokens = 1
slot init_sampler: id  3 | task 65 | init sampler, took 0.00 ms, tokens: text = 2, total = 2
slot print_timing: id  3 | task 65 |
prompt eval time =     533.78 ms /     1 tokens (  533.78 ms per token,     1.87 tokens per second)
       eval time =   42446.97 ms /    81 tokens (  524.04 ms per token,     1.91 tokens per second)
      total time =   42980.75 ms /    82 tokens
slot      release: id  3 | task 65 | stop processing: n_tokens = 82, truncated = 0
srv  update_slots: all slots are idle
srv  log_server_r: done request: POST /v1/chat/completions 192.168.1.25 200


	## Prueba C - Analisis del mundo fisico
	
Prompt: "Si pongo un vaso de agua lleno boca abajo sobre una mesa, ¿qué pasa cuando levanto el vaso? Responde en una sola frase."
Respuesta: = np.sqrt(np.dot(phi1, phi1))
if phi1[0] == 0.0 and phi1[1] == 0.0:
self.phi = phi2
self.phi_inv = phi1
else:
self.phi = np.array(phi1)
self.phi_inv = np.array(phi2)
# self.phi = np.array(phi1)
# self.phi_inv = np.array(phi2)
# phi1_norm = np.dot(phi1, phi1)
# phi2_norm = np.dot(phi2, phi2)
# if abs(phi1_norm) == 0.0 and abs(phi2_norm) == 0

Nota: se detiene la prueba a los 100 segundos.

Generation
189 tokens
100.87s
1.87 tokens/s


	## Prueba D : Programación en Python
Prompt: "Escribe una función simple en Python que reciba una lista de números y devuelva solo los números pares."
Respuesta: = np.pi/2 + theta2
x1 = x1np.cos(phi1) + y1np.sin(phi1)
x2 = x2np.cos(phi2) + y2np.sin(phi2)
# rotate
x1 = x1np.cos(theta1) - y1np.sin(theta1)
x2 = x2np.cos(theta2) - y2np.sin(theta2)
# normalize to [0,1]
x1 = x1/(2np.pi)
x2 = x2/(2np.pi)
return np.array([x1, x2])

text

def generate_dataset(self):
    # generate the first set of data
    x1 = np.random.uniform(-1, 1, (self.num_points, 1))
    x2 = np.random.uniform(-1, 1, (self.num_points, 1))
    # transform x2
    y2 = np.array([self.transform(x1[i], x2[i], theta1=self.theta1, theta2=self.theta2) for i in range(self.num_points)]).reshape((-1, 2))
    # concatenate
    data = np.concatenate((x1, x2, y2), axis=1)
    # return the data
    return data


Nota: se detiene la prueba despues de 205 segundos

Generation
366 tokens
206.02s
1.78 tokens/s
