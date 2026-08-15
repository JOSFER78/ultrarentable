# Especificación funcional del MVP

## 1. Usuarios

### Operador investigador

Configura campañas, observa progreso, inspecciona estrategias y exporta resultados.

### Agente investigador

Convierte ideas externas en hipótesis estructuradas y nunca ejecuta código arbitrario.

### Motor evolutivo

Crea poblaciones, muta, cruza, selecciona y programa nuevas evaluaciones.

## 2. Casos de uso principales

1. Crear una campaña indicando mercado, temporalidad, periodo, capital inicial y presupuesto de pruebas.
2. Generar una población inicial aleatoria o desde plantillas.
3. Evaluar candidatos en paralelo con el motor rápido.
4. Enviar los mejores candidatos supervivientes al backtester canónico.
5. Clasificar exclusivamente por crecimiento final dentro del modo Kamikaze.
6. Crear descendencia de los mejores candidatos.
7. Repetir en ventanas de tres meses con semillas guardadas.
8. Consultar el árbol genealógico y todos los experimentos.
9. Importar una idea externa como hipótesis, convertirla a DSL y probarla.
10. Exportar estrategia, configuración, trades y reporte reproducible.

## 3. Estados de candidato

```text
DRAFT -> COMPILED -> FAST_TESTED -> CANONICAL_TESTED
                        |                 |
                        v                 v
                     REJECTED         SURVIVOR
                                          |
                                          v
                                      ARCHIVED
```

`REJECTED` en Kamikaze solo significa liquidación/equity <= 0, invalidez técnica o falta de reproducibilidad.

## 4. Score

### Score principal

```text
terminal_multiple = final_equity / initial_equity
```

### Orden de desempate

1. mayor `terminal_multiple`;
2. mayor beneficio neto absoluto;
3. menor coste relativo total;
4. mayor número de fills válidos;
5. hash determinista.

Las métricas auxiliares nunca eliminan candidatos en este modo.

## 5. Modos

- `KAMIKAZE_DISCOVERY`: política descrita arriba.
- `OBSERVATION_ONLY`: no selecciona; solo recopila métricas.
- `ROBUSTNESS_LATER`: reservado para una fase posterior y separado del MVP.

## 6. Requisitos no funcionales

- Reproducibilidad total.
- Reanudación tras fallos.
- Idempotencia de jobs.
- Estrategias sin Python libre.
- Trazabilidad de cada dato y decisión.
- Separación entre API, workers y simuladores.
- Posibilidad de ejecutar en un único VPS y escalar después.
