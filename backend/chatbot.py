import json
import os
import unicodedata
from extractor_llm import extraer_filtros_llm
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

modelo_embeddings = SentenceTransformer("all-MiniLM-L6-v2")

# Cargar películas y embeddings
ruta_datos = os.path.dirname(__file__)
with open(os.path.join(ruta_datos, "peliculas_enriquecidas.json"), "r", encoding="utf-8") as f:
    peliculas = json.load(f)

with open(os.path.join(ruta_datos, "embeddings_peliculas_completo.json"), "r", encoding="utf-8") as f:
    peliculas_embedding = json.load(f)
matriz_embeddings = np.array([p["embedding"] for p in peliculas_embedding])

# Ruta a usuarios.json
USUARIOS_FILE = os.path.join(ruta_datos, "usuarios.json")


def normalizar(texto):
    if not texto:
        return ""
    return unicodedata.normalize('NFKD', texto.lower()).encode('ascii', 'ignore').decode('utf-8')


def cargar_preferencias_usuario(nombre_usuario):
    if not os.path.exists(USUARIOS_FILE):
        return None

    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    for u in usuarios:
        if u["usuario"] == nombre_usuario:
            return u.get("preferencias", None)

    return None

def obtener_historial_usuario(nombre_usuario):
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    for u in usuarios:
        if u["usuario"] == nombre_usuario:
            pendientes = u.get("pendientes", [])
            vistas = u.get("vistas", [])
            no_deseadas = u.get("no_deseadas", [])

            def buscar_pelis_por_ids(ids):
                return [p for p in peliculas_embedding if p.get("id") in ids]

            return {
                "pendientes": buscar_pelis_por_ids(pendientes),
                "vistas": buscar_pelis_por_ids(vistas),
                "no_deseadas": buscar_pelis_por_ids(no_deseadas)
            }

    return {"pendientes": [], "vistas": [], "no_deseadas": []}


def _recomendar_por_historial(pregunta, peliculas_base, preferencias, ids_excluidos):
    
    print("🎥 IDs en historial del usuario:", [p["id"] for p in peliculas_base])
    print("🎯 IDs disponibles en embeddings:", [p["id"] for p in peliculas_embedding[:10]])

    if not peliculas_base:
        return {"respuesta_ia": "No encontré ninguna película en tu historial para darte recomendaciones.", "peliculas": []}

    # Obtener embeddings de las películas base
    base_embeddings = []
    for peli in peliculas_base:
        emb = next((p["embedding"] for p in peliculas_embedding if p["id"] == peli["id"]), None)
        if emb:
            base_embeddings.append(emb)

    if not base_embeddings:
        return {"respuesta_ia": "No encontré datos suficientes para generar recomendaciones.", "peliculas": []}

    # Calcular embedding promedio
    emb_promedio = np.mean(base_embeddings, axis=0)

    # Calcular similitud con todas las demás películas
    similitudes = cosine_similarity([emb_promedio], matriz_embeddings)[0]
    indices_ordenados = np.argsort(similitudes)[::-1]

    # Seleccionar películas más parecidas
    recomendadas = []
    for idx in indices_ordenados:
        peli = peliculas_embedding[idx]
        if peli["id"] in ids_excluidos:
            continue
        recomendadas.append(peli)
        if len(recomendadas) >= 10:
            break

    # Aplicar preferencias si existen
    if preferencias:
        recomendadas = priorizar_por_preferencias(recomendadas, preferencias)

    recomendadas = recomendadas[:5]

    respuesta = generar_respuesta_conversacional(pregunta, recomendadas)
    return {"respuesta_ia": respuesta, "peliculas": recomendadas}


def filtrar_peliculas(peliculas, filtros, ids_excluidos=None):
    if ids_excluidos is None:
        ids_excluidos = set()

    resultado = []

    actor_filtro = filtros.get("actor")
    director_filtro = filtros.get("director")
    genero_filtro = filtros.get("genero")
    año_filtro = filtros.get("año")
    numero_filtro = filtros.get("numero")

    for peli in peliculas:
        if peli.get("id") in ids_excluidos:
            continue

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

    resultado = [p for p in resultado if "puntuacion" in p]
    resultado.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultado, numero_filtro


