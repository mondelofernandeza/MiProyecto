from sentence_transformers import SentenceTransformer
import json
import os

ruta = os.path.join(os.path.dirname(__file__), "peliculas_enriquecidas.json")
with open(ruta, "r", encoding="utf-8") as f:
    peliculas = json.load(f)

# Inicializar el modelo
modelo = SentenceTransformer("all-MiniLM-L6-v2")

# Crear texto representativo para cada película
textos = [
    f"{p['titulo']}. {p['descripcion']} Géneros: {', '.join(p['generos'])}. Director: {p['director']}. Actores: {', '.join(p['actores'])}."
    for p in peliculas
]

# Generar los embeddings
embeddings = modelo.encode(textos, show_progress_bar=True)

# Guardar en un JSON
data = []

for i, peli in enumerate(peliculas):
    data.append({
        "id": peli["id"],
        "titulo": peli["titulo"],
        "descripcion": peli["descripcion"],
        "generos": peli["generos"],
        "director": peli["director"],
        "actores": peli["actores"],
        "año": peli["año"],
        "embedding": embeddings[i].tolist()
    })

with open("embeddings_peliculas_completo.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)