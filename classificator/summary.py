import json
from google import genai
from google.genai import types

API_KEY = "AIzaSyBtPyuUZDk1ELOVqMUJsAb93WpYETgZXrs"
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
        "summary": "Выжимка в 1 предложение"
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