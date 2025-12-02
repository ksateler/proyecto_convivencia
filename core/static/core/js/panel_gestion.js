document.addEventListener("DOMContentLoaded", () => {
  function initKanbanPolling() {
    const conteoSpan = document.getElementById("conteo-pendientes-actual");
    const notificadorDiv = document.getElementById("notificador-alertas");

    if (!conteoSpan || !notificadorDiv) return;

    const apiUrl = notificadorDiv.dataset.apiUrl;
    if (!apiUrl) return;

    async function checkNuevasAlertas() {
      try {
        let conteoActualPagina = parseInt(conteoSpan.textContent.trim(), 10);
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`Error de red: ${response.status}`);
        }

        const data = await response.json();
        let conteoApi = data.conteo_pendientes;

        if (conteoApi > conteoActualPagina) {
          location.reload();
        }
      } catch (error) {
        // Esto muestra cualquier error en la consola
        console.error("Error en el polling (Kanban):", error);
      }
    }

    setInterval(checkNuevasAlertas, 4000); // cada 4 segundos
  }

  initKanbanPolling();
});
