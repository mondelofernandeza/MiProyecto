import { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [modo, setModo] = useState("login"); // "login" o "registro"
  const [usuario, setUsuario] = useState("");
  const [contraseña, setContraseña] = useState("");
  const [usuarioLogueado, setUsuarioLogueado] = useState(null);
  const [tienePreferencias, setTienePreferencias] = useState(false);

  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [temaOscuro, setTemaOscuro] = useState(false);

  const [generos, setGeneros] = useState([]);
  const [actores, setActores] = useState("");
  const [director, setDirector] = useState("");
  const [añoInicio, setAñoInicio] = useState("");
  const [añoFin, setAñoFin] = useState("");

  const [usarTodosLosAnios, setUsarTodosLosAnios] = useState(false);

  const [peliculasOcultas, setPeliculasOcultas] = useState([]);

  const [modoPreferencias, setModoPreferencias] = useState(false);
  const [pendientes, setPendientes] = useState([]);

  const [modoHistorial, setModoHistorial] = useState(false);
  const [historial, setHistorial] = useState({ vistas: [], pendientes: [], no_deseadas: [] });

  const [ultimaPregunta, setUltimaPregunta] = useState("");


  useEffect(() => {
    document.body.classList.toggle("dark", temaOscuro);
  }, [temaOscuro]);

  useEffect(() => {
    const userGuardado = localStorage.getItem("usuario");
    if (userGuardado) {
      setUsuarioLogueado(userGuardado);
      setTienePreferencias(true); // O mejor: podrías hacer una llamada a `/login` o `/preferencias`
    }
  }, []);

  const cambiarModo = () => {
    setModo(modo === "login" ? "registro" : "login");
    setError(null);
  };

  const cerrarSesion = () => {
    setUsuarioLogueado(null);
    setTienePreferencias(false);
    setModoPreferencias(false);
    setModoHistorial(false);
    setRespuesta(null);
    localStorage.removeItem("usuario");
  };

  const handleAuth = async () => {
    if (!usuario || !contraseña) return;

    const endpoint = modo === "login" ? "/login" : "/register";

    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario, contraseña }),
      });

      const data = await response.json();

      if (response.ok) {
        setUsuarioLogueado(usuario);
        localStorage.setItem("usuario", usuario);
        setTienePreferencias(data.tiene_preferencias || false);

        // 🔽 Cargar películas pendientes tras login
        try {
          const prefRes = await fetch(`http://127.0.0.1:8000/preferencias/${usuario}`);
          const dataPref = await prefRes.json();
          setPendientes(dataPref.pendientes || []);
        } catch {
          setPendientes([]);
        }

      } else {
        setError(data.detail || "Error de autenticación");
      }
    } catch (err) {
      setError("❌ No se pudo conectar con el servidor");
    }
  };


  const cargarHistorial = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/historial/${usuarioLogueado}`);
      const data = await res.json();
      if (res.ok) {
        setHistorial(data);
        setModoHistorial(true);
      } else {
        alert("❌ Error al cargar el historial");
      }
    } catch {
      alert("❌ Error al conectar con el servidor");
    }
  };

  const actualizarRecomendaciones = async () => {
    if (!ultimaPregunta.trim()) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/preguntar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ pregunta: ultimaPregunta, usuario: usuarioLogueado }),
      });

      const data = await response.json();
      if (response.ok) {
        setRespuesta(data);
      }
    } catch {
      // puedes mostrar error si quieres
    }
  };


  const hacerPregunta = async () => {
    if (!pregunta.trim()) return;

    setCargando(true);
    setError(null);
    setRespuesta(null);
    setUltimaPregunta(pregunta);

    try {
      const response = await fetch("http://127.0.0.1:8000/preguntar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ pregunta, usuario: usuarioLogueado }),
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

  const marcarPelicula = async (peliculaId, tipo) => {
    const endpoint = tipo === "vista" ? "marcar-vista" : "marcar-no-deseada";

    try {
      const res = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario: usuarioLogueado, pelicula_id: peliculaId }),
      });

      if (res.ok) {
        await actualizarRecomendaciones(); // 🔄 Recargar sugerencias actualizadas
      } else {
        alert("❌ No se pudo marcar la película");
      }
    } catch (err) {
      alert("❌ Error al conectar con el servidor");
    }
  };


  const togglePendiente = async (peliculaId) => {
  const yaMarcada = pendientes.includes(peliculaId);
  const endpoint = yaMarcada ? "desmarcar-pendiente" : "marcar-pendiente";

  try {
    const res = await fetch(`http://127.0.0.1:8000/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ usuario: usuarioLogueado, pelicula_id: peliculaId }),
    });

    if (res.ok) {
      setPendientes((prev) =>
        yaMarcada ? prev.filter((id) => id !== peliculaId) : [...prev, peliculaId]
      );
    } else {
      alert("❌ Error al actualizar pendiente");
    }
  } catch {
    alert("❌ Error de conexión con el servidor");
  }
};


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

    recognition.onresult = (event) => {
      const texto = event.results[0][0].transcript;
      setPregunta(texto);
    };

    recognition.start();
  };

  const alternarTema = () => {
    setTemaOscuro((prev) => !prev);
  };

  // 🌐 FASE 1: LOGIN o REGISTRO
  if (!usuarioLogueado) {
    return (
      <div className="login-container">
        <h1>{modo === "login" ? "🔐 Iniciar sesión" : "📝 Registro"}</h1>

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
        <button onClick={handleAuth}>
          {modo === "login" ? "Entrar" : "Registrar"}
        </button>

        <p style={{ marginTop: "1rem", cursor: "pointer", color: "#663399" }} onClick={cambiarModo}>
          {modo === "login" ? "¿No tienes cuenta? Regístrate aquí" : "¿Ya tienes cuenta? Inicia sesión"}
        </p>

        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  // 🌐 FASE 2: FALTA GESTIÓN DE PREFERENCIAS
  // 🌐 FASE 2: PREFERENCIAS DEL USUARIO
if (!tienePreferencias || modoPreferencias) {
  const listaGeneros = ["Acción", "Aventura", "Animación", "Ciencia ficción", "Comedia", "Crimen", "Documental", "Drama", "Familia", "Fantasía", "Historia", "Misterio", "Música", "Película de TV", "Romance", "Suspense", "Terror", "Western", "Bélica"];

  const toggleGenero = (g) => {
    setGeneros((prev) =>
      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]
    );
  };

  const guardarPreferencias = async () => {
    const preferencias = {
      usuario: usuarioLogueado,
      generos_favoritos: generos,
      actores_favoritos: actores.split(",").map((a) => a.trim()).filter(Boolean),
      director_favorito: director.trim(),
      rango_años: usarTodosLosAnios ? "todos" : [parseInt(añoInicio), parseInt(añoFin)],
    };

    try {
      const res = await fetch("http://127.0.0.1:8000/guardar-preferencias", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferencias),
      });

      if (res.ok) {
        setTienePreferencias(true);
        setModoPreferencias(false);
      } else {
        alert("❌ Error al guardar las preferencias");
      }
    } catch (error) {
      alert("❌ No se pudo conectar con el servidor");
    }
  };

  return (
    <div className="container">
      <h1>🎯 {modoPreferencias ? "Edita tus preferencias" : `Bienvenido, ${usuarioLogueado}`}</h1>
      {!modoPreferencias && <p>¡Configura tus preferencias de cine para empezar!</p>}

      <form className="preferencias-formulario">
        <fieldset>
          <legend>🎭 Géneros favoritos:</legend>
          <div className="checkbox-group">
            {listaGeneros.map((g) => (
              <label key={g}>
                <input
                  type="checkbox"
                  checked={generos.includes(g)}
                  onChange={() => toggleGenero(g)}
                />
                {g}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>👥 Actores favoritos (separados por coma):</legend>
          <div className="input-group">
            <input
              type="text"
              value={actores}
              onChange={(e) => setActores(e.target.value)}
            />
          </div>
        </fieldset>

        <fieldset>
          <legend>🎬 Director favorito:</legend>
          <div className="input-group">
            <input
              type="text"
              value={director}
              onChange={(e) => setDirector(e.target.value)}
            />
          </div>
        </fieldset>

        <fieldset>
          <legend>📅 Rango de años preferido:</legend>
          <div className="input-group" style={{ flexDirection: "row", gap: "1rem", alignItems: "center" }}>
            <input
              type="number"
              placeholder="Desde"
              value={añoInicio}
              onChange={(e) => setAñoInicio(e.target.value)}
              disabled={usarTodosLosAnios}
            />
            <input
              type="number"
              placeholder="Hasta"
              value={añoFin}
              onChange={(e) => setAñoFin(e.target.value)}
              disabled={usarTodosLosAnios}
            />
            <label style={{ fontSize: "0.9rem" }}>
              <input
                type="checkbox"
                checked={usarTodosLosAnios}
                onChange={() => setUsarTodosLosAnios((prev) => !prev)}
              />{" "}
              Todos los años
            </label>
          </div>
        </fieldset>

        <div className="botones-preferencias">
          <button type="button" onClick={guardarPreferencias}>
            {modoPreferencias ? "Actualizar preferencias" : "Guardar preferencias"}
          </button>
        </div>
      </form>
    </div>

  );
}

  if (modoHistorial) {
    return (
      <div className="container">
        <button
          className="tema-toggle"
          onClick={alternarTema}
        >
          {temaOscuro ? "☀️ Modo claro" : "🌙 Modo oscuro"}
        </button>

        <button
          style={{
            marginBottom: "1rem",
            backgroundColor: "#2196f3",
            color: "white",
            padding: "0.5rem 1rem",
            borderRadius: "6px",
            border: "none"
          }}
          onClick={() => setModoHistorial(false)}
        >
          🔙 Volver al chatbot
        </button>

        <h1>📚 Tu historial de películas</h1>

        <section>
          <h2>✅ Vistas</h2>
          {historial.vistas.length > 0 ? (
            historial.vistas.map((p, i) => (
              <div key={i} className="pelicula">
                <h3>{p.titulo}</h3>
                <p><strong>Descripción:</strong> {p.descripcion}</p>
                <p><strong>Año:</strong> {p.año}</p>
              </div>
            ))
          ) : (
            <p>No hay películas marcadas como vistas.</p>
          )}
        </section>

        <section>
          <h2>🕒 Pendientes</h2>
          {historial.pendientes.length > 0 ? (
            historial.pendientes.map((p, i) => (
              <div key={i} className="pelicula">
                <h3>{p.titulo}</h3>
                <p><strong>Descripción:</strong> {p.descripcion}</p>
                <p><strong>Año:</strong> {p.año}</p>
              </div>
            ))
          ) : (
            <p>No tienes películas pendientes.</p>
          )}
        </section>

        <section>
          <h2>🚫 No deseadas</h2>
          {historial.no_deseadas.length > 0 ? (
            historial.no_deseadas.map((p, i) => (
              <div key={i} className="pelicula">
                <h3>{p.titulo}</h3>
                <p><strong>Descripción:</strong> {p.descripcion}</p>
                <p><strong>Año:</strong> {p.año}</p>
              </div>
            ))
          ) : (
            <p>No hay películas no deseadas.</p>
          )}
        </section>
      </div>
    );
  }


  // 🌐 FASE 3: CHATBOT
  return (
    <div className="container">
      <button className="tema-toggle" onClick={alternarTema}>
        {temaOscuro ? "☀️ Modo claro" : "🌙 Modo oscuro"}
      </button>
      {usuarioLogueado && (
        <div style={{ position: "absolute", top: "1rem", left: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <button
            style={{
              backgroundColor: "#2196f3",
              color: "white",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              border: "none"
            }}
            onClick={async () => {
              try {
                const res = await fetch(`http://127.0.0.1:8000/preferencias/${usuarioLogueado}`);
                const data = await res.json();

                if (res.ok) {
                  setGeneros(data.generos_favoritos || []);
                  setActores((data.actores_favoritos || []).join(", "));
                  setDirector(data.director_favorito || "");
                  if (data.rango_años === "todos") {
                    setUsarTodosLosAnios(true);
                    setAñoInicio("");
                    setAñoFin("");
                  } else {
                    setUsarTodosLosAnios(false);
                    setAñoInicio(data.rango_años?.[0] || "");
                    setAñoFin(data.rango_años?.[1] || "");
                  }
                  setModoPreferencias(true);
                } else {
                  alert("❌ No se pudieron cargar las preferencias");
                }
              } catch {
                alert("❌ Error al conectar con el servidor");
              }
            }}
          >
            ⚙️ Editar preferencias
          </button>

          <button
            style={{
              backgroundColor: "#795548",
              color: "white",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              border: "none"
            }}
            onClick={cargarHistorial}
          >
            📚 Ver historial
          </button>

          <button
            style={{
              backgroundColor: "#9e9e9e",
              color: "white",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              border: "none"
            }}
            onClick={cerrarSesion}
          >
            🚪 Cerrar sesión
          </button>
        </div>
      )}


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

      {respuesta?.peliculas?.length > 0 && (
        <div className="respuesta">
          {respuesta.peliculas
            .filter((p) => !peliculasOcultas.includes(p.id))
            .map((peli, i) => (
              <div className="pelicula" key={i}>
                <h3>{peli.titulo}</h3>
                <p><strong>Descripción:</strong> {peli.descripcion}</p>
                <p><strong>Puntuación:</strong> {peli.puntuacion}</p>
                <p><strong>Géneros:</strong> {peli.generos.join(", ")}</p>
                <p><strong>Director:</strong> {peli.director}</p>
                <p><strong>Actores:</strong> {peli.actores.join(", ")}</p>
                <p><strong>Año:</strong> {peli.año}</p>

                <div style={{ marginTop: "0.5rem" }}>
                  <button
                    style={{
                      marginRight: "0.5rem",
                      backgroundColor: "#4caf50",
                      color: "white",
                      padding: "0.4rem 0.8rem",
                      borderRadius: "6px",
                      border: "none"
                    }}
                    onClick={() => {
                      marcarPelicula(peli.id, "vista");
                      setPeliculasOcultas((prev) => [...prev, peli.id]);
                    }}
                  >
                    ✅ Ya la he visto
                  </button>

                  <button
                    style={{
                      marginRight: "0.5rem",
                      backgroundColor: "#f44336",
                      color: "white",
                      padding: "0.4rem 0.8rem",
                      borderRadius: "6px",
                      border: "none"
                    }}
                    onClick={() => {
                      marcarPelicula(peli.id, "no_deseada");
                      setPeliculasOcultas((prev) => [...prev, peli.id]);
                    }}
                  >
                    ❌ No me interesa
                  </button>

                  <button
                    style={{
                      backgroundColor: pendientes.includes(peli.id) ? "#ff9800" : "#e0e0e0",
                      color: pendientes.includes(peli.id) ? "white" : "#333",
                      padding: "0.4rem 0.8rem",
                      borderRadius: "6px",
                      border: "none"
                    }}
                    onClick={() => togglePendiente(peli.id)}
                  >
                    {pendientes.includes(peli.id) ? "📌 Pendiente de ver" : "📌 Marcar pendiente"}
                  </button>
                </div>
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
