# Datos heredados en cuarentena

Estos archivos venían incluidos en `ultrarentable_real_only_v1.zip`.

Sus checksums coinciden con los manifiestos, pero **no pueden usarse para backtesting** porque:

- no se conservó la respuesta REST RAW original;
- no se conserva la URL completa ni los headers de la captura;
- varios manifiestos no distinguen de forma verificable velas cerradas de velas abiertas;
- la normalización aplicaba valores por defecto cuando faltaban campos;
- no existe una cadena de custodia completa desde BingX hasta el dataset normalizado.

El IDE debe regenerar los datasets con el nuevo ingestor y moverlos a `data/normalized/` únicamente cuando superen los controles de procedencia, cierre de velas, huecos, duplicados y checksum.
