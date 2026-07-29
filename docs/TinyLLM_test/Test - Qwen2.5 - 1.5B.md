 El Retador (Qwen 2.5 - 1.5B)
Modelo: qwen2.5-1.5b-instruct-q4_k_m.gguf
sudo ./build/bin/llama-server -m /storage/MySource/models/qwen2.5-1.5b-instruct-q4_k_m.gguf -c 2048 --host 0.0.0.0 --port 8080

[htop - baseline]
171 ~ 172 M / 3.70G

[htop - Service already up]
1.32G / 3.70G

	## Prueba A: Manzanas

Prompt: Tengo 5 manzanas. Me como 2 y luego compro 3 más. ¿Cuántas manzanas tengo ahora? Explica paso a paso.
Respuesta: 
Comencemos calculando paso a paso:

Llegamos a casa con 5 manzanas.
Comemos 2 manzanas.
Nos quedamos con 5 - 2 = 3 manzanas.
Comemos 3 más manzanas.
Nos quedamos con 3 - 3 = 0 manzanas.
Así que finalmente, después de todas estas acciones, tienes 0 manzanas.

Generation
100 tokens
29.63s
3.37 tokens/s

	## Prueba B: Correo Electronico

Prompt: "Escribe un correo electrónico corto y formal para mi jefe, informando que el proyecto del Raspberry Pi está operativo. Firma como 'Ingeniero de Pruebas'. No incluyas explicaciones extra, solo el correo."
Respuesta:
Asunto: Proyecto Raspberry Pi Operativo

Estimado Director,

Es un placer informarles que nuestro proyecto Raspberry Pi ha finalizado con éxito. El dispositivo ha alcanzado su estado operativo, y está listo para su uso y evaluación.

Esperamos que esta información les resulte útil para su informe de la semana, y les agradecemos su tiempo.

Con cordiales saludos,

Ingeniero de Pruebas


Generation
94 tokens
28.65s
3.28 tokens/s


	## Prueba C - Analisis del mundo fisico
	
Prompt: "Si pongo un vaso de agua lleno boca abajo sobre una mesa, ¿qué pasa cuando levanto el vaso? Responde en una sola frase."
Respuesta: 
El vaso se desplaza hacia abajo cuando se levantas.

Generation
16 tokens
4.76s
3.36 tokens/s


	## Prueba D : Programación en Python
Prompt: "Escribe una función simple en Python que reciba una lista de números y devuelva solo los números pares."
Respuesta:
Aquí tienes una función en Python que cumple con la descripción:

python

def get_even_numbers(numbers):
    even_numbers = [num for num in numbers if num % 2 == 0]
    return even_numbers

Esta función utiliza una lista comprensión para iterar sobre cada número en la lista numbers. La condición num % 2 == 0 verifica si el número es par (si la división entre 2 resulta en un resto de 0). Si la condición se cumple, el número es incluido en la nueva lista even_numbers. A continuación, la función devuelve la nueva lista con los números pares.


Generation
143 tokens
45.41s
3.15 tokens/s
