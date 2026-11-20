// Cerrar es la opción inicial; el selector permanece visible y deshabilitado.
(() => {
  const form = document.getElementById('form-acuerdo');
  if (!form) return;
  const franja = form.querySelector('#franja');
  const seguir = form.querySelector('#seguir');
  const actualizar = () => {
    franja.disabled = !seguir.checked;
    franja.required = seguir.checked;
  };
  form.querySelectorAll('[name="decision"]').forEach((radio) => radio.addEventListener('change', actualizar));
  actualizar();
})();