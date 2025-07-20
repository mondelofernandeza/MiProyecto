import requests
import os
from dotenv import load_dotenv
import json
from time import sleep
import time

# Cargar las variables de entorno
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def get_popular_movies(page=1):
    url = f"{BASE_URL}/movie/popular"
    params = {
        "api_key": API_KEY,
        "language": "es-ES",
        "page": page
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error en la solicitud:", response.status_code)
        return None

def get_movie_details(movie_id, reintentos=3):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "language": "es-ES",
        "append_to_response": "credits"
    }

    for intento in range(reintentos):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Error {response.status_code} en película {movie_id}. Intento {intento + 1}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Excepción en película {movie_id}: {e}. Intento {intento + 1}")

        time.sleep(1)  # Espera entre reintentos

    return {}  # Si falla todos los reintentos

def limpiar_y_enriquecer_datos(paginas=1, salida_json="peliculas_enriquecidas.json"):
    todas_peliculas = []
    for page in range(1, paginas + 1):
        data = get_popular_movies(page)
        if not data:
            continue

        for pelicula in data.get("results", []):
            movie_id = pelicula.get("id")
            detalles = get_movie_details(movie_id)
            sleep(0.3)  # Para no sobrecargar la API

            actores = [actor["name"] for actor in detalles.get("credits", {}).get("cast", [])[:5]]
            director = next((p["name"] for p in detalles.get("credits", {}).get("crew", []) if p["job"] == "Director"), None)
            generos = [g["name"] for g in detalles.get("genres", [])]

            pelicula_enriquecida = {
                "id": movie_id,
                "titulo": pelicula.get("title"),
                "descripcion": pelicula.get("overview"),
                "popularidad": pelicula.get("popularity"),
                "puntuacion": pelicula.get("vote_average"),
                "fecha_estreno": pelicula.get("release_date"),
                "año": pelicula.get("release_date", "")[:4],
                "generos": generos,
                "actores": actores,
                "director": director
            }
            todas_peliculas.append(pelicula_enriquecida)

    with open(salida_json, "w", encoding="utf-8") as f:
        json.dump(todas_peliculas, f, ensure_ascii=False, indent=4)

    print(f"✅ Se han guardado {len(todas_peliculas)} películas enriquecidas en '{salida_json}'.")

# Ejecutar el proceso para 2 páginas (40 películas)
limpiar_y_enriquecer_datos(paginas=200)
