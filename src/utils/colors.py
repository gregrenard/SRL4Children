"""
Safety Readiness Level for Children - LLM-based Evaluation
Translating Design Principles into Automated guardrails and replay alignement for child safety.
Author: Gregory Renard (with GenAI: Claude, Gemini, Codex)
Organization: Everyone.AI | Year: 2025
For the well-being and safety of our children
"""

import os
import sys

class Colors:
    """Codes ANSI pour couleurs du terminal"""
    
    # Couleurs de base
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Couleurs vives
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'
    
    @classmethod
    def is_supported(cls):
        """Vérifie si les couleurs sont supportées par le terminal"""
        return (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            os.environ.get('TERM') != 'dumb' and
            os.environ.get('NO_COLOR') is None
        )

def colorize(text: str, color: str) -> str:
    """Ajoute une couleur au texte si supporté"""
    if Colors.is_supported():
        return f"{color}{text}{Colors.RESET}"
    return text

# Fonctions de commodité pour les différents types de messages
def header(text: str) -> str:
    """En-tête principal - bleu vif gras"""
    return colorize(f"{Colors.BOLD}{text}", Colors.BRIGHT_BLUE)

def info(text: str) -> str:
    """Information générale - blanc"""
    return colorize(text, Colors.WHITE)

def success(text: str) -> str:
    """Succès - vert vif"""
    return colorize(text, Colors.BRIGHT_GREEN)

def warning(text: str) -> str:
    """Avertissement - jaune"""
    return colorize(text, Colors.YELLOW)

def error(text: str) -> str:
    """Erreur - rouge vif"""
    return colorize(text, Colors.BRIGHT_RED)

def progress(text: str) -> str:
    """Progression - cyan"""
    return colorize(text, Colors.CYAN)

def prompt_info(text: str) -> str:
    """Information sur prompt - magenta"""
    return colorize(text, Colors.MAGENTA)

def model_info(text: str) -> str:
    """Information sur modèle - bleu"""
    return colorize(text, Colors.BLUE)

def judge_info(text: str) -> str:
    """Information du judge - jaune vif"""
    return colorize(text, Colors.BRIGHT_YELLOW)

def config_info(text: str) -> str:
    """Information de configuration - cyan vif"""
    return colorize(text, Colors.BRIGHT_CYAN)

def mode_info(text: str) -> str:
    """Information sur mode - magenta vif"""
    return colorize(text, Colors.BRIGHT_MAGENTA)

def separator(char: str = "-", length: int = 50) -> str:
    """Séparateur coloré - gris"""
    return colorize(char * length, Colors.BRIGHT_BLACK)