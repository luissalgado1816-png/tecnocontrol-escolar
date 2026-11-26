(() => {
  const $ = (id) => document.getElementById(id),
    a = JSON.parse($("agenda-datos").textContent);
  const lista = $("lista-oferta"),
    nodo = Agenda.nodo,
    abierta = lista.dataset.abierta === "1";
  let semana = a.semana,
    seleccion = null,
    bloque = "";
  const clave = (d, b) => d + "|" + b;
  const corta = (d) => d.split("-").reverse().join("/");
  const cupo = (f) => (f.cupo - f.libres) + " de " + f.cupo + " reservados";
  function datosBloque(fecha, idBloque) {
    const dia = a.semanas[semana].find((d) => d.fecha === fecha);
    const coincide = (fila) => fila.fecha === fecha && fila.bloque === idBloque;
    return {
      key: clave(fecha, idBloque),
      clase: a.clases.find(
        (c) => c.dia === dia?.nombre && c.bloque === idBloque,
      ),
      citas: a.citas.filter(coincide),
      franjas: a.oferta.filter(coincide),
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
    { key, citas, franjas, clase },
    preferida = null,
    cancelacion = false,
  ) {
    const modal = $("bloque-citas");
    const ofrecidas = citas.some((c) => c.estado === "Programada") ? [] : franjas;
    const ocupado = citas.some((c) => c.estado !== "Cancelada");
    function motivoBloqueo(f) {
      if (f.suspendida) return "Asesoría suspendida";
      if (!f.libres) return "Sin cupo";
      if (ocupado) return "Ya tienes una asesoría en ese horario";
      if (abierta) return "Ya tienes una asesoría abierta de esta materia";
      return "";
    }
    const candidata = preferida ?? (ofrecidas.length === 1 ? ofrecidas[0] : null);
    if (candidata && !cancelacion && !motivoBloqueo(candidata)) {
      elegir(candidata);
    } else {
      seleccion = null;
      bloque = bloque === key ? "" : key;
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
      preferida?.suspendida ||
      (franjas.length && franjas.every((f) => f.suspendida))
    );
    cruce.hidden = !clase || !ofrecidas.some((f) => !motivoBloqueo(f));
    cruce.textContent = cruce.hidden
      ? ""
      : "Esta franja coincide con tu clase de " +
        clase.materia +
        ". Puedes continuar y aceptar el cruce antes de reservar.";
    opciones.replaceChildren();
    if (ofrecidas.length) {
      const f = ofrecidas[0];
      const detalle = [f.materia, corta(f.fecha), f.horario].join(" · ");
      opciones.append(nodo("p", detalle));
    }
    function actualizarReserva() {
      const franja = ofrecidas.find((f) => f.id === seleccion?.id);
      reservar.hidden = !franja;
      if (franja) reservar.href = franja.url;
      else reservar.removeAttribute("href");
      for (const boton of opciones.querySelectorAll("[data-franja]")) {
        const activa = Number(boton.dataset.franja) === franja?.id;
        boton.setAttribute("aria-pressed", String(activa));
        boton.classList.toggle("active", activa);
      }
    }
    for (const f of ofrecidas) {
      const motivo = motivoBloqueo(f);
      const boton = nodo(
        "button",
        f.docente + " · " + (motivo || cupo(f)),
        "btn btn-outline-primary w-100 text-start mb-2",
      );
      boton.type = "button";
      boton.dataset.franja = f.id;
      boton.disabled = Boolean(motivo);
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
      dias.some((d) => d.fecha === f.fecha),
    );
    Agenda.tabla($("calendario"), dias, a.bloques, (d, b) => {
      const datos = datosBloque(d.fecha, b.id);
      const { clase, citas, franjas, key } = datos;
      const textos = clase ? ["Clase · " + clase.materia] : [];
      for (const c of citas)
        textos.push(
          "Asesoría " +
            c.estado.toLowerCase().replace("no asistio", "no asistió") +
            " · " +
            c.materia,
        );
      if (franjas.length)
        textos.push(
          franjas.length === 1
            ? franjas[0].materia +
                " · " +
                (franjas[0].suspendida
                  ? "Suspendida"
                  : franjas[0].libres
                    ? "Disponible"
                    : "Sin cupo")
            : franjas.length + " tutores",
        );
            const tieneOferta = franjas.some((f) => !f.suspendida && f.libres);
      let estadoAsesoria = citas.some((c) => c.estado === "Programada")
        ? "cita-agenda"
        : citas.length
          ? "cerrada-agenda"
          : tieneOferta
            ? "oferta-agenda"
            : franjas.length
              ? "cerrada-agenda"
              : "";

      if (tieneOferta && estadoAsesoria !== "oferta-agenda") {
        estadoAsesoria += " oferta-agenda";
      }

      return {
        texto: textos.join("\n"),
        rel: key,
        elegida: bloque === key,
        clase: clase
          ? "clase-agenda clase-agenda-propia " + estadoAsesoria
          : estadoAsesoria,
        accion: citas.length || franjas.length ? () => mostrarBloque(datos) : null,
      };
    });
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
      row.dataset.rel = key;
      row.dataset.franja = f.id;
      row.classList.toggle(
        "sel-agenda",
        seleccion?.id === f.id || (!seleccion && bloque === key),
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
              : cupo(f) + (!f.libres ? " · Sin cupo" : "")),
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
