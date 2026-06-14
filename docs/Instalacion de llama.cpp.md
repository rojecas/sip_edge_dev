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

### 3. Compilar (esto es lo que reemplaza al antiguo make -j4)
```
cmake --build . --config Release -j4
```

## Descargar Modelos
```
wget -O models/qwen2.5-1.5b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
```
```
wget -O models/llama-3.2-3b-instruct-q4_k_m.gguf https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
```

Opción: Phi-2 (2.7B) - Formato Q4_K_M (Recomendado)
```
wget -O models/phi-2.Q4_K_M.gguf https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```


## Ejecutar el Servidor apuntando a la ruta absoluta
Ahora, para correr el servidor, debemos indicarle la ruta absoluta donde guardaste el modelo.
Asumiendo que estás parado en la carpeta raíz de llama.cpp (/storage/MySource/llama.cpp):
```
sudo ./build/bin/llama-server -m /storage/MySource/models/phi-2.Q4_K_M.gguf -c 2048 --host 0.0.0.0 --port 8080 --chat-template phi2
```
