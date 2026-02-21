import json
from openai import OpenAI

# Вставь сюда свой API-ключ от DeepSeek
API_KEY = "sk-5447ea793c4d4207ac4a8777eebb9060"

# Инициализируем клиент, переопределяя базовый URL на DeepSeek
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def analyze_ticket(description: str) -> dict:
    
    prompt = f"""
    Проанализируй обращение клиента и верни ответ строго в формате JSON.
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
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # Основная модель DeepSeek (V3)
            messages=[
                # Системный промпт помогает модели лучше держать формат
                {"role": "system", "content": "Ты полезный AI-ассистент. Твой ответ всегда должен быть валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}, # Жестко форсируем выдачу JSON
            temperature=0.1,
        )
        
        # Достаем текст ответа из структуры OpenAI и парсим его в словарь
        result_text = response.choices[0].message.content
        result_dict = json.loads(result_text)
        return result_dict
        
    except Exception as e:
        print(f"Ошибка при обращении к API DeepSeek: {e}")
        return {}

# --- Тестируем ---
if __name__ == "__main__":
    sample_text = "Сәлеметсіз бе! Менің картамнан белгісіз біреулер 50 000 теңге шешіп алды, тез бұғаттаңыздаршы!"
    
    result = analyze_ticket(sample_text)
    print("Результат анализа:")
    print(json.dumps(result, indent=4, ensure_ascii=False))