from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from bs4 import BeautifulSoup
import json

class ActionValidateCode(Action):

    def name(self) -> Text:
        return "action_validate_code"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        html_code = tracker.latest_message.get('text')
        
        soup = BeautifulSoup(html_code, 'html.parser')
        
        errors_found = []

        # Lógica de Validación
        # Verificación de <img> sin 'alt' (Criterio 1.1.1)
        images = soup.find_all('img')
        for img in images:
            if not img.has_attr('alt'):
                errors_found.append(f"La imagen '{img.get('src', '...')}' no tiene atributo 'alt' (Criterio 1.1.1).")

        # Verificación de <a> sin texto (Criterio 2.4.4)
        links = soup.find_all('a')
        for link in links:
            # Revisa si la etiqueta no tiene texto o el texto está vacío
            if not link.string or not str(link.string).strip():
                errors_found.append(f"El enlace '{link.get('href', '#')}' no tiene texto visible (Criterio 2.4.4).")

        # Responder al usuario
        if not errors_found:
            dispatcher.utter_message(text="✅ ¡Buen trabajo! No encontré errores obvios de Nivel A en tu código.")
        else:
            response_text = "¡Ojo! Encontré estos problemas en tu código:\n\n"
            for error in errors_found:
                response_text += f"❌ {error}\n"
            
            dispatcher.utter_message(text=response_text)

        return []

# ACCIÓN PARA EL MÓDULO 4: OBTENER CONTENIDO (CU-2, CU-3 y Navegación)
class ActionGetContent(Action):

    wcag_data = {}

    def __init__(self):
        """
        Constructor: Carga la base de conocimiento (wcag_data.json) en memoria.
        """
        try:
            json_path = "wcag_data.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                self.wcag_data = json.load(f)
            print("Base de Conocimiento (wcag_data.json) cargada exitosamente.")
        except FileNotFoundError:
            print(f"ERROR: No se encontró el archivo '{json_path}'.")
        except Exception as e:
            print(f"ERROR al cargar '{json_path}': {e}")

    def name(self) -> Text:
        return "action_get_content"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Obtener la entidad 'criterio_id'
        criterio_id = next(tracker.get_latest_entity_values("criterio_id"), None)

        if not criterio_id:
            dispatcher.utter_message(text="¿Qué criterio o término te gustaría consultar? (ej. '1.1.1' o 'ARIA')")
            return []
        
        # Normalizar el ID
        criterio_id = criterio_id.lower().strip()

        # LÓGICA DE NAVEGACIÓN
        if criterio_id == "principio_1":
            dispatcher.utter_message(
                text="👁️ **Principio 1: Perceptible**\nLa información debe ser presentada de manera que los usuarios puedan percibirla.\n\nSelecciona una pauta:",
                buttons=[
                    {"title": "1.1.1 Contenido no textual", "payload": '/consultar_criterio{"criterio_id": "1.1.1"}'},
                    {"title": "1.2.1 Solo audio/video", "payload": '/consultar_criterio{"criterio_id": "1.2.1"}'},
                    {"title": "1.2.2 Subtítulos", "payload": '/consultar_criterio{"criterio_id": "1.2.2"}'},
                    {"title": "1.3.1 Info y relaciones", "payload": '/consultar_criterio{"criterio_id": "1.3.1"}'},
                    {"title": "1.4.1 Uso del color", "payload": '/consultar_criterio{"criterio_id": "1.4.1"}'},
                ]
            )
            return []

        elif criterio_id == "principio_2":
            dispatcher.utter_message(
                text="⌨️ **Principio 2: Operable**\nLos componentes de la interfaz deben ser operables (navegables).\n\nSelecciona una pauta:",
                buttons=[
                    {"title": "2.1.1 Teclado", "payload": '/consultar_criterio{"criterio_id": "2.1.1"}'},
                    {"title": "2.1.2 Sin trampas de teclado", "payload": '/consultar_criterio{"criterio_id": "2.1.2"}'},
                    {"title": "2.4.2 Títulos de página", "payload": '/consultar_criterio{"criterio_id": "2.4.2"}'},
                    {"title": "2.4.4 Propósito de enlaces", "payload": '/consultar_criterio{"criterio_id": "2.4.4"}'},
                ]
            )
            return []

        elif criterio_id == "principio_3":
            dispatcher.utter_message(
                text="🧠 **Principio 3: Comprensible**\nLa información y el manejo de la interfaz deben ser comprensibles.\n\nSelecciona una pauta:",
                buttons=[
                    {"title": "3.1.1 Idioma de la página", "payload": '/consultar_criterio{"criterio_id": "3.1.1"}'},
                    {"title": "3.2.1 Al recibir foco", "payload": '/consultar_criterio{"criterio_id": "3.2.1"}'},
                    {"title": "3.3.2 Etiquetas/Instrucciones", "payload": '/consultar_criterio{"criterio_id": "3.3.2"}'},
                ]
            )
            return []

        elif criterio_id == "principio_4":
            dispatcher.utter_message(
                text="💪 **Principio 4: Robusto**\nEl contenido debe ser robusto para ser interpretado por tecnologías de asistencia.\n\nSelecciona una pauta:",
                buttons=[
                    {"title": "4.1.1 Análisis (Parsing)", "payload": '/consultar_criterio{"criterio_id": "4.1.1"}'},
                    {"title": "4.1.2 Nombre, Rol, Valor", "payload": '/consultar_criterio{"criterio_id": "4.1.2"}'},
                ]
            )
            return []

        # LÓGICA DE BÚSQUEDA EN EL JSON (CRITERIOS Y GLOSARIO)
        content_found = None
        
        # Buscar en la lista de 'criterios'
        lista_criterios = self.wcag_data.get("criterios", [])
        for item in lista_criterios:
            if item.get("id") == criterio_id:
                content_found = item
                break

        # Si no está en criterios, buscar en 'glosario'
        if not content_found:
            lista_glosario = self.wcag_data.get("glosario", [])
            for item in lista_glosario:
                # Compara el nombre en minúsculas para evitar errores
                if item.get("nombre", "").lower() == criterio_id:
                    content_found = item
                    break

        # Responder al usuario
        if content_found:
            # Extraer datos (Maneja tilde en 'definición' según tu JSON)
            definicion = content_found.get("definición", "No se encontró definición.")
            guia = content_found.get("guia", "")
            nombre_titulo = content_found.get("nombre", criterio_id.upper())
            
            # Construir respuesta
            response = f"📘 **{criterio_id.upper()} - {nombre_titulo}**\n\n"
            response += f"**Definición:**\n{definicion}\n"
            
            if guia:
                 response += f"\n💡 **Guía Rápida:**\n{guia}"
            
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text=f"⚠️ Lo siento, no pude encontrar información sobre '{criterio_id}'. Intenta con otro término o número.")

        return []