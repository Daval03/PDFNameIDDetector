import fitz  # PyMuPDF
import requests
import os
import difflib

def extract_first_page(input_pdf_path, output_pdf_path):
    """
    Extrae la primera página de un PDF y la guarda en un nuevo archivo.
    
    Args:
    - input_pdf_path (str): Ruta al archivo PDF de entrada.
    - output_pdf_path (str): Ruta al archivo PDF de salida con la primera página.
    """
    doc = fitz.open(input_pdf_path)
    doc.load_page(0)  # 0-indexed, la primera página es la 0
    new_doc = fitz.open()  # Nuevo documento PDF
    new_doc.insert_pdf(doc, from_page=0, to_page=0)  # Insertar solo la primera página
    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()

def extract_text_from_pdf(input_pdf_path):
    """
    Extrae el texto de la primera página de un PDF usando la API de OCR.space.
    
    Args:
    - input_pdf_path (str): Ruta al archivo PDF de entrada.
    
    Returns:
    - str: Texto extraído de la primera página del PDF.
    """
    output_pdf_path = 'temp_first_page.pdf'
    
    # Extraer la primera página del PDF
    extract_first_page(input_pdf_path, output_pdf_path)
    
    # Leer la API key desde el archivo de configuración
    with open('config.txt', 'r') as file:
        api_key = file.read().strip()

    # URL de la API de OCR.space
    url = 'https://api.ocr.space/parse/image'
    
    # Parámetros de la solicitud
    payload = {
        'apikey': api_key,
        'language': 'spa',
        'isOverlayRequired': 'false',
        'filetype': 'PDF',
        'OCREngine': '2'  # Habilitar OCR Engine 2
    }
    
    # Archivo PDF con la primera página
    with open(output_pdf_path, 'rb') as file:
        files = {'file': ('first_page.pdf', file)}
        
        # Envía la solicitud POST a la API
        response = requests.post(url, files=files, data=payload)
    
    # Procesa la respuesta
    if response.status_code == 200:
        json_response = response.json()
        if json_response['IsErroredOnProcessing']:
            raise Exception(f"Error en el procesamiento: {json_response['ErrorMessage']}")
        else:
            return json_response['ParsedResults'][0]['ParsedText']
    else:
        raise Exception(f"Error en la solicitud: {response.status_code}")

def leer_datos_archivo(nombre_archivo):
    """
    Lee los datos desde un archivo de texto.
    
    Args:
    - nombre_archivo (str): Ruta al archivo de texto.
    
    Returns:
    - list: Lista de tuplas con (id_, nombre).
    """
    datos = []
    
    try:
        with open(nombre_archivo, 'r') as archivo:
            for linea in archivo:
                # Eliminar posibles espacios en blanco al inicio y final
                linea = linea.strip()
                # Separar por el primer espacio en blanco encontrado
                partes = linea.split(maxsplit=1)
                if len(partes) == 2:
                    id_ = partes[0].strip()
                    nombre = partes[1].strip()
                    # Añadir como tupla (id_, nombre) a la lista
                    datos.append((id_, nombre))
    except FileNotFoundError:
        print(f"El archivo {nombre_archivo} no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    
    return datos

def encontrar_coincidencia(texto_extraido, datos):
    """
    Encuentra la coincidencia más cercana en los datos.
    
    Args:
    - texto_extraido (str): Texto extraído del PDF.
    - datos (list): Lista de tuplas con (id_, nombre) leídos desde el archivo.
    
    Returns:
    - tuple: La coincidencia más cercana (id_, nombre) o None si no hay coincidencia.
    """
    mejor_coincidencia = None
    mejor_ratio = 0
    
    for id_, nombre in datos:
        ratio_id = difflib.SequenceMatcher(None, id_, texto_extraido).ratio()
        ratio_nombre = difflib.SequenceMatcher(None, nombre, texto_extraido).ratio()
        
        if ratio_id > mejor_ratio or ratio_nombre > mejor_ratio:
            mejor_ratio = max(ratio_id, ratio_nombre)
            mejor_coincidencia = (id_, nombre)
    
    return mejor_coincidencia

def comparar_y_renombrar_pdfs(carpeta_pdfs, datos):
    """
    Lee todos los PDFs de una carpeta, extrae el texto de la primera página, compara con los datos
    y renombra los archivos PDF.
    
    Args:
    - carpeta_pdfs (str): Ruta a la carpeta que contiene los archivos PDF.
    - datos (list): Lista de tuplas con (id_, nombre) leídos desde el archivo.
    """
    archivos_pdfs = [f for f in os.listdir(carpeta_pdfs) if f.endswith('.pdf')]
    
    for archivo_pdf in archivos_pdfs:
        ruta_pdf = os.path.join(carpeta_pdfs, archivo_pdf)
        
        try:
            # Extraer texto del PDF
            texto_extraido = extract_text_from_pdf(ruta_pdf)
            
            # Encontrar coincidencia más cercana en los datos
            coincidencia = encontrar_coincidencia(texto_extraido, datos)
            
            if coincidencia:
                id_, nombre = coincidencia
                # Renombrar archivo PDF
                nuevo_nombre = f"{id_}_{nombre}.pdf"
                nueva_ruta_pdf = os.path.join(carpeta_pdfs, nuevo_nombre)
                os.rename(ruta_pdf, nueva_ruta_pdf)
                
                # Eliminar el dato de la lista
                datos.remove(coincidencia)
        except Exception as e:
            print(f"Error procesando {archivo_pdf}: {e}")

# Ejemplo de uso
carpeta_pdfs = 'Examenes-2'
nombre_archivo = 'Lista.txt'

try:
    # Leer datos desde el archivo
    lista_datos = leer_datos_archivo(nombre_archivo)
    print(f"Datos leídos del archivo:\n{lista_datos}")
    
    # Procesar y renombrar PDFs
    comparar_y_renombrar_pdfs(carpeta_pdfs, lista_datos)
    print(f"Renombrado de archivos completado.")
    
except Exception as e:
    print(e)
