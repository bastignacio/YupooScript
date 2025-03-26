import os
import time
import base64
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

def get_final_image_url(big_img):

    """
    Dado el <img> de la vista grande, devuelve la URL real de la imagen.
    Preferimos 'src' si no es un data:image.
    Si 'src' fuera un data: base64, entonces podríamos mirar otros atributos
    (por ejemplo 'data-origin' o 'data-src').
    """

    # 1) Intentar con 'src'
    src_attr = big_img.get_attribute("src")
    if src_attr and not src_attr.startswith("data:image"):
        return src_attr

    # 2) Como fallback, usar 'data-origin' o 'data-src'
    data_origin = big_img.get_attribute("data-origin")
    if data_origin and not data_origin.startswith("data:image"):
        return data_origin

    data_src = big_img.get_attribute("data-src")
    return data_src

def get_image_bytes(context, page, raw_url):

    """
    Descarga la imagen usando la misma sesión de Playwright (context.request).
    Si es data:image/... la decodifica en base64.
    De lo contrario, hace GET con cookies/referer compartidos.
    """

    if not raw_url:
        return None

    # Si es data:image, decodificamos base64
    if raw_url.startswith("data:image/"):
        base64_str = raw_url.split(",", 1)[1]
        return base64.b64decode(base64_str)

    # Si empieza con //, completamos con https:
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url

    # Si no es absoluta ni data, la unimos a la URL actual
    if not raw_url.startswith("http"):
        raw_url = urljoin(page.url, raw_url)

    # Descargar con la sesión de Playwright (cookies, etc.)
    response = context.request.get(raw_url, headers={"Referer": page.url})
    if not response.ok:
        raise RuntimeError(f"Error HTTP {response.status} al descargar {raw_url}")

    return response.body()

def download_big_images(context, page, dest_folder):

    """
    - Espera y localiza las miniaturas (div.showalbum__children.image__main).
    - Hace clic en cada miniatura para abrir la imagen grande.
    - Obtiene la URL real (prefiriendo 'src'), descarga con Playwright.
    - Cierra la vista y pasa a la siguiente.
    """

    page.wait_for_selector("div.showalbum__children.image__main", timeout=120000)
    thumbs = page.query_selector_all("div.showalbum__children.image__main")
    print(f"Se encontraron {len(thumbs)} miniaturas en el álbum.")

    # === NUEVA LÍNEA: guardamos la cantidad total de miniaturas ===
    num_thumbs = len(thumbs)

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    for idx, thumb in enumerate(thumbs, start=1):
        data_id = thumb.get_attribute("data-id") or str(idx)

        # 1) Clic en la miniatura para abrir la imagen grande
        thumb.click()

        # 2) Esperar a que aparezca el <img> grande
        page.wait_for_selector("img.viewer__img", timeout=180000)
        time.sleep(2)

        # 3) Tomar el <img> y obtener la URL real
        big_img = page.query_selector("img.viewer__img")
        raw_url = get_final_image_url(big_img)
        if not raw_url:
            print(f"[{data_id}] No se encontró URL en 'src' ni 'data-origin'.")
            page.click("#viewer__close")
            page.wait_for_selector("#viewer__close", state="hidden", timeout=180000)
            continue

        # 4) Descargar la imagen
        try:
            img_data = get_image_bytes(context, page, raw_url)
            if not img_data:
                raise RuntimeError("La imagen está vacía o no se pudo descargar.")
        except Exception as e:
            print(f"[{data_id}] Error descargando imagen: {e}")
            page.click("#viewer__close")
            page.wait_for_selector("#viewer__close", state="hidden", timeout=180000)
            continue

        # 5) Guardar la imagen en disco
        _, ext = os.path.splitext(raw_url)
        if not ext or "data:image" in raw_url:
            ext = ".jpg"

        #################################################################
        #################################################################

        # === NUEVO FORMATO: imagen_1_de_29.jpg ===
        file_name = f"NOMBREDEARCHIVO_{idx}_de_{num_thumbs}{ext}"

        file_path = os.path.join(dest_folder, file_name)
        with open(file_path, "wb") as f:
            f.write(img_data)

        print(f"[{data_id}] Descargada -> {file_path} ({len(img_data)} bytes)")

        # 6) Cerrar el visor
        page.click("#viewer__close")
        page.wait_for_selector("#viewer__close", state="hidden", timeout=180000)
        time.sleep(0.5)

def run(album_url, password, dest_folder):

    """
    1. Abre la página Yupoo protegida.
    2. Ingresa la contraseña.
    3. Llama a download_big_images() para cada miniatura.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1) Abrir la URL
        page.goto(album_url)

        # 2) Ingresar la contraseña
        page.wait_for_selector("#indexlock__input", timeout=60000)
        page.fill("#indexlock__input", password)
        page.press("#indexlock__input", "Enter")

        # 3) Esperar a que Yupoo procese la contraseña
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # 4) Descargar imágenes
        download_big_images(context, page, dest_folder)

        browser.close()

if __name__ == "__main__":
    album_url = "INGRESAR URL"
    password = "INGRESAR PASSWORD"
    dest_folder = "imagenes_descargadas"
    run(album_url, password, dest_folder)
