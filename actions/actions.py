from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from bs4 import BeautifulSoup
import json
import os

class ActionValidateCode(Action):
    def name(self) -> Text:
        return "action_validate_code"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        html_code = tracker.latest_message.get('text')
        soup = BeautifulSoup(html_code, 'html.parser')
        errors_found = []

        # Lógica de Validación
        # 1.1.1
        for img in soup.find_all('img'):
            if not img.has_attr('alt'):
                errors_found.append(f"• La imagen `{img.get('src', '...')}` no tiene atributo `alt` (1.1.1).")

        # 2.4.4
        for link in soup.find_all('a'):
            if not link.get_text(strip=True) and not link.find('img'):
                errors_found.append(f"• El enlace `{link.get('href', '#')}` está vacío (2.4.4).")

        # 3.1.1
        if soup.find('html') and not soup.find('html').has_attr('lang'):
             errors_found.append("• La etiqueta `<html>` no tiene atributo `lang` (3.1.1).")

        if not errors_found:
            dispatcher.utter_message(text="✅ Código validado\n\nNo se detectaron errores de Nivel A evidentes en este fragmento.")
        else:
            header = "⚠️ Atención:\n\n"
            body = "\n".join(errors_found)
            footer = "\n\nConsulta el menú para ver soluciones."
            dispatcher.utter_message(text=header + body + footer)

        return []

class ActionGetContent(Action):
    wcag_data = {}

    def __init__(self):
        try:
            json_path = "wcag_data.json"
            if not os.path.exists(json_path):
                json_path = os.path.join(os.path.dirname(__file__), "..", "wcag_data.json")
            with open(json_path, 'r', encoding='utf-8') as f:
                self.wcag_data = json.load(f)
            print(f"✅ Base cargada.")
        except Exception as e:
            print(f"❌ Error JSON: {e}")

    def name(self) -> Text:
        return "action_get_content"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        criterio_id = next(tracker.get_latest_entity_values("criterio_id"), None)
        
        if not criterio_id:
            dispatcher.utter_message(text="Por favor, selecciona una opción del menú.")
            return []
        
        criterio_id = criterio_id.lower().strip()

        # Menús de Principios
        if criterio_id.startswith("principio_"):
            self.mostrar_menu_principio(dispatcher, criterio_id)
            return []

        # Búsqueda de contenido
        content_found = None
        is_glossary = False
        
        for item in self.wcag_data.get("criterios", []):
            if item.get("id") == criterio_id:
                content_found = item
                break
        
        if not content_found:
            for item in self.wcag_data.get("glosario", []):
                if item.get("nombre", "").lower() == criterio_id:
                    content_found = item
                    is_glossary = True
                    break

        # --- DISEÑO VISUAL ---
        if content_found:
            if is_glossary:
                term = content_found.get("nombre")
                defi = content_found.get("definición")
                dispatcher.utter_message(
                    text=f"📖 {term}\n\n_{defi}_",
                    buttons=[{"title": "Ver más términos", "payload": "/consultar_glosario"}]
                )
            else:
                c_id = content_found.get("id")
                nombre = content_found.get("nombre")
                
                # 1. Título
                response = f"📌 {c_id} {nombre}\n\n"
                
                # 2. Definición
                response += f"{content_found.get('definición', '')}\n\n"
                
                # 3. Beneficio
                if content_found.get("beneficio"):
                    response += f"💡 {content_found.get('beneficio')}\n\n"
                
                # 4. Checklist de implementación
                if content_found.get("implementacion"):
                    impl_text = content_found.get('implementacion').replace("- ", "• ")
                    response += f"Cómo cumplirlo:\n{impl_text}\n\n"
                
                # 5. Código
                code_good = content_found.get("codigo_bueno", "")
                code_bad = content_found.get("codigo_malo", "")

                if code_good:
                    response += "✅ Correcto:\n"
                    response += f"html\n{code_good}\n\n"
                
                if code_bad:
                    response += "❌ Incorrecto:\n"
                    response += f"html\n{code_bad}\n"

                # Botones de navegación
                principio_base = c_id.split('.')[0]
                buttons_list = [
                    {"title": "⬅️ Volver", "payload": f'/consultar_criterio{{"criterio_id": "principio_{principio_base}"}}'},
                    {"title": "🔍 Validar", "payload": "/validar_codigo"}
                ]

                dispatcher.utter_message(text=response, buttons=buttons_list)

        else:
            dispatcher.utter_message(text=f"No encontré información sobre '{criterio_id}'.")

        return []

    def mostrar_menu_principio(self, dispatcher, p_id):
        # Mapeo simple de títulos
        titulos = {
            "principio_1": "PERCEPTIBLE",
            "principio_2": "OPERABLE",
            "principio_3": "COMPRENSIBLE",
            "principio_4": "ROBUSTO"
        }
        
        # Definimos los botones manualmente
        buttons = []
        if p_id == "principio_1":
            buttons = [
                {"title": "1.1.1 Contenido no textual", "payload": '/consultar_criterio{"criterio_id": "1.1.1"}'},
                {"title": "1.2.1 Solo audio/video", "payload": '/consultar_criterio{"criterio_id": "1.2.1"}'},
                {"title": "1.2.2 Subtítulos", "payload": '/consultar_criterio{"criterio_id": "1.2.2"}'},
                {"title": "1.3.1 Info y relaciones", "payload": '/consultar_criterio{"criterio_id": "1.3.1"}'},
                {"title": "1.4.1 Uso del color", "payload": '/consultar_criterio{"criterio_id": "1.4.1"}'}
            ]
        elif p_id == "principio_2":
            buttons = [
                {"title": "2.1.1 Teclado", "payload": '/consultar_criterio{"criterio_id": "2.1.1"}'},
                {"title": "2.1.2 Sin trampas", "payload": '/consultar_criterio{"criterio_id": "2.1.2"}'},
                {"title": "2.4.2 Títulos página", "payload": '/consultar_criterio{"criterio_id": "2.4.2"}'},
                {"title": "2.4.4 Propósito enlaces", "payload": '/consultar_criterio{"criterio_id": "2.4.4"}'}
            ]
        elif p_id == "principio_3":
            buttons = [
                {"title": "3.1.1 Idioma página", "payload": '/consultar_criterio{"criterio_id": "3.1.1"}'},
                {"title": "3.2.1 Al recibir foco", "payload": '/consultar_criterio{"criterio_id": "3.2.1"}'},
                {"title": "3.3.2 Etiquetas/Instr.", "payload": '/consultar_criterio{"criterio_id": "3.3.2"}'}
            ]
        elif p_id == "principio_4":
            buttons = [
                {"title": "4.1.1 Análisis (Parsing)", "payload": '/consultar_criterio{"criterio_id": "4.1.1"}'},
                {"title": "4.1.2 Nombre, Rol, Valor", "payload": '/consultar_criterio{"criterio_id": "4.1.2"}'}
            ]

        buttons.append({"title": "🏠 Inicio", "payload": "/navegar_principios"})
        
        dispatcher.utter_message(
            text=f"{titulos.get(p_id, 'Menú')}\nSelecciona una pauta:",
            buttons=buttons
        )