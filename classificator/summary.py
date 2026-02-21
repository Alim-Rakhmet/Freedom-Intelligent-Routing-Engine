import json
from google import genai
from google.genai import types

API_KEY = "AIzaSyApubIr9vqK9_F-qjM2WwLfBhKDKzO-Mp8"
client = genai.Client(api_key=API_KEY)

def analyze_ticket(description: str) -> dict:
    
    prompt = f"""
    Проанализируй обращение клиента и верни ответ в формате JSON.
    Текст обращения: "{description}"
    
    Схема JSON:
    {{
        "ai_type": "одна из: Жалоба, Смена данных, Консультация, Претензия, Неработоспособность приложения, Мошеннические действия, Спам",
        "ai_sentiment": "Позитивный, Нейтральный или Негативный",
        "ai_priority": целое число от 1 до 10,
        "ai_language": "RU, KZ или ENG",
        "ai_summary": "Выжимка в 1 предложение"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        
        # Получаем текст ответа и превращаем в словарь
        result_dict = json.loads(response.text)
        return result_dict
        
    except Exception as e:
        print(f"Ошибка при обращении к API: {e}")
        return {}

# --- Тестируем ---
if __name__ == "__main__":
    sample_text = "Сәлеметсіз бе! Менің картамнан белгісіз біреулер 50 000 теңге шешіп алды, тез бұғаттаңыздаршы!"
    
    result = analyze_ticket(sample_text)
    print("Результат анализа:")
    print(json.dumps(result, indent=4, ensure_ascii=False))