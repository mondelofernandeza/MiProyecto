import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env desde la carpeta backend explícitamente
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extraer_filtros_llm(pregunta, peliculas, contexto=""):
    ejemplos = [
        {
            "pregunta": "Quiero ver 3 películas de terror dirigidas por James Wan",
            "filtros": {
                "actor": None,
                "director": "James Wan",
                "genero": "Terror",
                "año": None,
                "numero": 3
            }
        },
        {
            "pregunta": "Dime las 2 películas más famosas de Leonardo DiCaprio",
            "filtros": {
                "actor": ["Leonardo DiCaprio"],
                "director": None,
                "genero": None,
                "año": None,
                "numero": 2
            }
        },
        {
            "pregunta": "Películas con Leonardo DiCaprio y Cillian Murphy",
            "filtros": {
                "actor": ["Leonardo DiCaprio", "Cillian Murphy"],
                "director": None,
                "genero": None,
                "año": None,
                "numero": None
            }
        }
    ]

    prompt = f"""
Eres un asistente que ayuda a extraer filtros de búsqueda de películas en formato JSON.
Transforma una consulta de usuario en un diccionario JSON con los siguientes campos:

- "actor": lista de nombres si hay más de uno, o null si no se menciona ninguno
- "director": nombre del director si se menciona, si no, null
- "genero": solo uno (en español), si no hay, null
- "año": número o rango (como [2000, 2010]), si no hay, null
- "numero": cuántas películas quiere el usuario (por defecto 5, pero si dice "todas", se pone null)

Ejemplos:
{json.dumps(ejemplos, indent=4, ensure_ascii=False)}

Historial reciente de conversación (si hay):
{contexto}

Ahora, analiza esta nueva consulta y responde solo con el JSON:

\"\"\"{pregunta}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        contenido = response.choices[0].message.content.strip()
        filtros = json.loads(contenido)

        if isinstance(filtros.get("numero"), str) and filtros["numero"].lower() == "todas":
            filtros["numero"] = None

        print("🧠 Filtros extraídos:", filtros)
        return filtros
    except Exception as e:
        print("⚠️ Error al interpretar con GPT:", e)
        return {
            "actor": None,
            "director": None,
            "genero": None,
            "año": None,
            "numero": 5
        }
