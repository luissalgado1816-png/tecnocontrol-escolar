// Editor dinamico de horario base para estudiantes y docentes (Modulo 2)
(function () {
  const nodoDatos = document.getElementById("datos-horario");
  if (!nodoDatos) return;

  const datos = JSON.parse(nodoDatos.textContent);
  const esDocente = datos.modo === "docente";
  const filas = datos.filas.map((f) => Object.assign({}, f));
  const $ = (id) => document.getElementById(id);

  const selMateria = $("ed-materia");
  const selDia = $("ed-dia");
  const selBloque = $("ed-bloque");
  const selCarreraEd = $("ed-carrera");
  const cuerpo = $("ed-cuerpo");
  const vacio = $("ed-vacio");
  const aviso = $("ed-aviso");

  const materias = new Map(datos.materias.map((m) => [m.id, m]));
  const bloques = new Map(datos.bloques.map((b, i) => [b.id, { etiqueta: b.etiqueta, orden: i }]));
  const carreras = new Map(datos.carreras.map((c) => [c.id, c.nombre]));
  const guion = (texto) => texto.replace("-", "–");

  // Obtiene el ID de carrera activa segun el modo (estudiante o docente)
  function carreraActual() {
    if (esDocente) return Number(selCarreraEd.value);
    const campo = $("id_carrera");
    return campo ? Number(campo.value) : NaN;
  }

  // Filtra las materias disponibles segun carrera y departamento
  function llenarMaterias() {
    const previa = selMateria.value;
    selMateria.replaceChildren(new Option("Selecciona materia", ""));
    const carrera = carreraActual();
    const depto = esDocente ? Number($("id_departamento").value) : null;
    datos.materias
      .filter((m) => m.carreras.includes(carrera) && (depto === null || m.depto === depto))
      .forEach((m) => selMateria.add(new Option(m.nombre, m.id)));
    if ([...selMateria.options].some((o) => o.value === previa)) selMateria.value = previa;
  }

  // Muestra u oculta el mensaje de validacion local del horario
  function avisar(texto) {
    aviso.textContent = texto;
    aviso.classList.toggle("d-none", !texto);
  }

  // Crea un input oculto para enviar cada fila al guardar el formulario
  function entrada(nombre, valor) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = nombre;
    input.value = valor;
    return input;
  }

  // Ordena por dia y bloque y dibuja la tabla de horario base
  function pintar() {
    filas.sort(
      (a, b) =>
        datos.dias.indexOf(a.dia) - datos.dias.indexOf(b.dia) ||
        (bloques.get(a.bloque)?.orden ?? 0) - (bloques.get(b.bloque)?.orden ?? 0)
    );
    cuerpo.replaceChildren();
    filas.forEach((fila, i) => {
      const tr = document.createElement("tr");
      const textos = [
        fila.dia,
        guion(bloques.get(fila.bloque)?.etiqueta ?? ""),
        materias.get(fila.materia)?.nombre ?? "(materia no válida)",
      ];
      if (esDocente) textos.push(carreras.get(fila.carrera) ?? "");
      textos.forEach((texto) => {
        const td = document.createElement("td");
        td.textContent = texto;
        tr.appendChild(td);
      });

      const tdAccion = document.createElement("td");
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "btn btn-sm btn-outline-danger";
      boton.textContent = "Quitar";
      boton.addEventListener("click", () => pedirQuitar(i));
      tdAccion.appendChild(boton);
      tdAccion.appendChild(entrada("h_materia", fila.materia));
      tdAccion.appendChild(entrada("h_dia", fila.dia));
      tdAccion.appendChild(entrada("h_bloque", fila.bloque));
      if (esDocente) tdAccion.appendChild(entrada("h_carrera", fila.carrera));
      tr.appendChild(tdAccion);
      cuerpo.appendChild(tr);
    });
    vacio.classList.toggle("d-none", filas.length > 0);
  }

  // Solicita confirmacion modal antes de quitar un bloque del horario
  let pendiente = null;
  const modalQuitar = document.getElementById("modalQuitar");
  function pedirQuitar(indice) {
    pendiente = indice;
    bootstrap.Modal.getOrCreateInstance(modalQuitar).show();
  }
  $("confirmar-quitar").addEventListener("click", () => {
    if (pendiente !== null) {
      filas.splice(pendiente, 1);
      pendiente = null;
      pintar();
    }
    bootstrap.Modal.getOrCreateInstance(modalQuitar).hide();
  });

  // Valida que no exista cruce de dia y bloque antes de agregar la fila
  $("ed-agregar").addEventListener("click", () => {
    if (!selMateria.value || !selDia.value || !selBloque.value) {
      avisar("Selecciona materia, día y hora.");
      return;
    }
    const dia = selDia.value;
    const bloque = Number(selBloque.value);
    if (filas.some((f) => f.dia === dia && f.bloque === bloque)) {
      avisar(`Ya hay una clase el ${dia} de ${guion(bloques.get(bloque).etiqueta)}.`);
      return;
    }
    const fila = { materia: Number(selMateria.value), dia, bloque };
    if (esDocente) fila.carrera = Number(selCarreraEd.value);
    filas.push(fila);
    avisar("");
    bootstrap.Toast.getOrCreateInstance($("aviso-horario"), { delay: 3500 }).show();
    selMateria.value = "";
    pintar();
  });

  // Carga catalogos iniciales y escucha cambios de carrera o departamento
  datos.dias.forEach((d) => selDia.add(new Option(d, d)));
  datos.bloques.forEach((b) => selBloque.add(new Option(guion(b.etiqueta), b.id)));

  const campoCarrera = $("id_carrera");
  if (campoCarrera) campoCarrera.addEventListener("change", llenarMaterias);
  if (esDocente) {
    selCarreraEd.addEventListener("change", llenarMaterias);
    $("id_departamento").addEventListener("change", llenarMaterias);
  }

  llenarMaterias();
  pintar();
})();
