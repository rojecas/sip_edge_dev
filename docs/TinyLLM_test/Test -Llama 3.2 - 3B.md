Llama 3.2 - 3B
Modelo: llama-3.2-3b-instruct-q4_k_m.gguf
sudo ./build/bin/llama-server -m /storage/MySource/models/llama-3.2-3b-instruct-q4_k_m.gguf -c 2048 --host 0.0.0.0 --port 8080

[htop - baseline]
171 ~ 172 M / 3.70G

[htop - Service already up]
2.41G / 3.70G

	## Prueba A: Manzanas

Prompt: Tengo 5 manzanas. Me como 2 y luego compro 3 más. ¿Cuántas manzanas tengo ahora? Explica paso a paso.
Respuesta: Tengo 5 manzanas. Me como 2 y luego compro 3 más. ¿Cuántas manzanas tengo ahora? Explica paso a paso.

Generation
37 tokens
22.36s
1.65 tokens/s

	## Prueba B: Correo Electronico

Prompt: "Escribe un correo electrónico corto y formal para mi jefe, informando que el proyecto del Raspberry Pi está operativo. Firma como 'Ingeniero de Pruebas'. No incluyas explicaciones extra, solo el correo."
Respuesta: {"name": "send_email", "parameters": {"subject": "Proyecto Raspberry Pi operativo", "body": "Estimado \u0417\u044fmetro, el proyecto del Raspberry Pi se encuentra en funcionamiento.", "to": "jefe@example.com", "cc": "", "from": "ingeniero.de.pruebas@example.com"}}

Generation
74 tokens
47.93s
1.54 tokens/s

	## Prueba C - Analisis del mundo fisico
	
Prompt: "Si pongo un vaso de agua lleno boca abajo sobre una mesa, ¿qué pasa cuando levanto el vaso? Responde en una sola frase."
Respuesta: {"name": "describe_event", "parameters": {"action": "levantar el vaso boca abajo"}}

Generation
24 tokens
15.62s
1.54 tokens/s

	## Prueba D : Programación en Python
Prompt: "Escribe una función simple en Python que reciba una lista de números y devuelva solo los números pares."
Respuesta: {"name": "filter_pares", "parameters": {"numbers": "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"}}

Generation
46 tokens
31.03s
1.48 tokens/s
