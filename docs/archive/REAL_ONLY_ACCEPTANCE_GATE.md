# Puerta de aceptación REAL-ONLY local

Una fase solo puede declararse completa cuando:

1. El código ha sido ejecutado.
2. Los tests relevantes han pasado y se conserva su salida.
3. Los datos provienen de BingX o de una fuente registrada.
4. Existe RAW y checksum antes de normalizar.
5. Las velas abiertas están excluidas.
6. No existen valores financieros inventados.
7. Las rutas funcionan fuera del PC del desarrollador.
8. El proyecto arranca sin Docker.
9. La interfaz consulta endpoints reales.
10. No hay `Math.random()` ni temporizadores de progreso en producción.
11. Los módulos vacíos muestran estado real y acción concreta.
12. Los resultados incluyen estrategia, dataset, semilla, versión y artefactos.
13. Un resultado `CANONICAL` tiene ledger independiente.
14. Live trading permanece desactivado por defecto.
