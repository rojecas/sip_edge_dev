https://github.com/ggml-org/llama.cpp

https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md


Preparar el Entorno
Abre tu terminal (o conecta por SSH) y actualiza el sistema e instala las herramientas de compilación:

```
sudo apt update && sudo apt upgrade -y
sudo apt install git build-essential cmake -y
sudo apt install libssl-dev -y
```

## Clonar y Compilar el repo
```
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
```

### 1. Crear una carpeta de compilación para no ensuciar el código
```
mkdir build
cd build
```

### 2. Configurar el proyecto con CMake
```
cmake ..
```

### 3. Desactivar libreria multimodal MTMD
libmtmd es la librería para MulTiModal Data (procesamiento de imágenes, audio, etc.) en llama.cpp. Al compilar con LLAMA_MTMD=ON (valor por defecto en algunas versiones), se generan ejecutables que enlazan dinámicamente con esa librería.

cmake .. -DLLAMA_MTMD=OFF

### 4. Compilar (esto es lo que reemplaza al antiguo make -j4)
```
cmake --build . --config Release -j4
```


### 5. "Instalar" la aplicacion
Para instalar los binarios a nivel de sistema, escribe el siguiente comando, el cual copiará los ejecutables principales (llama-cli, llama-server, etc.) a la carpeta /usr/local/bin.  Esta ubicación es la más adecuada para que estén disponibles para todos los usuarios y ya está incluida en el PATH del sistema.

```Bash
sudo cmake --install build
```

### 5.1 Verificar y probar

Después de la instalación, puedes hacer algunas comprobaciones rápidas:

Para comprobar la ruta, ejecuta:

```Bash
which llama-cli.
```

Debería mostrar /usr/local/bin/llama-cli.

Para verificar permisos, un vistazo rápido con:

```Bash
ls -l /usr/local/bin/llama*
```
 debería mostrar -rwxr-xr-x, lo que indica que todos los usuarios pueden leer y ejecutar el archivo.
 
Verifica que todo funciona
```bash
llama-cli --help
```

## 6. Descargar Modelos

sudo mkdir /home/models

sudo chown root:users /home/models

sudo chmod 755 /home/models

```
wget -O /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
```
```
wget -O /home/models/llama-3.2-3b-instruct-q4_k_m.gguf https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

Opción: Phi-2 (2.7B) - Formato Q4_K_M (Recomendado)
```
sudo wget -O /home/models/phi-2.Q4_K_M.gguf https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

sudo wget -O /home/models/gemma-4-E2B-it-Q4_K_M.gguf https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf


sudo wget -O /home/models/gemma-4-E4B-it-Q4_K_M.gguf https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q4_K_M.gguf


sudo wget -O /home/models/Qwen3.5-2B-UD-Q2_K_XL.gguf https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-UD-Q2_K_XL.gguf

sudo wget -O /home/models/Qwen3.5-2B-UD-Q3_K_XL.gguf https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-UD-Q3_K_XL.gguf

sudo wget -O /home/models/Qwen3.5-0.8B-UD-Q2_K_XL.gguf https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-UD-Q2_K_XL.gguf

sudo wget -O /home/models/Qwen3.5-0.8B-UD-Q3_K_XL.gguf https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-UD-Q3_K_XL.gguf

sudo wget -O /home/models/Qwen3.5-0.8B-UD-Q4_K_XL.gguf https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/resolve/main/Qwen3.5-0.8B-UD-Q4_K_XL.gguf


## Ejecutar en CLI

# Usar 4 núcleos (máximo en CM-4)
llama-cli -m /home/models/gemma-4-E2B-it-Q4_K_M.gguf -c 2048 -p "Hola" -t 4

# Usar 2 núcleos (para dejar recursos para otros procesos)
llama-cli -m modelo.gguf -p "Hola" -t 2

# Usar 1 núcleo (para depuración o ahorro de batería)
llama-cli -m modelo.gguf -p "Hola" -t 1


## Ejecutar el Servidor apuntando a la ruta absoluta
Ahora, para correr el servidor, debemos indicarle la ruta absoluta donde guardaste el modelo.
Asumiendo que estás parado en la carpeta raíz de llama.cpp (/storage/MySource/llama.cpp):

```Bash
sudo llama-server -m /storage/MySource/models/phi-2.Q4_K_M.gguf -c 2048 --host 0.0.0.0 --port 8080 --chat-template phi2

sudo llama-server -m /home/models/gemma-4-E2B-it-Q4_K_M.gguf -c 2048 --host 0.0.0.0 --port 8080 --chat-template gemma
sudo llama-server -m /home/models/gemma-4-E4B-it-Q4_K_M.gguf -c 2048 --host 0.0.0.0 --port 8080 --chat-template gemma

sudo llama-server -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf -c 2048 --host 0.0.0.0 --port 8080
```

sudo llama-server -m /home/models/gemma-4-E2B-it-Q4_K_M.gguf --host 0.0.0.0 --port 8080 -t 4 --chat-template-kwargs '{"enable_thinking":false}'

sudo llama-server -m /home/models/Qwen3.5-2B-UD-Q2_K_XL.gguf --host 0.0.0.0 --port 8080 -t 4 --chat-template-kwargs '{"enable_thinking":false}'