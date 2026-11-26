(() => {
  const $ = (id) => document.getElementById(id),
    form = $("form-franjas");
  let datos = JSON.parse($("agenda-datos").textContent),
    semana = Number($("semana-vista").value),
    version = 0;
  const seleccion = new Set(),
    aviso = $("aviso-opciones");
  function decir(texto) {
    aviso.textContent = texto;
    aviso.classList.toggle("d-none", !texto);
  }
  function pintar() {
    $("semana-vista").value = semana;
    const publicadas = [
      ...document.querySelectorAll("#franjas-publicadas tr[data-docente]"),
    ];
    for (const fila of publicadas)
      fila.hidden =
        !!$("docente").value && fila.dataset.docente !== $("docente").value;
    $("sin-publicadas").hidden = publicadas.some((f) => !f.hidden);
    Agenda.semanas(
      $("semanas"),
      datos.semanas,
      (n) => {
        semana = n;
        pintar();
      },
      semana,
    );
    Agenda.tabla(
      $("calendario"),
      datos.semanas[semana],
      datos.bloques,
      (d, b) => {
        const f = datos.franjas.find(
          (f) =>
            f.fecha === d.fecha &&
            f.bloque === b.id &&
            f.estado !== "Cancelada",
        );
        const clase = datos.clases.find(
          (c) => c.dia === d.nombre && c.bloque === b.id,
        );
        const suspendida = datos.bloqueos.some(
          (x) => x.desde <= d.fecha && d.fecha <= x.hasta,
        );
        if (clase)
          return { texto: "Clase · " + clase.materia, clase: "clase-agenda" };
        if (f)
          return {
            rel: d.fecha + "|" + b.id,
            texto: f.materia + " · " + f.reservados + " de " + f.cupo,
            clase: "oferta-agenda",
          };
        if (suspendida) return { texto: "Suspendida", clase: "cerrada-agenda" };
        const key = d.fecha + "|" + b.id,
          on = seleccion.has(key);
        if (
          !$("docente").value ||
          d.fecha < datos.hoy ||
          (d.fecha === datos.hoy && b.hora <= datos.hora)
        )
          return {};
        return {
          texto: on ? $("materia").selectedOptions[0].text : "",
          elegida: on,
          accion: () => {
            if (!$("materia").value) {
              decir("Selecciona carrera y materia autorizada.");
              return;
            }
            if (on) seleccion.delete(key);
            else seleccion.add(key);
            decir("");
            pintar();
          },
        };
      },
    );
    $("seleccionadas").textContent = seleccion.size
      ? seleccion.size + " bloque(s) por publicar."
      : "Selecciona los bloques libres que deseas publicar.";
    $("seleccion-envio").replaceChildren(
      ...[...seleccion].map((v) => {
        const i = Agenda.nodo("input");
        i.type = "hidden";
        i.name = "seleccion";
        i.value = v;
        return i;
      }),
    );
  }
  async function actualizar() {
    const turno = ++version;
    seleccion.clear();
    const materia = $("materia");
    materia.replaceChildren(new Option("Selecciona materia", ""));
    datos = { ...datos, clases: [], franjas: [], bloqueos: [] };
    pintar();
    try {
      const resp = await fetch(
        form.dataset.opciones +
          "?" +
          new URLSearchParams({
            docente: $("docente").value,
            carrera: $("carrera").value,
          }),
      );
      if (!resp.ok) throw Error();
      const r = await resp.json();
      if (turno !== version) return;
      datos = r.agenda;
      for (const m of r.materias)
        materia.add(new Option(m.nombre, m.id_materia));
      decir("");
      pintar();
    } catch {
      if (turno === version)
        decir(
          "No se pudo consultar el horario del tutor. Vuelve a seleccionarlo.",
        );
    }
  }
  $("docente").addEventListener("change", actualizar);
  $("carrera").addEventListener("change", actualizar);
  $("materia").addEventListener("change", () => {
    seleccion.clear();
    pintar();
  });
  form.addEventListener("submit", (e) => {
    if (!seleccion.size) {
      e.preventDefault();
      decir("Selecciona al menos un bloque libre.");
    }
  });
  pintar();
})();
