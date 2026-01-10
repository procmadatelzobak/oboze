"""Gemini AI Agent for Ó bože."""
import json
import re
import logging
from typing import Optional
import google.generativeai as genai

from app.config import get_config
from app.models import Entity, Scenario, AgentResponse, EngineCommands

logger = logging.getLogger("oboze.agent")


SYSTEM_PROMPT = """Jsi vypravěč ve hře "Ó bože". Hráč hraje roli "bože" (skloňování jako "moře") - něco jako božstvo, které může radit bytostem, které mu naslouchají.

PRAVIDLA:
1. Přijmeš vstup od hráče (jeho radu/příkaz bytosti)
2. Napíšeš narativní popis toho, co se stane (2-4 věty, styl Dračího doupěte)
3. Vygeneruješ JSON příkazy pro herní engine

FORMÁT ODPOVĚDI:
Odpověz PŘESNĚ v tomto formátu (včetně oddělovačů):

---NARRATIVE---
[Tvůj narativní popis toho, co se stane]

---COMMANDS---
{
  "commands": [
    {
      "entityId": "ID_ENTITY",
      "action": "move",
      "direction": {"x": -1, "y": 0},
      "steps": 50,
      "speed": 2
    }
  ]
}

DOSTUPNÉ AKCE:
1. "move" - pohyb entity
   - direction: {"x": číslo, "y": číslo} - směr pohybu (-1 až 1)
   - steps: počet kroků (max 200)
   - speed: rychlost (1-5)
   
2. "wait" - entita čeká na místě (pro rozhovory, přemýšlení, atd.)
   - steps: počet kroků čekání (1-100)
   - Používej pro scény, kde postavy mluví, přemýšlí nebo něco dělají na místě!
   
3. "disappear" - entita zmizí (smrt, útěk z mapy, atd.)
   - delay: počet kroků před zmizením (volitelné)

MAPA:
- Rozměr 100x100
- Souřadnice (0,0) je levý horní roh
- Entita mimo mapu automaticky zmizí

DŮLEŽITÉ:
- Scénář MUSÍ končit tím, že všechny entity zmizí (uteče, zemřou, odejdou)
- Když postavy mluví nebo něco dělají, MUSÍ to trvat nějaký čas - použij "wait" akci!
- Příklad: pokud si povídají, dej oběma "wait" s steps: 30-50, pak teprve další akce
- Piš česky
- Buď kreativní ale stručný v narativu
- JSON musí být validní
"""


class Agent:
    """AI Agent using Gemini."""
    
    def __init__(self):
        config = get_config()
        genai.configure(api_key=config["gemini"]["api_key"])
        self.model_name = config["gemini"]["model"]
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"Agent initialized with model: {self.model_name}")
    
    def test_connection(self) -> str:
        """Test connection to Gemini API."""
        try:
            response = self.model.generate_content("Řekni 'Ó bože funguje!'")
            return response.text
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return f"Error: {e}"
    
    def process_input(self, user_input: str, scenario: Scenario) -> AgentResponse:
        """
        Process user input and generate response.
        Returns narrative text and engine commands.
        """
        logger.info(f"Processing input: {user_input[:50]}...")
        
        # Build context about entities
        entity_info = []
        for e in scenario.entities:
            status = "naslouchá hráči (bože)" if e.listensToPlayer else "nenaslouchá hráči"
            entity_info.append(
                f"- {e.name} (ID: {e.id}): pozice ({e.position.x}, {e.position.y}), "
                f"{status}, {e.properties.character}, cíl: {e.properties.goals}"
            )
        
        prompt = f"""SCÉNÁŘ: {scenario.name}
{scenario.description}

BYTOSTI:
{chr(10).join(entity_info)}

VSTUP HRÁČE (rada bytosti, která mu naslouchá): {user_input}

Vygeneruj odpověď podle pravidel. Nezapomeň použít "wait" akci, pokud postavy mluví nebo dělají něco na místě!"""

        logger.debug(f"Full prompt:\n{prompt}")

        try:
            response = self.model.generate_content(
                [{"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]}]
            )
            
            logger.debug(f"Raw response:\n{response.text}")
            
            return self._parse_response(response.text)
            
        except Exception as e:
            logger.exception(f"Error processing input: {e}")
            return AgentResponse(
                narrative=f"Nastala chyba při komunikaci s božskou mocí: {e}",
                commands=EngineCommands(commands=[]),
                error=str(e)
            )
    
    def _parse_response(self, response_text: str) -> AgentResponse:
        """Parse the structured response from Gemini."""
        try:
            # Extract narrative
            narrative = ""
            narrative_match = re.search(r'---NARRATIVE---\s*(.*?)\s*---COMMANDS---', response_text, re.DOTALL)
            if narrative_match:
                narrative = narrative_match.group(1).strip()
            else:
                # Fallback: try to find narrative before JSON
                parts = response_text.split('{', 1)
                if len(parts) > 1:
                    narrative = parts[0].strip()
            
            # Extract JSON commands
            json_match = re.search(r'\{[\s\S]*"commands"[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                commands_data = json.loads(json_str)
                commands = EngineCommands(**commands_data)
                logger.info(f"Parsed {len(commands.commands)} commands")
            else:
                logger.warning("No commands found in response")
                commands = EngineCommands(commands=[])
            
            return AgentResponse(
                narrative=narrative if narrative else "Božská moc mlčí...",
                commands=commands
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nResponse was: {response_text[:500]}")
            return AgentResponse(
                narrative="Božská moc zaváhala... (chyba v odpovědi)",
                commands=EngineCommands(commands=[]),
                error=f"JSON parse error: {e}"
            )
        except Exception as e:
            logger.exception(f"Parse error: {e}")
            return AgentResponse(
                narrative="Něco se pokazilo...",
                commands=EngineCommands(commands=[]),
                error=str(e)
            )


# Singleton instance
_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


def reset_agent() -> None:
    """Reset agent instance (call after config change)."""
    global _agent
    _agent = None
    logger.info("Agent reset - will reinitialize on next use")
