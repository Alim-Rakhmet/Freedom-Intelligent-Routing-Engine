import json
import time
from google import genai
from google.genai import types

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
                model='gemini-2.5-flash-lite', # <--- Указали Flash Lite
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            
            # Получаем текст ответа и превращаем в словарь
            result_dict = json.loads(response.text)
            
            # Опционально: можно добавить time.sleep(4) прямо сюда, 
            # чтобы делать паузы между запросами и вообще не доводить до 429 ошибки
            
            return result_dict
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⏳ Уперлись в квоту. Ждем 60 секунд (попытка {attempt + 1}/{max_retries})...")
                time.sleep(60) # Спим минуту, пока Google не обновит счетчик
            else:
                print(f"❌ Ошибка при обращении к API: {e}")
                return {}
                
    return {}

# --- Тестируем ---
if __name__ == "__main__":
    sample_text = "Сәлеметсіз бе! Менің картамнан белгісіз біреулер 50 000 теңге шешіп алды, тез бұғаттаңыздаршы!"
    
    print("Запускаем анализ...")
    result = analyze_ticket(sample_text)
    print("Результат анализа:")
    print(json.dumps(result, indent=4, ensure_ascii=False))