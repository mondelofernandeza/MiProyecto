from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union
from chatbot import iniciar_chat_con_pregunta
import json
import os
from fastapi import Path

app = FastAPI()

# Permitir acceso desde el frontend (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USUARIOS_FILE = os.path.join(os.path.dirname(__file__), "usuarios.json")

# Crear el archivo de usuarios si no existe
if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# ------------------------------
# MODELOS
# ------------------------------

class PreguntaRequest(BaseModel):
    pregunta: str
    usuario: str

class UserData(BaseModel):
    usuario: str
    contraseña: str

# ------------------------------
# RUTAS DEL CHATBOT
# ------------------------------

@app.post("/preguntar")
async def preguntar(req: PreguntaRequest):
    resultado = iniciar_chat_con_pregunta(req.pregunta, req.usuario)
    return resultado

# ------------------------------
# RUTAS DE AUTENTICACIÓN
# ------------------------------

@app.post("/register")
def register(data: UserData):
    with open(USUARIOS_FILE, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)

        if any(u["usuario"] == data.usuario for u in usuarios):
            raise HTTPException(status_code=400, detail="Usuario ya existe")

        nuevo_usuario = {
            "usuario": data.usuario,
            "contraseña": data.contraseña,
            "preferencias": None
        }

        usuarios.append(nuevo_usuario)

        f.seek(0)
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
        f.truncate()

    return {"mensaje": "Usuario registrado correctamente"}

@app.post("/login")
def login(data: UserData):
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    usuario = next((u for u in usuarios if u["usuario"] == data.usuario and u["contraseña"] == data.contraseña), None)

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return {"mensaje": "Login correcto", "tiene_preferencias": usuario["preferencias"] is not None}

class PreferenciasData(BaseModel):
    usuario: str
    generos_favoritos: list
    actores_favoritos: list
    director_favorito: str
    rango_años: Union[list, str]

class MarcarPeliculaData(BaseModel):
    usuario: str
    pelicula_id: int

@app.post("/guardar-preferencias")
def guardar_preferencias(data: PreferenciasData):
    with open(USUARIOS_FILE, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)

        for u in usuarios:
            if u["usuario"] == data.usuario:
                u["preferencias"] = {
                    "generos_favoritos": data.generos_favoritos,
                    "actores_favoritos": data.actores_favoritos,
                    "director_favorito": data.director_favorito,
                    "rango_años": data.rango_años
                }
                break
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        f.seek(0)
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
        f.truncate()

    return {"mensaje": "Preferencias guardadas correctamente"}

@app.post("/marcar-vista")
def marcar_pelicula_vista(data: MarcarPeliculaData):
    with open(USUARIOS_FILE, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)

        for u in usuarios:
            if u["usuario"] == data.usuario:
                if "vistas" not in u:
                    u["vistas"] = []
                if data.pelicula_id not in u["vistas"]:
                    u["vistas"].append(data.pelicula_id)
                break
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        f.seek(0)
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
        f.truncate()

    return {"mensaje": "Película marcada como vista"}

@app.post("/marcar-no-deseada")
def marcar_pelicula_no_deseada(data: MarcarPeliculaData):
    with open(USUARIOS_FILE, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)

        for u in usuarios:
            if u["usuario"] == data.usuario:
                if "no_deseadas" not in u:
                    u["no_deseadas"] = []
                if data.pelicula_id not in u["no_deseadas"]:
                    u["no_deseadas"].append(data.pelicula_id)
                break
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        f.seek(0)
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
        f.truncate()

    return {"mensaje": "Película marcada como no deseada"}


@app.get("/preferencias/{usuario}")
def obtener_preferencias(usuario: str = Path(..., min_length=1)):
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    for u in usuarios:
        if u["usuario"] == usuario:
            return {
                **(u.get("preferencias", {})),
                "pendientes": u.get("pendientes", [])
            }

    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.post("/marcar-pendiente")
def marcar_pendiente(data: dict):
    usuario = data["usuario"]
    pelicula_id = data["pelicula_id"]

    with open(USUARIOS_FILE, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)
        for u in usuarios:
            if u["usuario"] == usuario:
                u.setdefault("pendientes", [])
                if pelicula_id not in u["pendientes"]:
                    u["pendientes"].append(pelicula_id)
                break
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        f.seek(0)
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
        f.truncate()

    return {"mensaje": "Película marcada como pendiente"}

@app.post("/desmarcar-pendiente")
def desmarcar_pendiente(data: dict):
    usuario = data["usuario"]
    pelicula_id = data["pelicula_id"]

    with open(USUARIOS_FILE, "r+", encoding="utf-8") as f:
        usuarios = json.load(f)
        for u in usuarios:
            if u["usuario"] == usuario:
                u.setdefault("pendientes", [])
                if pelicula_id in u["pendientes"]:
                    u["pendientes"].remove(pelicula_id)
                break
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        f.seek(0)
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
        f.truncate()

    return {"mensaje": "Película desmarcada como pendiente"}

@app.get("/historial/{usuario}")
def obtener_historial(usuario: str = Path(..., min_length=1)):
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    with open(os.path.join(os.path.dirname(__file__), "peliculas_enriquecidas.json"), "r", encoding="utf-8") as f:
        peliculas = json.load(f)

    for u in usuarios:
        if u["usuario"] == usuario:
            ids_vistas = set(u.get("vistas", []))
            ids_no_deseadas = set(u.get("no_deseadas", []))
            ids_pendientes = set(u.get("pendientes", []))

            def filtrar_por_ids(ids):
                return [p for p in peliculas if p["id"] in ids]

            return {
                "vistas": filtrar_por_ids(ids_vistas),
                "no_deseadas": filtrar_por_ids(ids_no_deseadas),
                "pendientes": filtrar_por_ids(ids_pendientes),
            }

    raise HTTPException(status_code=404, detail="Usuario no encontrado")
