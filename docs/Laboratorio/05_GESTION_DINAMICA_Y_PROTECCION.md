# Gestión dinámica y protección de beneficios

## Problema observado

La estrategia podía subir cientos por ciento y después devolverlo progresivamente hasta cero. Los gráficos mostraban pirámides de crecimiento y caída. La solución no debe destruir la lógica que produce la subida.

## Principio

Separar la señal original de una capa de protección que se activa después de alcanzar hitos.

## Ratchet adaptativo

1. Antes del primer hito, conservar entradas, salidas y piramidación originales.
2. Al multiplicar el capital, crear un suelo de equity.
3. Elevar el porcentaje protegido al alcanzar nuevos hitos.
4. Reducir exposición cuando la equity se acerca al suelo.
5. Retirar beneficios de la subcuenta activa.
6. Desactivar o degradar la estrategia si pierde su comportamiento esperado.

Ejemplo de trabajo mencionado:

- activación al alcanzar 2x;
- proteger aproximadamente 50 % entre 2x y 3x;
- 65 % entre 3x y 5x;
- 75 % por encima de 5x.

Son parámetros experimentales, no reglas finales.

## Herramientas

- trailing de equity, no solo de precio;
- cierres parciales;
- break-even condicionado;
- anti-martingala;
- reducción de apalancamiento por proximidad al suelo;
- separación en subcuentas sacrificables;
- retirada automática;
- límites por régimen y deterioro.

## Regla de evaluación

La protección se mide por:

- reducción del giveback;
- conservación del potencial de cola derecha;
- probabilidad de alcanzar el siguiente hito;
- frecuencia de corte prematuro;
- supervivencia tras costes y slippage.
