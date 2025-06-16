import json
import os
import unicodedata
from extractor_llm import extraer_filtros_llm
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Cargar clave desde .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Modelo de embeddings
modelo_embeddings = SentenceTransformer("all-MiniLM-L6-v2")

# Cargar películas y sus embeddings
def cargar_peliculas(ruta_json=None):
    if ruta_json is None:
        ruta_json = os.path.join(os.path.dirname(__file__), "peliculas_enriquecidas.json")
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)

ruta_embeddings = os.path.join(os.path.dirname(__file__), "embeddings_peliculas_completo.json")
with open(ruta_embeddings, "r", encoding="utf-8") as f:
    data_embeddings = json.load(f)

matriz_embeddings = np.array([p["embedding"] for p in data_embeddings])
peliculas_embedding = data_embeddings

def normalizar(texto):
    if not texto:
        return ""
    return unicodedata.normalize('NFKD', texto.lower()).encode('ascii', 'ignore').decode('utf-8')

def filtrar_peliculas(peliculas, filtros):
    resultado = []

    actor_filtro = filtros.get("actor")
    director_filtro = filtros.get("director")
    genero_filtro = filtros.get("genero")
    año_filtro = filtros.get("año")
    numero_filtro = filtros.get("numero")

    for peli in peliculas:
        if actor_filtro:
            actores_filtro = actor_filtro if isinstance(actor_filtro, list) else [actor_filtro]
            actores_normalizados = [normalizar(a) for a in peli["actores"]]
            if not all(normalizar(nombre) in actores_normalizados for nombre in actores_filtro):
                continue

        if director_filtro:
            if normalizar(director_filtro) != normalizar(peli["director"]):
                continue

        if genero_filtro:
            generos_normalizados = [normalizar(g) for g in peli["generos"]]
            if normalizar(genero_filtro) not in generos_normalizados:
                continue

        if año_filtro:
            if isinstance(año_filtro, (list, tuple)):
                if not (año_filtro[0] <= int(peli["año"]) <= año_filtro[1]):
                    continue
            elif str(peli["año"]) != str(año_filtro):
                continue

        resultado.append(peli)

    resultado.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultado[:numero_filtro] if numero_filtro is not None else resultado

def buscar_parecidas_a(pelicula_titulo, top_k=5):
    idx_objetivo = None
    for i, p in enumerate(peliculas_embedding):
        if normalizar(p["titulo"]) == normalizar(pelicula_titulo):
            idx_objetivo = i
            break
    if idx_objetivo is None:
        return []

    emb_objetivo = matriz_embeddings[idx_objetivo]
    similitudes = cosine_similarity([emb_objetivo], matriz_embeddings)[0]
    indices_ordenados = np.argsort(similitudes)[::-1]

    resultados = []
    for idx in indices_ordenados:
        if idx != idx_objetivo:
            resultados.append(peliculas_embedding[idx])
        if len(resultados) >= top_k:
            break
    return resultados

def generar_respuesta_conversacional(pregunta: str, peliculas: list) -> str:
    if not peliculas:
        return "No he encontrado películas que encajen con tu búsqueda. ¿Quieres probar con otra pregunta?"

    contexto = "\n\n".join([
        f"Título: {p['titulo']}\n"
        f"Descripción: {p['descripcion']}\n"
        f"Géneros: {', '.join(p['generos'])}\n"
        f"Director: {p['director']}\n"
        f"Actores: {', '.join(p['actores'])}\n"
        f"Año: {p['año']}"
        for p in peliculas
    ])

    prompt = f"""
Eres un asistente experto en cine. El usuario te ha hecho la siguiente pregunta:

"{pregunta}"

Estas son las películas relevantes encontradas por el sistema:

{contexto}

Redacta una respuesta amable, cercana y profesional. Introduce brevemente, comenta con entusiasmo por qué podrían gustar las películas y finaliza animando a verlas. Usa lenguaje natural, no repitas la pregunta ni hagas listas frías.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error al generar la respuesta conversacional: {e}"

def iniciar_chat():
    peliculas = cargar_peliculas()
    historial = []

    print("🎬 Bienvenido al Chatbot de Cine IA (escribe 'salir' para terminar)")

    while True:
        pregunta = input("\n❓ Pregunta sobre películas (o 'salir'): ")
        if pregunta.lower() == "salir":
            break

        if "parecidas a" in pregunta.lower():
            titulo = pregunta.lower().split("parecidas a")[-1].strip().strip("'\"")
            similares = buscar_parecidas_a(titulo, top_k=5)
            respuesta = generar_respuesta_conversacional(pregunta, similares)
            print(f"\n🤖 {respuesta}")
            mostrar_peliculas(similares)
            continue

        contexto = "\n".join([f"Pregunta: {h['pregunta']}\nFiltros: {h['filtros']}" for h in historial])
        filtros = extraer_filtros_llm(pregunta, peliculas, contexto=contexto)

        historial.append({"pregunta": pregunta, "filtros": filtros})

        if "filtros" in filtros:
            filtros = filtros["filtros"]

        resultado = filtrar_peliculas(peliculas, filtros)
        respuesta_ia = generar_respuesta_conversacional(pregunta, resultado)

        print(f"\n🤖 {respuesta_ia}")
        mostrar_peliculas(resultado)

def mostrar_peliculas(peliculas):
    for i, peli in enumerate(peliculas, 1):
        print(f"\n🎬 Película {i}:")
        print(f"🎬 Título: {peli['titulo']}")
        print(f"📝 Descripción: {peli['descripcion']}")
        print(f"⭐ Puntuación: {peli['puntuacion']}")
        print(f"🎭 Géneros: {', '.join(peli['generos'])}")
        print(f"🎬 Director: {peli['director']}")
        print(f"👥 Actores: {', '.join(peli['actores'])}")
        print(f"📅 Año: {peli['año']}")

def iniciar_chat_con_pregunta(pregunta):
    print("❓ Pregunta recibida:", pregunta)

    if "parecidas a" in pregunta.lower():
        titulo = pregunta.lower().split("parecidas a")[-1].strip().strip("'\"")
        similares = buscar_parecidas_a(titulo, top_k=5)
        respuesta = generar_respuesta_conversacional(pregunta, similares)
        return {"respuesta_ia": respuesta, "peliculas": similares}

    peliculas = cargar_peliculas()
    filtros = extraer_filtros_llm(pregunta, peliculas)
    print("🧠 Filtros generados:", filtros)

    if "filtros" in filtros:
        filtros = filtros["filtros"]

    resultado = filtrar_peliculas(peliculas, filtros)
    respuesta_ia = generar_respuesta_conversacional(pregunta, resultado)

    return {"respuesta_ia": respuesta_ia, "peliculas": resultado}

if __name__ == "__main__":
    iniciar_chat()
