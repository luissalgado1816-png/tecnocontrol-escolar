/* Cuadrícula compartida por los cuatro perfiles. */
window.Agenda = (() => {
  function nodo(tag, texto, clase) {
    const el = document.createElement(tag);
    if (texto != null) el.textContent = texto;
    if (clase) el.className = clase;
    return el;
  }
  function tabla(destino, dias, bloques, contenido) {
    const table = nodo("table", null, "table tabla-semanal");
    const cabecera = table.createTHead().insertRow();
    for (const texto of ["Horario", ...dias.map((d) => d.etiqueta)]) {
      const th = nodo("th", texto);
      th.scope = "col";
      cabecera.append(th);
    }
    const body = table.createTBody();
    for (const bloque of bloques) {
      const tr = body.insertRow(),
        th = nodo("th", bloque.etiqueta.replace("-", "–"));
      th.scope = "row";
      tr.append(th);
      for (const dia of dias) {
        const o = contenido(dia, bloque) || {},
          td = tr.insertCell();
        const el = nodo(
          o.accion ? "button" : "span",
          o.texto || "",
          "celda-agenda " + (o.clase || ""),
        );
        if (o.accion) {
          el.type = "button";
          el.setAttribute(
            "aria-label",
            [dia.etiqueta, bloque.etiqueta, o.texto || "Seleccionar"].join(
              " · ",
            ),
          );
          el.setAttribute("aria-pressed", String(!!o.elegida));
          el.addEventListener("click", o.accion);
        }
        if (o.rel) el.dataset.rel = o.rel;
        if (o.tono != null) el.dataset.tono = o.tono;
        if (o.elegida) el.classList.add("sel-agenda");
        td.append(el);
      }
    }
    destino.replaceChildren(table);
  }
  let marcado = "";
  function resaltar(id) {
    marcado = id || "";
    document
      .querySelectorAll("[data-rel]")
      .forEach((el) =>
        el.classList.toggle("rel-activa", !!id && el.dataset.rel === id),
      );
  }
  for (const event of ["mouseover", "focusin"])
    document.addEventListener(event, (e) => {
      const t = e.target.closest("[data-rel]");
      if (t) resaltar(t.dataset.rel);
    });
  for (const event of ["mouseout", "focusout"])
    document.addEventListener(event, (e) => {
      if (
        marcado &&
        e.target.closest("[data-rel]") &&
        !e.relatedTarget?.closest?.("[data-rel]")
      )
        resaltar("");
    });
  function semanas(destino, lista, elegir, actual = 0) {
    destino.replaceChildren();
    lista.forEach((dias, i) => {
      const btn = nodo(
        "button",
        (i ? "Semana siguiente" : "Semana actual") +
          " · " +
          dias[0].corta +
          "–" +
          dias[4].corta,
        i === actual
          ? "btn btn-primary btn-sm"
          : "btn btn-outline-primary btn-sm",
      );
      btn.type = "button";
      btn.setAttribute("aria-pressed", String(i === actual));
      btn.addEventListener("click", () => elegir(i));
      destino.append(btn);
    });
  }
  return { nodo, tabla, semanas, resaltar };
})();
