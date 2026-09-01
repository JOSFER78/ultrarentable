# Drop-ins de systemd — aplicar con sudo

Estos ficheros NO se aplican solos: modificar unidades de systemd requiere permisos que la sesión
de Claude no tiene. Emilio los instala con los comandos de `orchestration/OPERACION_VPS.md`.

Un drop-in en `/etc/systemd/system/<unidad>.d/override.conf` **añade** directivas sin tocar la
unidad original, así que revertir es borrar el fichero y recargar. No se edita la unidad base.