def priorizar_por_preferencias(peliculas, preferencias):
    def calcular_score(peli):
        score = 0

        if preferencias.get("director_favorito") and normalizar(peli["director"]) == normalizar(preferencias["director_favorito"]):
            score += 2

        if preferencias.get("actores_favoritos"):
            actores_peli = [normalizar(a) for a in peli["actores"]]
            score += sum(1 for a in preferencias["actores_favoritos"] if normalizar(a) in actores_peli)

        if preferencias.get("generos_favoritos"):
            generos_peli = [normalizar(g) for g in peli["generos"]]
            score += sum(1 for g in preferencias["generos_favoritos"] if normalizar(g) in generos_peli)

        rango = preferencias.get("rango_años")
        if rango and isinstance(rango, list) and peli.get("año"):
            try:
                año = int(peli["año"])
                if rango[0] <= año <= rango[1]:
                    score += 1
            except:
                pass

        return score

    return sorted(peliculas, key=calcular_score, reverse=True)


def buscar_parecidas_a(pelicula_titulo, top_k=5, preferencias=None, ids_excluidos=None):
    if ids_excluidos is None:
        ids_excluidos = set()

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
        peli = peliculas_embedding[idx]
        if idx == idx_objetivo:
            continue
        if peli.get("id") in ids_excluidos:
            continue
        resultados.append(peli)
        if len(resultados) >= top_k:
            break

    if preferencias:
        resultados = priorizar_por_preferencias(resultados, preferencias)

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


def iniciar_chat_con_pregunta(pregunta, usuario):
    preferencias = cargar_preferencias_usuario(usuario)
    historial = []  # No se usa aún, pero se puede extender

    if any(pal in pregunta.lower() for pal in ["pendiente", "vista", "no deseada", "que marqué", "he visto"]):
        historial_usuario = obtener_historial_usuario(usuario)

        # Detectar sobre qué parte del historial se pregunta
        if "pendiente" in pregunta.lower():
            base = historial_usuario["pendientes"]
        elif "vista" in pregunta.lower():
            base = historial_usuario["vistas"]
        elif "no deseada" in pregunta.lower():
            base = historial_usuario["no_deseadas"]
        else:
            base = []

        if "parecidas" in pregunta.lower():
            todas_a_excluir = historial_usuario["vistas"] + historial_usuario["no_deseadas"] + base
            ids_excluidos = set(p["id"] for p in todas_a_excluir)
            return _recomendar_por_historial(pregunta, base, preferencias, ids_excluidos)

        # Extraer filtros del lenguaje natural
        filtros = extraer_filtros_llm(pregunta, base)
        if "filtros" in filtros:
            filtros = filtros["filtros"]

        resultado_filtrado, limite = filtrar_peliculas(base, filtros)

        if preferencias:
            resultado_filtrado = priorizar_por_preferencias(resultado_filtrado, preferencias)

        if limite is not None:
            resultado_filtrado = resultado_filtrado[:limite]

        respuesta_ia = generar_respuesta_conversacional(pregunta, resultado_filtrado)
        return {"respuesta_ia": respuesta_ia, "peliculas": resultado_filtrado}
    

    # Cargar exclusiones
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    vistas = []
    no_deseadas = []
    for u in usuarios:
        if u["usuario"] == usuario:
            vistas = u.get("vistas", [])
            no_deseadas = u.get("no_deseadas", [])
            break

    ids_excluidos = set(vistas + no_deseadas)

    print("❓ Pregunta recibida:", pregunta)

    if "parecidas a" in pregunta.lower():
        titulo = pregunta.lower().split("parecidas a")[-1].strip().strip("'\"")
        similares = buscar_parecidas_a(titulo, top_k=5, preferencias=preferencias, ids_excluidos=ids_excluidos)
        respuesta = generar_respuesta_conversacional(pregunta, similares)
        return {"respuesta_ia": respuesta, "peliculas": similares}

    filtros = extraer_filtros_llm(pregunta, peliculas)

    if "filtros" in filtros:
        filtros = filtros["filtros"]

    resultado_filtrado, limite = filtrar_peliculas(peliculas, filtros, ids_excluidos=ids_excluidos)

    if preferencias:
        resultado_filtrado = priorizar_por_preferencias(resultado_filtrado, preferencias)

    if limite is not None:
        resultado_filtrado = resultado_filtrado[:limite]

    respuesta_ia = generar_respuesta_conversacional(pregunta, resultado_filtrado)
    return {"respuesta_ia": respuesta_ia, "peliculas": resultado_filtrado}
