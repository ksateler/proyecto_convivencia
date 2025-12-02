document.addEventListener("DOMContentLoaded", () => {
  function initApoderadoInfoToggle() {
    const studentSelect = document.getElementById("id_estudiante");
    const visibleContainer = document.getElementById("info-apoderado-visible");
    const hiddenContainer = document.getElementById("datos-apoderados-ocultos");
    const defaultText =
      "<p>Por favor, seleccione un estudiante para ver la información del apoderado.</p>";

    function actualizarInfoApoderado() {
      if (!visibleContainer) return; // Si el div no está visible no hace nada

      if (studentSelect && studentSelect.value) {
        const infoOculta = hiddenContainer.querySelector(
          `#info-apoderado-${studentSelect.value}`
        );
        if (infoOculta) {
          visibleContainer.innerHTML = infoOculta.innerHTML;
        } else {
          visibleContainer.innerHTML = defaultText;
        }
      } else {
        visibleContainer.innerHTML = defaultText;
      }
    }

    if (studentSelect) {
      studentSelect.addEventListener("change", actualizarInfoApoderado);
    }

    actualizarInfoApoderado();
  }

  initApoderadoInfoToggle();
});
