document.addEventListener("DOMContentLoaded", () => {
  // POLLING DEL PROFESOR
  function initProfesorPolling() {
    // div donde se ponen los mensajes
    const notificadorDiv = document.getElementById("notificador-profesor");

    // NSi no hay div no hace nada
    if (!notificadorDiv) return;

    // La URL de la API con alertas
    const apiUrl = notificadorDiv.dataset.apiUrl;

    if (!apiUrl) return; // Si no hay URL no hace nada

    // Función que busca los datos
    async function checkAlertas() {
      try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        notificadorDiv.innerHTML = ""; // Limpiamos

        if (data.alertas && data.alertas.length > 0) {
          // Si la API devolvió alertas se muestra
          data.alertas.forEach((alerta) => {
            const mensaje = document.createElement("p");
            mensaje.style.fontWeight = "bold";
            mensaje.style.color = "blue";
            mensaje.textContent = `¡ATENCIÓN! Alerta de "${alerta.tipo}" está siendo atendida por ${alerta.atendida_por} (desde las ${alerta.tiempo_aceptacion} hrs).`;
            notificadorDiv.appendChild(mensaje);
          });
        } else {
          notificadorDiv.innerHTML =
            "<p>No hay alertas en curso para este curso.</p>";
        }
      } catch (error) {
        console.error("Error en el polling (profesor):", error);
        notificadorDiv.innerHTML =
          '<p style="color: red;">Error de conexión con el notificador.</p>';
      }
    }

    checkAlertas();
    setInterval(checkAlertas, 5000); // Recarga cada 5 segundos
  }

  // FORMULARIO DE ALERTA TÉCNICA
  function initAlertaTecnicaToggle() {
    const tipoAlertaSelect = document.getElementById("alerta-tipo-select");
    const descripcionBloque = document.getElementById(
      "bloque-descripcion-tecnica"
    );
    const descripcionTextarea = document.getElementById("alerta_descripcion");

    // No hace nada si no están los elementos anteriores
    if (!tipoAlertaSelect || !descripcionBloque || !descripcionTextarea) return;

    function toggleDescripcion() {
      if (tipoAlertaSelect.value === "tecnico") {
        descripcionBloque.style.display = "block";
        descripcionTextarea.required = true;
      } else {
        descripcionBloque.style.display = "none";
        descripcionTextarea.required = false;
      }
    }

    tipoAlertaSelect.addEventListener("change", toggleDescripcion);
    toggleDescripcion();
  }

  initProfesorPolling();
  initAlertaTecnicaToggle();
});
