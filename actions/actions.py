from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from bs4 import BeautifulSoup
import json
import os

class ActionValidateCode(Action):

    def name(self) -> Text:
        return "action_validate_code"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        html_code = tracker.latest_message.get('text')
        
        # Intento básico de limpiar el input si no es HTML puro
        soup = BeautifulSoup(html_code, 'html.parser')
        
        errors_found = []

        # Lógica de Validación (Prototipo para Criterios A)
        # 1.1.1 Imágenes sin alt
        images = soup.find_all('img')
        for img in images:
            if not img.has_attr('alt'):
                errors_found.append(f"La imagen '{img.get('src', '...')}' no tiene atributo 'alt' (Criterio 1.1.1).")
            elif not img['alt'].strip():
                # Si está vacío, verificamos si es decorativo (contexto difícil de saber automatizado, pero se avisa)
                pass 

        # 2.4.4 Enlaces vacíos
        links = soup.find_all('a')
        for link in links:
            if not link.get_text(strip=True) and not link.find('img'):
                errors_found.append(f"El enlace '{link.get('href', '#')}' no tiene texto visible ni imagen con alt (Criterio 2.4.4).")

        # 3.1.1 Idioma de página (Básico)
        html_tag = soup.find('html')
        if html_tag and not html_tag.has_attr('lang'):
             errors_found.append("La etiqueta <html> no tiene el atributo 'lang' definido (Criterio 3.1.1).")

        # Responder al usuario
        if not errors_found:
            dispatcher.utter_message(text="✅ **Análisis Rápido:**\nNo encontré errores obvios de Nivel A en este fragmento.\n\nRecuerda que la validación automática es limitada. ¡Revisa el contexto manualmente!")
        else:
            response_text = "⚠️ **Problemas Encontrados:**\n\n"
            for error in errors_found:
                response_text += f"❌ {error}\n"
            
            response_text += "\n¿Quieres saber cómo arreglar esto? Usa el menú para consultar el criterio."
            dispatcher.utter_message(text=response_text)

        return []

