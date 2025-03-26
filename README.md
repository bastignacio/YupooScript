# Yupoo Album Downloader

Este script utiliza [Playwright](https://playwright.dev/) para acceder a un álbum protegido de Yupoo, ingresar la contraseña, y descargar las imágenes en grande. Las imágenes se guardan en disco con un nombre que incluye un contador y el total de miniaturas encontradas en el álbum.

## Características

- Acceso a álbumes protegidos por contraseña en Yupoo.
- Automatiza la navegación para hacer clic en cada miniatura y abrir la imagen grande.
- Descarga la imagen real usando la sesión de Playwright (para conservar cookies y cabeceras necesarias).
- Guarda cada imagen con un nombre en el formato `imagen_X_de_Y.jpg`, donde:
  - `X` es el número de imagen actual.
  - `Y` es la cantidad total de miniaturas encontradas.

## Requisitos

- **Python 3.7+** (se recomienda Python 3.10 o superior)
- Paquete **playwright**

## Instalación

1. **Clona este repositorio** o descarga el script.
2. Crea y activa un entorno virtual (opcional, pero recomendado):

   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En macOS/Linux:
   source venv/bin/activate

