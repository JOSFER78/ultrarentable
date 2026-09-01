# MOTIVO — `apps/web/node_modules/next` roto (2026-09-01)

Durante la ola web, dos `npm install` concurrentes (uno mío y uno de un subagente) dejaron el
paquete `next` a medias (errores `ENOTEMPTY`/`EPERM` de npm en Windows) y `npm run build` fallaba
con "`next` no encontrado". El directorio dañado se movió aquí íntegro (regla "nunca rm") y se
reinstaló limpio con un único `npm install`; después el build de producción quedó verde.

No se versiona (ver `.gitignore`): son ficheros de dependencia de terceros, no código del
proyecto. Puede borrarse cuando Emilio lo autorice; hasta entonces ocupa disco y nada más.
