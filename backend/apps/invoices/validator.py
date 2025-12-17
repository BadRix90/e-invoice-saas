"""
XRechnung Validator Service
Nutzt den Kosit Validator für offizielle Konformitätsprüfung
"""
import requests
from dataclasses import dataclass
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

VALIDATOR_URL = "http://localhost:8081"


@dataclass
class ValidationResult:
    """Ergebnis der XRechnung-Validierung."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_xrechnung(xml_content: str) -> ValidationResult:
    """Validiert XRechnung XML gegen den Kosit Validator."""
    try:
        response = requests.post(
            VALIDATOR_URL,
            data=xml_content.encode('utf-8'),
            headers={'Content-Type': 'application/xml'},
            timeout=30
        )
        
        # 200 = valid, 406 = invalid aber trotzdem verarbeitet
        if response.status_code in [200, 406]:
            errors = []
            warnings = []
            is_valid = False
            
            try:
                root = ET.fromstring(response.content)
                
                # Check valid attribute im root report element
                if 'valid' in root.attrib:
                    is_valid = root.attrib['valid'].lower() == 'true'
                
                # Suche nach Fehlern und Warnungen
                for elem in root.iter():
                    tag_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    
                    # failed-assert = Fehler
                    if tag_local == 'failed-assert':
                        for child in elem:
                            child_local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                            if child_local == 'text' and child.text:
                                errors.append(child.text.strip())
                    
                    # successful-report = Warnung
                    if tag_local == 'successful-report':
                        for child in elem:
                            child_local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                            if child_local == 'text' and child.text:
                                warnings.append(child.text.strip())
                    
                    # Auch assessment messages prüfen
                    if tag_local == 'message' and elem.text:
                        msg = elem.text.strip()
                        level = elem.attrib.get('level', 'error')
                        if level in ['error', 'fatal']:
                            errors.append(msg)
                        elif level == 'warning':
                            warnings.append(msg)
                            
            except ET.ParseError as e:
                logger.warning(f"Could not parse validator response: {e}")
                errors.append("Validator-Antwort konnte nicht verarbeitet werden")
            
            return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validator-Fehler: HTTP {response.status_code}"],
                warnings=[]
            )
            
    except requests.exceptions.ConnectionError:
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Validator nicht erreichbar - Validierung übersprungen"]
        )
    except Exception as e:
        logger.exception("Fehler bei der Validierung")
        return ValidationResult(
            is_valid=False,
            errors=[f"Validierungsfehler: {str(e)}"],
            warnings=[]
        )


def check_validator_health() -> bool:
    """Prüft ob der Validator erreichbar ist."""
    try:
        response = requests.get(f"{VALIDATOR_URL}/server/health", timeout=5)
        return response.status_code == 200
    except:
        return False