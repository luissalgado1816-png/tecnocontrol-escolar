(() => {
  const $ = (id) => document.getElementById(id),
    a = JSON.parse($("agenda-datos").textContent);
  function pintar(indice) {
    Agenda.semanas($("semanas"), a.semanas, pintar, indice);
    Agenda.tabla($("calendario"), a.semanas[indice], a.bloques, (d, b) => {
      const c = a.clases.find((c) => c.dia === d.nombre && c.bloque === b.id);
      if (c)
        return {
          texto: "Clase · " + c.materia,
          clase: "clase-agenda clase-agenda-propia",
        };
      const franjas = a.franjas.filter((f) => f.fecha === d.fecha && f.bloque === b.id);
      const f = franjas.find((f) => f.estado !== "Cancelada") || franjas[0];
      if (f)
        return {
          texto:
            (f.estado === "Cancelada"
              ? "Asesoría cancelada · "
              : "Asesoría · ") +
            f.materia +
            (f.estado === "Cancelada"
              ? ""
              : " · " + f.reservados + " de " + f.cupo),
          clase: f.estado === "Cancelada" ? "cerrada-agenda" : "oferta-agenda",
        };
      return a.bloqueos.some((x) => x.desde <= d.fecha && d.fecha <= x.hasta)
        ? { texto: "Suspendida", clase: "cerrada-agenda" }
        : {};
    });
  }
  function consultarPeriodo() {
    const desde = $("desde"),
      hasta = $("hasta");
    if (!desde.value || !desde.validity.valid) return;
    if (hasta.value && hasta.value < desde.value) hasta.value = "";
    if (!hasta.validity.valid) return;
    const url = new URL(location.href);
    url.searchParams.set("desde", desde.value);
    url.searchParams.set("hasta", hasta.value || desde.value);
    if (url.href !== location.href) location.assign(url);
  }
  $("desde").addEventListener("change", consultarPeriodo);
  $("hasta").addEventListener("change", consultarPeriodo);
  $("restablecer-disponibilidad")?.addEventListener("show.bs.modal", (evento) => {
    const { fecha, fechaTexto } = evento.relatedTarget.dataset;
    $("restablecer-fecha").value = fecha;
    $("restablecer-fecha-texto").textContent = fechaTexto;
  });
  pintar($("desde").value >= a.semanas[1][0].fecha ? 1 : 0);
  if ($("suspension"))
    bootstrap.Modal.getOrCreateInstance($("suspension")).show();
})();
