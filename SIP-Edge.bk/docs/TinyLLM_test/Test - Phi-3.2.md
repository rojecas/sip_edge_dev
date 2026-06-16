MS PHI-3
Modelo:Phi-3-mini-4k-instruct-q4.gguf
sudo ./build/bin/llama-server -m /storage/MySource/models/Phi-3-mini-4k-instruct-q4.gguf -c 2048 --host 0.0.0.0 --port 8080

[htop - baseline]
171 ~ 172 M / 3.70G

[htop - Service already up]
3.29G / 3.70G


	## Prueba A: Manzanas

Prompt: Tengo 5 manzanas. Me como 2 y luego compro 3 más. ¿Cuántas manzanas tengo ahora? Explica paso a paso.
Respuesta: 

Paso 1: Tienes inicialmente 5 manzanas.
Paso 2: Te comes 2 manzanas, así que restamos 2 de 5: 5 - 2 = 3 manzanas.
Paso 3: Compras 3 manzanas adicionales, así que sumamos 3 a las 3 manzanas que aún tienes: 3 + 3 = 6 manzanas.
Por lo tanto, ahora tienes 6 manzanas.

Generation
124 tokens
92.41s
1.34 tokens/s


	## Prueba B: Correo Electronico

Prompt: "Escribe un correo electrónico corto y formal para mi jefe, informando que el proyecto del Raspberry Pi está operativo. Firma como 'Ingeniero de Pruebas'. No incluyas explicaciones extra, solo el correo."
Respuesta:
Estimado Sr. García,

Espero que este mensaje le encuentre bien. Me dirijo a usted para informarle que el proyecto del Raspberry Pi está completamente operativo y está funcionando sin inconvenientes.

Agradezco su continuo apoyo y confío en que esta solución sea un paso adelante hacia nuestros objetivos de mejora en la eficiencia de la empresa.

Agradezco su atención y quedo a la espera de cualquier comentario o instrucción adicional.

Atentamente,

Ingeniero de Pruebas

Generation
148 tokens
116.45s
1.27 tokens/s

	## Prueba C - Analisis del mundo fisico
	
Prompt: "Si pongo un vaso de agua lleno boca abajo sobre una mesa, ¿qué pasa cuando levanto el vaso? Responde en una sola frase."
Respuesta: El vaso de agua se derrama debido al peso del agua y la gravedad.
Generation
21 tokens
16.25s
1.29 tokens/s

	## Prueba D : Programación en Python
Prompt: "Escribe una función simple en Python que reciba una lista de números y devuelva solo los números pares."
Respuesta: 
def filtrar_pares(lista_numeros):

   return [numero for numero in lista_numeros if numero % 2 == 0]


# Ejemplo de uso:

lista = [1, 2, 3, 4, 5, 6]

resultado = filtrar_pares(lista)

print(resultado)  # Imprime: [2, 4, 6]


