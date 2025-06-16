from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import iniciar_chat_con_pregunta

app = FastAPI()

# Permitir acceso desde el frontend (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para la petición
class PreguntaRequest(BaseModel):
    pregunta: str

# Ruta para procesar las preguntas
@app.post("/preguntar")
async def preguntar(req: PreguntaRequest):
    resultado = iniciar_chat_con_pregunta(req.pregunta)
    return resultado