class ActionGetContent(Action):

    wcag_data = {}

    def __init__(self):
        """
        Carga la base de conocimiento al iniciar el Action Server.
        """
        try:
            # Aseguramos la ruta correcta (a veces Docker/Heroku cambian el CWD)
            json_path = "wcag_data.json"
            if not os.path.exists(json_path):
                # Fallback por si la ruta cambia en producción
                json_path = os.path.join(os.path.dirname(__file__), "..", "wcag_data.json")

            with open(json_path, 'r', encoding='utf-8') as f:
                self.wcag_data = json.load(f)
            print(f"✅ Base de Conocimiento cargada: {len(self.wcag_data.get('criterios', []))} criterios.")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO al cargar JSON: {e}")
            self.wcag_data = {"criterios": [], "glosario": []}

    def name(self) -> Text:
        return "action_get_content"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 1. Obtener qué pidió el usuario (Entidad o Payload)
        criterio_id = next(tracker.get_latest_entity_values("criterio_id"), None)

        if not criterio_id:
            dispatcher.utter_message(text="¿Qué criterio te gustaría consultar? (ej. escribe '1.1.1' o elige del menú)")
            return []
        
        criterio_id = criterio_id.lower().strip()

        # 2. MENU DE NAVEGACIÓN (PRINCIPIOS)
        # Esto permite navegar jerárquicamente: Principios -> Criterios
        if criterio_id == "principio_1":
            dispatcher.utter_message(
                text="👁️ **Principio 1: Perceptible**\nLa información debe ser presentada de manera que los usuarios puedan percibirla.",
                buttons=[
                    {"title": "1.1.1 Contenido no textual", "payload": '/consultar_criterio{"criterio_id": "1.1.1"}'},
                    {"title": "1.2.1 Solo audio/video", "payload": '/consultar_criterio{"criterio_id": "1.2.1"}'},
                    {"title": "1.2.2 Subtítulos", "payload": '/consultar_criterio{"criterio_id": "1.2.2"}'},
                    {"title": "1.3.1 Info y relaciones", "payload": '/consultar_criterio{"criterio_id": "1.3.1"}'},
                    {"title": "1.4.1 Uso del color", "payload": '/consultar_criterio{"criterio_id": "1.4.1"}'},
                    {"title": "🔙 Volver al Inicio", "payload": "/navegar_principios"}
                ]
            )
            return []

        elif criterio_id == "principio_2":
            dispatcher.utter_message(
                text="⌨️ **Principio 2: Operable**\nLos componentes de la interfaz deben ser operables (navegables).",
                buttons=[
                    {"title": "2.1.1 Teclado", "payload": '/consultar_criterio{"criterio_id": "2.1.1"}'},
                    {"title": "2.1.2 Sin trampas", "payload": '/consultar_criterio{"criterio_id": "2.1.2"}'},
                    {"title": "2.4.2 Títulos página", "payload": '/consultar_criterio{"criterio_id": "2.4.2"}'},
                    {"title": "2.4.4 Propósito enlaces", "payload": '/consultar_criterio{"criterio_id": "2.4.4"}'},
                    {"title": "🔙 Volver al Inicio", "payload": "/navegar_principios"}
                ]
            )
            return []

        elif criterio_id == "principio_3":
            dispatcher.utter_message(
                text="🧠 **Principio 3: Comprensible**\nLa información y el manejo de la interfaz deben ser comprensibles.",
                buttons=[
                    {"title": "3.1.1 Idioma página", "payload": '/consultar_criterio{"criterio_id": "3.1.1"}'},
                    {"title": "3.2.1 Al recibir foco", "payload": '/consultar_criterio{"criterio_id": "3.2.1"}'},
                    {"title": "3.3.2 Etiquetas/Instr.", "payload": '/consultar_criterio{"criterio_id": "3.3.2"}'},
                    {"title": "🔙 Volver al Inicio", "payload": "/navegar_principios"}
                ]
            )
            return []

        elif criterio_id == "principio_4":
            dispatcher.utter_message(
                text="💪 **Principio 4: Robusto**\nEl contenido debe ser robusto para ser interpretado por tecnologías de asistencia.",
                buttons=[
                    {"title": "4.1.1 Análisis (Parsing)", "payload": '/consultar_criterio{"criterio_id": "4.1.1"}'},
                    {"title": "4.1.2 Nombre, Rol, Valor", "payload": '/consultar_criterio{"criterio_id": "4.1.2"}'},
                    {"title": "🔙 Volver al Inicio", "payload": "/navegar_principios"}
                ]
            )
            return []

        # 3. BÚSQUEDA DE CONTENIDO PROFUNDO (CRITERIOS Y GLOSARIO)
        content_found = None
        is_glossary = False
        
        # Buscar primero en Criterios
        for item in self.wcag_data.get("criterios", []):
            if item.get("id") == criterio_id:
                content_found = item
                break

        # Si no, buscar en Glosario
        if not content_found:
            for item in self.wcag_data.get("glosario", []):
                if item.get("nombre", "").lower() == criterio_id:
                    content_found = item
                    is_glossary = True
                    break

        # 4. CONSTRUCCIÓN DE LA RESPUESTA
        if content_found:
            if is_glossary:
                # Respuesta simple para glosario
                term = content_found.get("nombre")
                defi = content_found.get("definición")
                dispatcher.utter_message(text=f"📖 **GLOSARIO: {term}**\n\n{defi}")
                # Botón simple para volver
                dispatcher.utter_message(
                    text="¿Consultar otro término?",
                    buttons=[{"title": "Ver todo el Glosario", "payload": "/consultar_glosario"}]
                )

            else:
                # Respuesta COMPLETA para Criterios (Usando los nuevos campos del JSON)
                c_id = content_found.get("id")
                nombre = content_found.get("nombre")
                definicion = content_found.get("definición", "")
                beneficio = content_found.get("beneficio", "")
                implementacion = content_found.get("implementacion", "")
                errores = content_found.get("errores", "")
                code_good = content_found.get("codigo_bueno", "")
                code_bad = content_found.get("codigo_malo", "")

                # Bloque 1: Teoría
                response = f"📘 **{c_id} {nombre}**\n\n"
                response += f"**Definición:**\n{definicion}\n\n"
                
                if beneficio:
                    response += f"❤️ **Beneficio:**\n{beneficio}\n\n"
                
                if implementacion:
                    response += f"✅ **Cómo cumplirlo:**\n{implementacion}\n\n"
                
                if errores:
                    response += f"⚠️ **Errores comunes:**\n{errores}"

                dispatcher.utter_message(text=response)

                # Bloque 2: Código (Mensaje separado para claridad)
                if code_good or code_bad:
                    code_msg = ""
                    if code_good:
                        code_msg += f"👍 **BIEN:**\n```html\n{code_good}\n```\n"
                    if code_bad:
                        code_msg += f"👎 **MAL:**\n```html\n{code_bad}\n```"
                    
                    dispatcher.utter_message(text=code_msg)

                # Bloque 3: Botones de Flujo (Navegación inteligente)
                # Determinamos a qué principio volver (ej: 1.1.1 -> principio_1)
                principio_base = c_id.split('.')[0]
                
                dispatcher.utter_message(
                    text="¿Qué hacemos ahora?",
                    buttons=[
                        {"title": f"🔙 Volver al Principio {principio_base}", "payload": f'/consultar_criterio{{"criterio_id": "principio_{principio_base}"}}'},
                        {"title": "🏠 Menú Principal", "payload": "/navegar_principios"},
                        {"title": "🔍 Validar Código", "payload": "/validar_codigo"}
                    ]
                )

        else:
            dispatcher.utter_message(text=f"🤔 No encontré información sobre '{criterio_id}'. Intenta con el número (ej. '1.1.1') o usa el menú.")

        return []