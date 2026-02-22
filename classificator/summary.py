import json
import time
import logging  # <--- 1. Добавили импорт модуля логирования
from google import genai
from google.genai import types

# <--- 2. Настроили формат вывода логов (время, уровень, сообщение)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ВНИМАНИЕ: Старайся не светить свои реальные API-ключи в чатах, их могут скопировать боты. 
# Лучше перевыпусти тот ключ, который ты кидал выше, в Google AI Studio!
API_KEY = "AIzaSyD-WNU8J3KlzY-FKEeTH-npAVCweNXroHE"
client = genai.Client(api_key=API_KEY)

def analyze_ticket(description: str) -> dict:
    
    prompt = f"""
    Проанализируй обращение клиента и верни ответ в формате JSON.
    Текст обращения: "{description}"
    
    Схема JSON:
    {{
        "type": "одна из: Жалоба, Смена данных, Консультация, Претензия, Неработоспособность приложения, Мошеннические действия, Спам",
        "sentiment": "Позитивный, Нейтральный или Негативный",
        "priority": целое число от 1 до 10,
        "language": "RU, KZ или ENG",
        "summary": "Краткая выжимка сути обращения (1-2 предложения) + рекомендация по дальнейшим действиям для менеджера"
    }}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            
            # Получаем текст ответа и превращаем в словарь
            result_dict = json.loads(response.text)
            
            # <--- 3. ДОБАВЛЕН ЛОГ С ВЫВОДОМ JSON
            logging.info(f"Сгенерированный JSON от Gemini:\n{json.dumps(result_dict, indent=4, ensure_ascii=False)}")
            
            return result_dict
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # Заменили print на logging.warning
                logging.warning(f"⏳ Уперлись в квоту. Ждем 60 секунд (попытка {attempt + 1}/{max_retries})...")
                time.sleep(60) 
            else:
                # Заменили print на logging.error
                logging.error(f"❌ Ошибка при обращении к API: {e}")
                return {}
                
    return {}

# --- Тестируем ---
if __name__ == "__main__":
    sample_text = "Сәлеметсіз бе! Менің картамнан белгісіз біреулер 50 000 теңге шешіп алды, тез бұғаттаңыздаршы!"
    
    logging.info("Запускаем анализ тестового обращения...")
    result = analyze_ticket(sample_text)
    # Нижние принты можно даже убрать, так как функция теперь сама всё логирует