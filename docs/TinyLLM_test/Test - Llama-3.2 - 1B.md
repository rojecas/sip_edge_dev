META - Llama 3.2 1B
Modelo: llama-3.2-1b-instruct-q4_k_m.gguf
sudo ./build/bin/llama-server -m /storage/MySource/models/llama-3.2-1b-instruct-q4_k_m.gguf -c 2048 --host 0.0.0.0 --port 8080

[htop - baseline]
171 ~ 172 M / 3.70G

[htop - Service already up]
1.06G / 3.70G

Llama 3.2 - 1B (El velocista)

	## Prueba A: Manzanas

Prompt: Tengo 5 manzanas. Me como 2 y luego compro 3 más. ¿Cuántas manzanas tengo ahora? Explica paso a paso.

Respuesta: {
"nombre": "tengo_manzanas",
"parametros": "5, 2, 3"
}

Paso 1: Me comí 2 manzanas, por lo que tengo 5 - 2 = 3 manzanas.

Paso 2: Me compré 3 más manzanas, por lo que ahora tengo 3 + 3 = 6 manzanas.

Paso 3: La cantidad de manzanas que tengo ahora es de 6.

Generation
108 tokens
26.65s
4.05 tokens/s


srv  update_slots: all slots are idle
srv  log_server_r: done request: GET / 192.168.1.25 200
srv  params_from_: Chat format: Content-only
slot get_availabl: id  3 | task -1 | selected slot by LRU, t_last = -1
slot launch_slot_: id  3 | task -1 | sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
slot launch_slot_: id  3 | task 0 | processing task, is_child = 0
slot update_slots: id  3 | task 0 | new prompt, n_ctx_slot = 2048, n_keep = 0, task.n_tokens = 124
slot update_slots: id  3 | task 0 | n_tokens = 0, memory_seq_rm [0, end)
slot update_slots: id  3 | task 0 | prompt processing progress, n_tokens = 124, batch.n_tokens = 124, progress = 1.000000
slot update_slots: id  3 | task 0 | prompt done, n_tokens = 124, batch.n_tokens = 124
slot init_sampler: id  3 | task 0 | init sampler, took 0.18 ms, tokens: text = 124, total = 124
slot print_timing: id  3 | task 0 |
prompt eval time =   11672.60 ms /   124 tokens (   94.13 ms per token,    10.62 tokens per second)
       eval time =   26652.03 ms /   108 tokens (  246.78 ms per token,     4.05 tokens per second)
      total time =   38324.63 ms /   232 tokens
slot      release: id  3 | task 0 | stop processing: n_tokens = 231, truncated = 0
srv  update_slots: all slots are idle
srv  log_server_r: done request: POST /v1/chat/completions 192.168.1.15 200


	## Prueba B: Correo Electronico

Prompt: "Escribe un correo electrónico corto y formal para mi jefe, informando que el proyecto del Raspberry Pi está operativo. Firma como 'Ingeniero de Pruebas'. No incluyas explicaciones extra, solo el correo."
Respuesta:{
"correo": "Ingeniero de Pruebas"
"datos": "El proyecto del Raspberry Pi está operativo. Los detalles serán compartidos en una reunión."
}

Generation
39 tokens
9.61s
4.06 tokens/s

srv  params_from_: Chat format: Content-only
slot get_availabl: id  3 | task -1 | selected slot by LCP similarity, sim_best = 0.436 (> 0.100 thold), f_keep = 0.545
slot launch_slot_: id  3 | task -1 | sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
slot launch_slot_: id  3 | task 109 | processing task, is_child = 0
slot update_slots: id  3 | task 109 | new prompt, n_ctx_slot = 2048, n_keep = 0, task.n_tokens = 289
slot update_slots: id  3 | task 109 | n_tokens = 126, memory_seq_rm [126, end)
slot update_slots: id  3 | task 109 | prompt processing progress, n_tokens = 289, batch.n_tokens = 163, progress = 1.000000
slot update_slots: id  3 | task 109 | prompt done, n_tokens = 289, batch.n_tokens = 163
slot init_sampler: id  3 | task 109 | init sampler, took 0.27 ms, tokens: text = 289, total = 289
slot print_timing: id  3 | task 109 |
prompt eval time =   16025.19 ms /   163 tokens (   98.31 ms per token,    10.17 tokens per second)
       eval time =    9611.33 ms /    39 tokens (  246.44 ms per token,     4.06 tokens per second)
      total time =   25636.51 ms /   202 tokens
