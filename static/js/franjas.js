/* Módulo 3 · opciones dependientes. La publicación repite las reglas en Flask. */
(function () {
  const form = document.getElementById('form-franjas');
  if (!form) return;
  const campo = (id) => document.getElementById(id);
  let secuencia = 0;
  function llenar(select, opciones, valor, clave, etiqueta) {
    const inicial = select.options[0].textContent;
    select.replaceChildren(new Option(inicial, ''));
    opciones.forEach((opcion) => select.add(new Option(opcion[etiqueta], opcion[clave])));
    if ([...select.options].some((o) => o.value === valor)) select.value = valor;
  }
  async function actualizar() {
    const turno = ++secuencia;
    const previa = campo('materia').value;
    const params = new URLSearchParams(['docente', 'carrera', 'fecha'].map((id) => [id, campo(id).value]));
    campo('materia').disabled = true;
    campo('bloque').disabled = true;
    try {
      const response = await fetch(form.dataset.opciones + '?' + params.toString(), { headers: { Accept: 'application/json' } });
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error('opciones');
      const datos = await response.json();
      if (turno !== secuencia) return;
      llenar(campo('materia'), datos.materias, previa, 'id_materia', 'nombre');
      llenar(campo('bloque'), datos.bloques, '', 'id_bloque', 'etiqueta');
      campo('dia').value = datos.dia;
      campo('aviso-opciones').textContent = datos.mensaje;
      campo('aviso-opciones').classList.toggle('d-none', !datos.mensaje);
    } catch (_) {
      if (turno !== secuencia) return;
      campo('aviso-opciones').textContent = 'No se pudo actualizar el horario disponible. Recarga la página e inténtalo de nuevo.';
      campo('aviso-opciones').classList.remove('d-none');
      llenar(campo('bloque'), [], '', 'id_bloque', 'etiqueta');
    } finally {
      if (turno === secuencia) {
        campo('materia').disabled = false;
        campo('bloque').disabled = false;
      }
    }
  }
  ['docente', 'carrera', 'fecha'].forEach((id) => campo(id).addEventListener('change', actualizar));
})();
