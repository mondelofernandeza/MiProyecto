import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [usuario, setUsuario] = useState("");
  const [contraseña, setContraseña] = useState("");
  const [autenticado, setAutenticado] = useState(false);
  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [temaOscuro, setTemaOscuro] = useState(false);

  useEffect(() => {
    document.body.classList.toggle("dark", temaOscuro);
  }, [temaOscuro]);

  const iniciarReconocimientoVoz = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("❌ Tu navegador no soporta reconocimiento por voz.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log("🎙️ Escuchando...");
    };

    recognition.onerror = (event) => {
      console.error("Error en reconocimiento:", event.error);
    };

    recognition.onresult = (event) => {
      const texto = event.results[0][0].transcript;
      console.log("🎧 Texto reconocido:", texto);
      setPregunta(texto);
    };

    recognition.start();
  };

  const hacerLogin = () => {
    if (usuario === "admin" && contraseña === "1234") {
      setAutenticado(true);
    } else {
      alert("❌ Usuario o contraseña incorrectos");
    }
  };

  const hacerPregunta = async () => {
    if (!pregunta.trim()) return;

    setCargando(true);
    setError(null);
    setRespuesta(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/preguntar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ pregunta }),
      });

      const data = await response.json();

      if (response.ok) {
        setRespuesta(data);
      } else {
        setError(data.detail || "Error al procesar la pregunta");
      }
    } catch (err) {
      setError("❌ No se pudo conectar con el servidor");
    } finally {
      setCargando(false);
    }
  };

  const alternarTema = () => {
    setTemaOscuro((prev) => !prev);
  };

  if (!autenticado) {
    return (
      <div className="login-container">
        <h1>🔐 Iniciar sesión</h1>
        <input
          type="text"
          placeholder="Usuario"
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={contraseña}
          onChange={(e) => setContraseña(e.target.value)}
        />
        <button onClick={hacerLogin}>Entrar</button>
      </div>
    );
  }

  return (
    <div className="container">
      <button className="tema-toggle" onClick={alternarTema}>
        {temaOscuro ? "☀️ Modo claro" : "🌙 Modo oscuro"}
      </button>

      <h1>🎬 Chatbot de Cine IA</h1>
      <input
        autoFocus
        type="text"
        placeholder="Escribe tu pregunta sobre películas..."
        value={pregunta}
        onChange={(e) => setPregunta(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            hacerPregunta();
          }
        }}
      />
      <div className="botones">
        <button onClick={hacerPregunta}>Preguntar</button>
        <button onClick={iniciarReconocimientoVoz}>🎙️</button>
      </div>

      {cargando && <p className="pensando">🤔 Pensando...</p>}
      {error && <p className="error">{error}</p>}

      {respuesta?.respuesta_ia && (
        <div className="respuesta-ia">
          <p>{respuesta.respuesta_ia}</p>
        </div>
      )}

      {respuesta?.peliculas && respuesta.peliculas.length > 0 && (
        <div className="respuesta">
          {respuesta.peliculas.map((peli, i) => (
            <div className="pelicula" key={i}>
              <h3>{peli.titulo}</h3>
              <p><strong>Descripción:</strong> {peli.descripcion}</p>
              <p><strong>Puntuación:</strong> {peli.puntuacion}</p>
              <p><strong>Géneros:</strong> {peli.generos.join(", ")}</p>
              <p><strong>Director:</strong> {peli.director}</p>
              <p><strong>Actores:</strong> {peli.actores.join(", ")}</p>
              <p><strong>Año:</strong> {peli.año}</p>
            </div>
          ))}
        </div>
      )}

      {respuesta?.peliculas?.length === 0 && (
        <p className="alerta">⚠️ No se encontraron películas que coincidan con tu búsqueda.</p>
      )}
    </div>
  );
}

export default App;
