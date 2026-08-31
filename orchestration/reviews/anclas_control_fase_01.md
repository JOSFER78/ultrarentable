# ANCLAS DE CONTROL — Fase 1 (USO EXCLUSIVO DEL ORQUESTADOR)

Verificadas por Hermes antes de que Antigravity entregue. NO se le comunican.

| # | Dato | Valor real | Comando |
| :-- | :--- | ---: | :--- |
| B1 | Scripts de minería/certificación | **26** | `ls scripts/ | grep -cE '^(mine|certify|fast_)'` |
| B2 | Líneas totales de esos scripts | **19396** | `wc -l scripts/mine_and_certify_*.py scripts/certify_*.py scripts/fast_*.py scripts/mine_*.py | tail -1` |
| B3 | Ficheros de test | **115** | `find tests -name 'test_*.py' | wc -l` |
| B4 | HEAD al despachar | **88439c76b** | `git log --oneline -1` |

## Criterios de auditoría de esta fase
- **B4 es el ancla crítica:** si al recibir el DONE el HEAD ha cambiado, Antigravity ha vuelto a
  commitear ⇒ `needs_user_input` inmediato.
- Si dice haber movido N scripts, verificar `ls cuarentena/scripts_legacy_mining/ | wc -l` = N
  y que el manifiesto tenga N líneas con SHA-256 que **el Orquestador recalcula**.
- Verificar que `scripts/mine.py` **no es un wrapper** que invoca a los legacy: si importa o
  ejecuta ficheros de `cuarentena/`, no ha consolidado nada.
- Re-ejecutar `python3 scripts/mine.py --help` y el `--dry-run` por cuenta propia.
- Comprobar que el pytest no trae fallos NUEVOS distintos del INTERNALERROR ya conocido.
