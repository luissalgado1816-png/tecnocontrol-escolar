(() => {
  const $ = (id) => document.getElementById(id);
  const datos = JSON.parse($("datos-horario").textContent);
  const docente = datos.modo === "docente";
  const carrera = $(docente ? "ed-carrera" : "id_carrera"),
    materia = $("ed-materia");
  const materias = new Map(datos.materias.map((m) => [m.id, m]));
  const carreras = new Map(datos.carreras.map((c) => [c.id, c.nombre]));
  let filas = datos.filas.slice(),
    marcada = "";
  const llave = (dia, bloque) => dia + "-" + bloque;
  const bloqueado = () => docente && $("estado_laboral").value !== "Activo";
  function elegible(m, c) {
    if (!m || !m.carreras.includes(c)) return false;
    if (docente)
      return (
        m.depto === Number($("id_departamento").value) &&
        m.pos <= ({ "Ing.": 1, "Mtro.": 2, "Dr.": 3 }[$("grado").value] || 0)
      );
    const p = datos.periodoActual,
      indice = (ciclo) => (ciclo === "Agosto-Diciembre" ? 2 : 1);
    return (
      p &&
      m.planes[c] ===
        (p.anio - Number($("anio").value)) * 2 +
          indice(p.ciclo) -
          indice($("ciclo").value) +
          1
    );
  }
  function catalogo() {
    const previa = materia.value;
    materia.replaceChildren(new Option("Selecciona materia", ""));
    if (!bloqueado())
      datos.materias
        .filter((m) => elegible(m, Number(carrera.value)))
        .forEach((m) =>
          materia.add(new Option(m.nombre + " · " + m.clave, m.id)),
        );
    if ([...materia.options].some((o) => o.value === previa))
      materia.value = previa;
    materia.disabled = bloqueado();
    if (docente) carrera.disabled = bloqueado();
    $("ed-aviso").textContent = bloqueado()
      ? "Horario vacío. Estado laboral del docente: " +
        $("estado_laboral").value +
        "."
      : "Selecciona una materia y sus horas. Vuelve a pulsar una celda para quitarla.";
  }
  function quitar(fila) {
    filas.splice(filas.indexOf(fila), 1);
    marcada = "";
    pintar();
  }
  function alternar(dia, bloque, fila) {
    if (fila) {
      quitar(fila);
      return;
    }
    if (!materia.value) {
      $("ed-aviso").textContent = "Selecciona primero la materia.";
      materia.focus();
      return;
    }
    filas.push({
      materia: Number(materia.value),
      dia,
      bloque,
      carrera: Number(carrera.value),
    });
    marcada = llave(dia, bloque);
    pintar();
  }
  function pintar() {
    const dias = datos.dias.map((nombre) => ({ nombre, etiqueta: nombre }));
    Agenda.tabla($("ed-calendario"), dias, datos.bloques, (d, b) => {
      const f = filas.find((x) => x.dia === d.nombre && x.bloque === b.id),
        key = llave(d.nombre, b.id);
      return {
        texto: f ? materias.get(f.materia)?.nombre : "",
        tono: f ? f.materia % 4 : null,
        rel: key,
        elegida: key === marcada,
        accion: bloqueado() ? null : () => alternar(d.nombre, b.id, f),
      };
    });
    const cuerpo = $("ed-cuerpo");
    cuerpo.replaceChildren();
    filas.sort(
      (a, b) =>
        datos.dias.indexOf(a.dia) - datos.dias.indexOf(b.dia) ||
        a.bloque - b.bloque,
    );
    for (const f of filas) {
      const tr = cuerpo.insertRow(),
        key = llave(f.dia, f.bloque);
      tr.dataset.rel = key;
      tr.tabIndex = 0;
      tr.classList.toggle("fila-elegida", key === marcada);
      const marcar = () => {
        marcada = key;
        pintar();
        Agenda.resaltar(key);
      };
      tr.addEventListener("click", marcar);
      tr.addEventListener("keydown", (e) => {
        if (e.target === tr && e.key === "Enter") marcar();
      });
      const horario =
        datos.bloques.find((b) => b.id === f.bloque)?.etiqueta || "";
      const valores = [
        f.dia,
        horario.replace("-", "–"),
        materias.get(f.materia)?.nombre,
      ];
      if (docente) valores.push(carreras.get(f.carrera));
      for (const v of valores) tr.insertCell().textContent = v;
      const td = tr.insertCell(),
        boton = Agenda.nodo(
          "button",
          "Quitar",
          "btn btn-sm btn-outline-danger",
        );
      boton.type = "button";
      boton.addEventListener("click", (e) => {
        e.stopPropagation();
        quitar(f);
      });
      td.append(boton);
      for (const k of docente
        ? ["materia", "dia", "bloque", "carrera"]
        : ["materia", "dia", "bloque"]) {
        const i = Agenda.nodo("input");
        i.type = "hidden";
        i.name = "h_" + k;
        i.value = f[k];
        td.append(i);
      }
    }
    $("ed-vacio").hidden = filas.length > 0;
  }
  for (const id of docente
    ? ["ed-carrera", "id_departamento", "grado", "estado_laboral"]
    : ["id_carrera", "anio", "ciclo"]) {
    $(id).addEventListener("change", () => {
      if (bloqueado()) filas = [];
      else if (id !== "ed-carrera")
        filas = filas.filter((f) =>
          elegible(
            materias.get(f.materia),
            docente ? f.carrera : Number(carrera.value),
          ),
        );
      marcada = "";
      catalogo();
      pintar();
    });
  }
  catalogo();
  pintar();
})();
