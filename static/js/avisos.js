// Inicializa los avisos flotantes de guardado (Toast de Bootstrap)
document.querySelectorAll('[data-aviso-guardado]').forEach((aviso) => {
  bootstrap.Toast.getOrCreateInstance(aviso).show();
});
