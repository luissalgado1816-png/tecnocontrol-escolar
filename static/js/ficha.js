// Calculo en vivo de semestre, usuario de acceso y correo institucional (Modulo 2)
(function () {
  const $ = (id) => document.getElementById(id);

  // Calcula el semestre actual segun el ano y ciclo de ingreso
  const semestre = $("semestre_calculado");
  if (semestre) {
    const anioActual = Number(semestre.dataset.anioActual);
    const cicloActual = semestre.dataset.cicloActual;
    const indice = { "Enero-Junio": 1, "Agosto-Diciembre": 2 };
    const calcular = () => {
      const anio = Number($("anio").value);
      const ciclo = $("ciclo").value;
      if (!anioActual || !anio || !indice[ciclo]) {
        semestre.value = "—";
        return;
      }
      const n = (anioActual - anio) * 2 + indice[cicloActual] - indice[ciclo] + 1;
      semestre.value = n >= 1 ? String(n) : "—";
    };
    $("anio").addEventListener("input", calcular);
    $("ciclo").addEventListener("change", calcular);
    calcular();
  }

  // Ajusta el prefijo de matricula (C o T) y refleja el usuario de acceso
  const usuario = $("usuario-acceso");
  const matricula = $("matricula");
  if (usuario && matricula) {
    const actualizar = () => {
      const tipo = document.querySelector('input[name="tipo_ingreso"]:checked')?.value;
      const prefijo = { 'Regular': '', 'Cambio de carrera': 'C', 'Traslado': 'T' }[tipo] ?? '';
      const base = matricula.value.trim().toUpperCase().replace(/^[CT]/, '');
      if (/^[0-9]{8}$/.test(base)) matricula.value = prefijo + base;
      usuario.textContent = matricula.value.trim().toUpperCase() || '—';
    };
    matricula.addEventListener("input", actualizar);
    document.querySelectorAll('input[name="tipo_ingreso"]').forEach((radio) => radio.addEventListener('change', actualizar));
    actualizar();
  }

  // Genera la parte local del correo institucional mientras no se modifique manualmente
  const correo = $("correo_local");
  if (correo && correo.dataset.sugerir) {
    let tocado = correo.value !== "";
    correo.addEventListener("input", () => (tocado = true));
    const valor = (id) => ($(id) ? $(id).value.trim() : "");
    const limpiar = (texto) => texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^A-Za-z0-9]/g, "");
    const sugerir = () => {
      if (tocado) return;
      if (correo.dataset.sugerir === "estudiante") {
        const m = valor("matricula").toUpperCase();
        correo.value = m ? "L" + m : "";
      } else {
        const nombre = limpiar(valor("nombres"));
        const apellido = limpiar(valor("ap_paterno"));
        const digitos = valor("clave_docente").replace(/\D/g, "");
        correo.value = nombre && apellido
          ? nombre[0].toUpperCase() + apellido[0].toUpperCase() + apellido.slice(1) + digitos
          : "";
      }
    };
    ["matricula", "nombres", "ap_paterno", "clave_docente"].forEach((id) => {
      if ($(id)) $(id).addEventListener("input", sugerir);
    });
    document.querySelectorAll('input[name="tipo_ingreso"]').forEach((radio) => radio.addEventListener('change', sugerir));
    sugerir();
  }
})();
