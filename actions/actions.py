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

        # 1. Obtener el código HTML del último mensaje del usuario
        html_code = tracker.latest_message.get('text')
        
        # 2. Inicializar BeautifulSoup
        soup = BeautifulSoup(html_code, 'html.parser')
        
        # 3. Lista para guardar errores
        errors_found = []

        # --- Lógica de Validación (Criterios Nivel A) ---

        # 1. Verificación de <img> sin 'alt' (Criterio 1.1.1)
        images = soup.find_all('img')
        for img in images:
            if not img.has_attr('alt'):
                errors_found.append(f"La imagen '{img.get('src', '...')}' no tiene atributo 'alt' (Criterio 1.1.1).")

        # 2. Verificación de <a> sin texto (Criterio 2.4.4)
        links = soup.find_all('a')
        for link in links:
            # Revisa si la etiqueta no tiene texto o el texto está vacío
            if not link.string or not str(link.string).strip():
                errors_found.append(f"El enlace '{link.get('href', '#')}' no tiene texto visible (Criterio 2.4.4).")

        # 3. Responder al usuario
        if not errors_found:
            dispatcher.utter_message(text="✅ ¡Buen trabajo! No encontré errores obvios de Nivel A en tu código.")
        else:
            response_text = "¡Ojo! Encontré estos problemas en tu código:\n\n"
            for error in errors_found:
                response_text += f"❌ {error}\n"
            
            dispatcher.utter_message(text=response_text)

        return []

# ---------------------------------------------------------------------
# ACCIÓN PARA EL MÓDULO 4: OBTENER CONTENIDO DEL JSON
# ---------------------------------------------------------------------
class ActionGetContent(Action):

    # Variable de clase para guardar los datos del JSON
    wcag_data = {}

    def __init__(self):
        """
        Constructor: Carga la base de conocimiento (Módulo 4) en memoria.
        """
        try:
            # Ruta al archivo JSON
            json_path = "wcag_data.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                self.wcag_data = json.load(f)
            print("Base de Conocimiento (wcag_data.json) cargada exitosamente.")
        except FileNotFoundError:
            print(f"ERROR: No se encontró el archivo '{json_path}'. El bot no podrá dar definiciones.")
        except Exception as e:
            print(f"ERROR al cargar '{json_path}': {e}")


    def name(self) -> Text:
        return "action_get_content"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 1. Obtener la entidad 'criterio_id' que extrajo el NLU
        criterio_id = next(tracker.get_latest_entity_values("criterio_id"), None)

        if not criterio_id:
            # Si no se pudo extraer la entidad
            dispatcher.utter_message(text="¿Qué criterio o término te gustaría consultar? (ej. '1.1.1' o 'ARIA')")
            return []
        
        # Normalizar el ID
        criterio_id = criterio_id.lower().strip()
        content_found = None

        # 2. Lógica de búsqueda en el JSON
        # Busqueda en base al ID
        Lista_criterios = self.wcag_data.get("criterios", [])
        for item in Lista_criterios:
            if item.get("id") == criterio_id:
                content_found = item
                break

        # Si no está en criterios, buscamos en 'glosario' comparando el campo "nombre"
        if not content_found:
            Lista_glosario = self.wcag_data.get("glosario", [])
            for item in Lista_glosario:
                if item.get("nombre", "").lower() == criterio_id:
                    content_found = item
                    break

        # 3. Responder al usuario
        if content_found:
            # Supuesto: cada entrada tiene 'definicion' y 'guia'
            definicion = content_found.get("definición", "No se encontró definición.")
            guia = content_found.get("guia", "No se encontró guía.")
            
            response = f"**{criterio_id.upper()}**:\n\n"
            response += f"**Definición:**\n{definicion}\n\n"
            
            if "guia" in content_found and content_found["guia"]:
                 response += f"**Guía Rápida:**\n{guia}"
            
            dispatcher.utter_message(text=response)
        else:
            # No se encontró en el JSON
            dispatcher.utter_message(text=f"Lo siento, no pude encontrar información sobre '{criterio_id}'.")

        return []