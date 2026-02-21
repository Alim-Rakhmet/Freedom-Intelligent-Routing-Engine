from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date
from uuid import UUID
from enum import Enum

# --- Перечисления (Enums) для строгих бизнес-правил ---

class Segment(str, Enum):
    MASS = "Mass"
    VIP = "VIP"
    PRIORITY = "Priority"

class Position(str, Enum):
    SPEC = "Спец"
    LEAD_SPEC = "Ведущий спец"
    CHIEF_SPEC = "Глав спец"

# --- Основные классы данных ---

@dataclass
class BusinessUnit:
    """Офис (Бизнес-единица)"""
    name: str
    address: str

@dataclass
class Manager:
    """Менеджер"""
    full_name: str
    position: Position
    skills: List[str]  # Ожидается список, например: ["VIP", "ENG", "KZ"]
    business_unit: BusinessUnit
    current_load: int = 0

@dataclass
class Ticket:
    """Обращение клиента"""
    client_guid: UUID
    gender: str
    birth_date: date
    segment: Segment
    description: str
    
    # Гео-данные (Адрес)
    country: str
    region: str
    city: str
    street: str
    house: str
    
    # Вложения (список путей к файлам или URL)
    attachments: Optional[List[str]] = field(default_factory=list)
    
    # Поля под AI-обогащение (можно заполнять позже в процессе пайплайна)
    ai_type: Optional[str] = None
    ai_sentiment: Optional[str] = None
    ai_priority: Optional[int] = None
    ai_language: str = "RU"
    ai_summary: Optional[str] = None