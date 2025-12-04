import requests
import json

url = "http://localhost:8000/api/tobe/generate"
data = {
    "classified_data": None,
    "segmented_data": [
        {
            "id": 1,
            "nombre": "Actividad de prueba",
            "descripcion": "Descripción de prueba",
            "tiempo_promedio_min": 10,
            "clasificacion_lean": "VA"
        }
    ],
    "api_key": "test_key_invalid",  
    "contexto_proceso": "Proceso de prueba"
}

try:
    print("Enviando solicitud al endpoint TO-BE...")
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
