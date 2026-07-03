import streamlit as st
import requests
import time
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# set_page_config debe ser la primera orden de Streamlit
st.set_page_config(
    page_title="Asistente Académico",
    page_icon="👽",
    layout="centered"
)

# Leer parámetros de la URL si vienen de Moodle via LTI
parametros_url = st.query_params
id_curso_moodle = parametros_url.get("course_id", "test_tfg")
id_usuario_moodle = parametros_url.get("user_id", "alumno_demo")

# Estilo personalizado con CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Barra lateral de configuración
with st.sidebar:
    st.title("⚙️ Configuración")
    st.markdown("---")
    id_curso = st.text_input("ID del Curso", value=id_curso_moodle)
    id_usuario = st.text_input("ID del Alumno", value=id_usuario_moodle)
    st.info("Prueba de asistente, con Qdrant.")
    if st.button("Limpiar Chat"):
        st.session_state.mensajes = []
        st.rerun()

# Auto-limpieza del historial visual al cambiar de curso o alumno.
# Esto garantiza que al cambiar de sesión no queden mensajes de otra conversación en pantalla,
# aunque a nivel de backend LangGraph ya aísla los hilos por thread_id (curso_usuario).
identidad_actual = f"{id_curso}_{id_usuario}"
if "identidad_anterior" not in st.session_state:
    st.session_state.identidad_anterior = identidad_actual
elif st.session_state.identidad_anterior != identidad_actual:
    st.session_state.mensajes = []
    st.session_state.identidad_anterior = identidad_actual
    st.rerun()

# Cuerpo principal
st.title("Buenos días, en que te puedo ayudar hoy")
st.caption("Pregunta lo que necesites sobre tus apuntes")

# Inicializamos historial de mensajes
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostramos mensajes anteriores del historial
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])
        # Si el mensaje del asistente tiene fuentes, las mostramos en un desplegable
        if "fuentes" in mensaje and mensaje["fuentes"]:
            with st.expander("📚 Ver fuentes consultadas"):
                for idx, fuente in enumerate(mensaje["fuentes"]):
                    st.write(f"**Fragmento {idx+1}:**")
                    st.caption(fuente)

# Input del usuario
if prompt := st.chat_input("Escribe tu duda aquí..."):
    # Añadimos mensaje del usuario al historial
    st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta de la IA
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Buscando en los apuntes...*")

        try:
            payload = {
                "message": prompt,
                "course_id": id_curso,
                "user_id": id_usuario
            }

            respuesta_api = requests.post(f"{BACKEND_URL}/api/v1/chat/", json=payload)

            if respuesta_api.status_code == 200:
                datos = respuesta_api.json()
                respuesta_completa = datos["answer"]
                fuentes = datos.get("sources", [])

                # Efecto de escritura "typewriter"
                texto_escrito = ""
                for fragmento_texto in respuesta_completa.split():
                    texto_escrito += fragmento_texto + " "
                    time.sleep(0.04)
                    message_placeholder.markdown(texto_escrito + "▌")

                message_placeholder.markdown(respuesta_completa)

                # Mostramos fuentes si existen
                if fuentes:
                    with st.expander("📚 Ver fuentes consultadas"):
                        for idx, fuente in enumerate(fuentes):
                            st.write(f"**Fragmento {idx+1}:**")
                            st.caption(fuente)

                # Guardamos en el historial
                st.session_state.mensajes.append({
                    "rol": "assistant",
                    "contenido": respuesta_completa,
                    "fuentes": fuentes
                })
            else:
                st.error(f"Error del servidor. Código HTTP: {respuesta_api.status_code}")
        except Exception as e:
            st.error(f"Error de conexión con el backend: {e}")