srv  log_server_r: done request: POST /v1/chat/completions 192.168.1.25 200
slot      release: id  3 | task 109 | stop processing: n_tokens = 327, truncated = 0
srv  update_slots: all slots are idle



	## Prueba C - Analisis del mundo fisico
	
Prompt: "Si pongo un vaso de agua lleno boca abajo sobre una mesa, ¿qué pasa cuando levanto el vaso? Responde en una sola frase."
Respuesta: "El vaso se endurecerá como plástico y la mesa se dañará, pero no tendrás daño personal."

Generation
29 tokens
7.52s
3.86 tokens/s

Nota: aqui se tardo al rededor de 30 segundos antes de empezar a generar tokens

srv  update_slots: all slots are idle
srv  params_from_: Chat format: Content-only
slot get_availabl: id  3 | task -1 | selected slot by LRU, t_last = -1
slot launch_slot_: id  3 | task -1 | sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
slot launch_slot_: id  3 | task 0 | processing task, is_child = 0
slot update_slots: id  3 | task 0 | new prompt, n_ctx_slot = 2048, n_keep = 0, task.n_tokens = 370
slot update_slots: id  3 | task 0 | n_tokens = 0, memory_seq_rm [0, end)
slot update_slots: id  3 | task 0 | prompt processing progress, n_tokens = 370, batch.n_tokens = 370, progress = 1.000000
slot update_slots: id  3 | task 0 | prompt done, n_tokens = 370, batch.n_tokens = 370
slot init_sampler: id  3 | task 0 | init sampler, took 0.38 ms, tokens: text = 370, total = 370
slot print_timing: id  3 | task 0 |
prompt eval time =   35896.92 ms /   370 tokens (   97.02 ms per token,    10.31 tokens per second)
       eval time =    7517.58 ms /    29 tokens (  259.23 ms per token,     3.86 tokens per second)
      total time =   43414.50 ms /   399 tokens
slot      release: id  3 | task 0 | stop processing: n_tokens = 398, truncated = 0
srv  update_slots: all slots are idle
srv  log_server_r: done request: POST /v1/chat/completions 192.168.1.25 200



	## Prueba D : Programación en Python
Prompt: "Escribe una función simple en Python que reciba una lista de números y devuelva solo los números pares."
Respuesta:
{
"nombre": "pares_numeros",
"parametros": "[]
}

respuesta = [n for n in pares_numeros if n % 2 == 0]
print(respuesta)

Generation
45 tokens
11.43s
3.94 tokens/s

srv  params_from_: Chat format: Content-only
slot get_availabl: id  3 | task -1 | selected slot by LCP similarity, sim_best = 0.921 (> 0.100 thold), f_keep = 1.000
slot launch_slot_: id  3 | task -1 | sampler chain: logits -> ?penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
slot launch_slot_: id  3 | task 30 | processing task, is_child = 0
slot update_slots: id  3 | task 30 | new prompt, n_ctx_slot = 2048, n_keep = 0, task.n_tokens = 432
slot update_slots: id  3 | task 30 | n_tokens = 398, memory_seq_rm [398, end)
slot update_slots: id  3 | task 30 | prompt processing progress, n_tokens = 432, batch.n_tokens = 34, progress = 1.000000
slot update_slots: id  3 | task 30 | prompt done, n_tokens = 432, batch.n_tokens = 34
slot init_sampler: id  3 | task 30 | init sampler, took 0.43 ms, tokens: text = 432, total = 432
slot print_timing: id  3 | task 30 |
prompt eval time =    3731.11 ms /    34 tokens (  109.74 ms per token,     9.11 tokens per second)
       eval time =   11425.93 ms /    45 tokens (  253.91 ms per token,     3.94 tokens per second)
      total time =   15157.04 ms /    79 tokens
slot      release: id  3 | task 30 | stop processing: n_tokens = 476, truncated = 0
srv  update_slots: all slots are idle
srv  log_server_r: done request: POST /v1/chat/completions 192.168.1.25 200
