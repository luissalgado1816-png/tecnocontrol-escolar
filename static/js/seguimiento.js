(() => {
  const $ = (id) => document.getElementById(id);
  if (!$("asistencia")) return;
  function actualizar() {
    const asistio = $("asistencia").value === "asistio",
      seguir = asistio && $("decision").value === "seguir";
    $("decision-seguimiento").disabled = !asistio;
    $("franja").disabled = !seguir;
    $("franja").required = seguir;
    $("descripcion").required = seguir;
    $("opcional").textContent =
      $("decision").value === "cerrar" ? "(opcional)" : "";
    if ($("sin-franjas")) $("sin-franjas").hidden = !seguir;
    $("guardar-atencion").disabled =
      !$("asistencia").value ||
      (asistio && (!$("decision").value || (seguir && !$("franja").value)));
  }
  ["asistencia", "decision", "franja"].forEach((id) =>
    $(id).addEventListener("change", actualizar),
  );
  actualizar();
})();
