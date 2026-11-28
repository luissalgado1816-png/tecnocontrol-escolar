(() => {
  const $ = (id) => document.getElementById(id),
    a = JSON.parse($("agenda-datos").textContent);
  const lista = $("lista-oferta"),
    nodo = Agenda.nodo,
    abierta = lista.dataset.abierta === "1",
    inscrito = lista.dataset.inscrito === "1";
  let semana = a.semana,
    seleccion = null,
    bloque = "";
  const clave = (d, b) => d + "|" + b;
  const corta = (d) => d.split("-").reverse().join("/");
  const cupo = (f) => (f.cupo - f.libres) + " de " + f.cupo + " reservados";
  const publicada = (f) => !f.pasada && !f.suspendida;
  const esCitaProgramada = (cita) => cita.estado === "Programada" && cita.futura;
  const franjasPropias = new Set(
    a.citas.filter(esCitaProgramada).map((cita) => cita.id_franja),
  );
  const avisoMateria = "Ya tienes una asesoría abierta de esta materia";

  function estadoOferta(f) {
    if (f.suspendida) return "Asesoría suspendida";
    if (f.pasada) return "Franja pasada";
    if (f.libres <= 0) return "Sin cupo";
    return "";
  }

  function bloqueadaPorMateria(f) {
    return abierta && !estadoOferta(f) && !franjasPropias.has(f.id);
  }

  function datosBloque(fecha, idBloque) {
    const dia = a.semanas[semana].find((d) => d.fecha === fecha);
    const coincide = (fila) => fila.fecha === fecha && fila.bloque === idBloque;
    const citas = a.citas.filter(coincide);
    const programada = citas.find(esCitaProgramada);
    return {
      key: clave(fecha, idBloque),
      clase: a.clases.find(
        (c) => c.dia === dia?.nombre && c.bloque === idBloque,
      ),
      citas,
      programada,
      franjas: a.oferta.filter(
        (f) => coincide(f) && f.id !== programada?.id_franja,
      ),
    };
  }
  function elegir(f) {
    seleccion = seleccion?.id === f.id ? null : f;
    bloque = seleccion ? clave(f.fecha, f.bloque) : "";
    pintar();
  }
  function concentrado() {
    const dest = $("concentrado");
    dest.replaceChildren();
    if (!seleccion) {
      dest.textContent = "Aún no hay una franja seleccionada.";
      return;
    }
    const f = seleccion,
      p = nodo(
        "p",
        corta(f.fecha) +
          " · " +
          f.horario +
          " · " +
          f.materia +
          " · " +
          f.docente,
      );
    p.dataset.rel = clave(f.fecha, f.bloque);
    const reservar = nodo("a", "Reservar", "btn btn-primary me-2");
    reservar.href = f.url;
    const quitar = nodo("button", "Quitar", "btn btn-outline-secondary");
    quitar.type = "button";
    quitar.onclick = () => elegir(f);
    dest.append(p, reservar, quitar);
  }
  function mostrarBloque(
    { key, citas, programada, franjas, clase },
    preferida = null,
    cancelacion = false,
  ) {
    const modal = $("bloque-citas");
    const ocupado = citas.some((c) => c.estado !== "Cancelada");
    function motivoBloqueo(f) {
      const estado = estadoOferta(f);
      if (estado) return estado;
      if (!inscrito) return "Solo un estudiante inscrito puede reservar";
      if (ocupado) return "Ya tienes una asesoría en ese horario";
      if (bloqueadaPorMateria(f)) return avisoMateria;
      return "";
    }
    const publicadas = franjas.filter(publicada);
    const candidata = preferida
      ? franjas.find((f) => f.id === preferida.id)
      : publicadas.length === 1 ? publicadas[0] : null;
    if (candidata && !cancelacion && !motivoBloqueo(candidata)) {
      elegir(candidata);
    } else {
      seleccion = null;
      const soloConsulta = !programada && franjas.some(bloqueadaPorMateria);
      bloque = !soloConsulta && bloque !== key ? key : "";
      pintar();
    }
    const opciones = $("citas-oferta");
    const cruce = $("cruce-oferta");
    const reservar = $("reservar-oferta");
    $("titulo-citas").textContent = citas.length
      ? "Mis asesorías"
      : "Franjas de asesoría";
    $("aviso-cancelacion-franja").hidden = !(
      cancelacion ||
      citas.some((c) => c.cancelada_por_docente) ||
      franjas.some((f) => f.suspendida)
    );
    cruce.hidden = !clase || !franjas.some((f) => !motivoBloqueo(f));
    cruce.textContent = cruce.hidden
      ? ""
      : "Esta franja coincide con tu clase de " +
        clase.materia +
        ". Puedes continuar y aceptar el cruce antes de reservar.";
    opciones.replaceChildren();
    if (franjas.length) {
      const f = franjas[0];
      const detalle = [f.materia, corta(f.fecha), f.horario].join(" · ");
      opciones.append(nodo("p", detalle));
    }
    function actualizarReserva() {
      const franja = franjas.find((f) => f.id === seleccion?.id);
      reservar.hidden = !franja;
      if (franja) reservar.href = franja.url;
      else reservar.removeAttribute("href");
      for (const boton of opciones.querySelectorAll("[data-franja]")) {
        const activa = Number(boton.dataset.franja) === franja?.id;
        boton.setAttribute("aria-pressed", String(activa));
        boton.classList.toggle("active", activa);
      }
    }
    for (const f of franjas) {
      const motivo = motivoBloqueo(f);
      const boton = nodo(
        "button",
        f.docente + " · " + (motivo || cupo(f)),
        "btn btn-outline-primary w-100 text-start mb-2",
      );
      boton.type = "button";
      boton.dataset.franja = f.id;
      boton.disabled = Boolean(motivo);
      boton.classList.toggle("oferta-bloqueada-materia", bloqueadaPorMateria(f));
      boton.onclick = () => {
        elegir(f);
        actualizarReserva();
      };
      opciones.append(boton);
    }
    actualizarReserva();
    modal
      .querySelectorAll("[data-cita]")
      .forEach(
        (s) => (s.hidden = !citas.some((r) => r.id === Number(s.dataset.cita))),
      );
    modal.addEventListener("hidden.bs.modal", () => {
      const origen = preferida
        ? lista.querySelector(`button[data-franja="${preferida.id}"]`)
        : $("calendario").querySelector(`button[data-rel="${key}"]`);
      origen?.focus({ preventScroll: true });
    }, { once: true });
    bootstrap.Modal.getOrCreateInstance(modal).show();
  }
  function contenidoCelda(datos) {
    const { clase, citas, programada, franjas, key } = datos;
    const hayOferta = franjas.some((f) => !estadoOferta(f));
    const publicadas = franjas.filter(publicada);
    const textos = [];
    let estilo = "";

    if (clase) {
      estilo = "clase-agenda-propia";
      textos.push("Clase · " + clase.materia);
    }
    if (programada) {
      estilo = clase ? estilo + " cruce-agenda-cita" : "cita-agenda";
      textos.push("Asesoría programada · " + programada.materia);
    }
    if (hayOferta) {
      const bloqueada = franjas.some(bloqueadaPorMateria);
      if (!estilo) estilo = "oferta-agenda";
      else if (!programada || (!clase && !bloqueada)) estilo += " cruce-agenda-oferta";
      if (bloqueada && !programada) estilo += " bloqueo-agenda-materia";
      const varias = publicadas.length > 1;
      const oferta = varias ? publicadas.length + " tutores" : publicadas[0].materia;
      if (bloqueada) textos.push(oferta + " · Bloqueada por cita abierta");
      else textos.push(varias ? oferta : oferta + " · Disponible");
    }
    if (!estilo && (citas.length || franjas.length)) {
      estilo = "cerrada-agenda";
      if (franjas.length) {
        const f = publicadas[0] ?? franjas[0];
        textos.push(
          publicadas.length > 1
            ? publicadas.length + " tutores · Sin cupo"
            : f.materia + " · " + estadoOferta(f),
        );
      } else {
        const cita = citas.at(-1);
        const estado = cita.estado === "Programada"
          ? "pasada"
          : cita.estado.toLowerCase().replace("no asistio", "no asistió");
        textos.push("Asesoría " + estado + " · " + cita.materia);
      }
    }

    return {
      texto: textos.join("\n"),
      rel: key,
      elegida: bloque === key,
      clase: estilo,
      accion: citas.length || franjas.length ? () => mostrarBloque(datos) : null,
    };
  }

  function pintar() {
    const dias = a.semanas[semana];
    $("semana-consulta").value = semana;
    Agenda.semanas(
      $("semanas"),
      a.semanas,
      (n) => {
        semana = n;
        seleccion = null;
        bloque = "";
        pintar();
      },
      semana,
    );
    const oferta = a.oferta.filter((f) =>
      !f.pasada && dias.some((d) => d.fecha === f.fecha),
    );
    Agenda.tabla($("calendario"), dias, a.bloques, (d, b) =>
      contenidoCelda(datosBloque(d.fecha, b.id)),
    );
    lista.replaceChildren();
    if (!oferta.length)
      lista.append(
        nodo(
          "p",
          lista.dataset.materia
            ? "No hay franjas publicadas para esta materia en la semana seleccionada."
            : "Selecciona una materia para consultar los tutores.",
        ),
      );
    for (const f of oferta) {
      const key = clave(f.fecha, f.bloque),
        row = nodo(
          "button",
          null,
          "btn btn-light text-start border w-100 mb-1",
        );
      row.type = "button";
      const bloqueada = bloqueadaPorMateria(f);
      row.disabled = bloqueada;
      row.classList.toggle("oferta-bloqueada-materia", bloqueada);
      row.classList.toggle("border", !bloqueada);
      row.dataset.rel = key;
      row.dataset.franja = f.id;
      row.classList.toggle(
        "sel-agenda",
        !bloqueada && (seleccion?.id === f.id || (!seleccion && bloque === key)),
      );
      row.setAttribute("aria-pressed", String(seleccion?.id === f.id));
      row.append(
        nodo("strong", f.docente),
        nodo("br"),
        nodo(
          "span",
          corta(f.fecha) +
            " · " +
            f.horario +
            " · " +
            (f.suspendida
              ? "Asesoría suspendida"
              : bloqueada
                ? avisoMateria
                : cupo(f) + (f.libres <= 0 ? " · Sin cupo" : "")),
        ),
      );
      row.setAttribute("aria-haspopup", "dialog");
      row.onclick = () => mostrarBloque(datosBloque(f.fecha, f.bloque), f);
      lista.append(row);
    }
    concentrado();
  }
  $("materia").addEventListener("change", () => {
    if ($("asesoria")) $("asesoria").disabled = true;
    $("materia").form.requestSubmit();
  });
  $("asesoria")?.addEventListener("change", () =>
    $("asesoria").form.requestSubmit(),
  );
  pintar();
  if (a.franja_cancelada) {
    const f = a.franja_cancelada;
    mostrarBloque(datosBloque(f.fecha, f.bloque), null, true);
  }
})();
