from django.core.exceptions import ValidationError
import re

def validate_strong_password(value):
    """
    Validiert starkes Passwort:
    - Mindestens 12 Zeichen
    - Mindestens 1 Großbuchstabe
    - Mindestens 1 Kleinbuchstabe
    - Mindestens 1 Zahl
    - Mindestens 1 Sonderzeichen
    """
    if len(value) < 12:
        raise ValidationError('Passwort muss mindestens 12 Zeichen lang sein.')
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError('Passwort muss mindestens einen Großbuchstaben enthalten.')
    
    if not re.search(r'[a-z]', value):
        raise ValidationError('Passwort muss mindestens einen Kleinbuchstaben enthalten.')
    
    if not re.search(r'[0-9]', value):
        raise ValidationError('Passwort muss mindestens eine Zahl enthalten.')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError('Passwort muss mindestens ein Sonderzeichen enthalten (!@#$%^&* etc.).')