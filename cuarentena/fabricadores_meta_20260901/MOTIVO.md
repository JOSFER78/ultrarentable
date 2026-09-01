# MOTIVO — cuarentena de los fabricadores de datos de portafolio/meta (2026-09-01)

> Decisión D8 del ORQUESTADOR LOCAL (W6.0), a petición del carril META (`orchestration/results/I3_diseno_meta.md`
> §2 y §7). Cada afirmación fue re-verificada por el orquestador con `grep`/`sed` sobre el árbol
> real antes de mover nada.

| Fichero | Qué fabricaba (ruta:línea del original) | Importadores de producción |
| :--- | :--- | :--- |
| `services/portfolio/portfolio_engine.py` | `116-118`: con <2 trades devuelve 10 retornos de 0,01 y matriz identidad inventados; `126-127`: correlación NaN → identidad en silencio; `149-152`: `HIERARCHICAL_RISK_PARITY` implementado como inversa de varianza (no es HRP) | Solo `services/portfolio/__init__.py` (exportación sin uso) y un test |
| `services/portfolio/portfolio_combiner.py` | `83-86`: correlación sobre NIVELES de equity (error estadístico) y NaN → 0,0; `107`: PF techo arbitrario 99,0 | Ninguno |
| `services/api/app/factory/ultra_portfolio_engine.py` | Huérfano; único importador de `portfolio_engine`/`portfolio_combiner` | Ninguno |
| `services/api/app/factory/portfolio_sprint_engine.py` | `93`: `correlation_score=0.18` literal, nunca calculado; su test no lo comprobaba | Ninguno |

Tests: `tests/test_portfolio_combiner.py` (dedicado) se mueve entero. De
`tests/test_portfolio_provenance_and_zero_mock.py` y `tests/test_portfolio_and_ultra_engine.py`
se extraen SOLO las funciones que probaban estos módulos (copiadas íntegras aquí como
`*__parte_cuarentenada.py`); el resto de cada fichero sigue vivo y se ejecuta.

Lo que sigue vivo y es REAL-ONLY (base de `services/meta/`): `meta_strategy_pipeline.py`,
`meta_ensemble_service.py`. `autonomous_meta_daemon.py` sigue en su sitio pero se retira del
arranque en cuanto el carril FONDEO termine con `main.py` (W6.0.a).

Nunca se usó `rm`. Todo está íntegro bajo su ruta original dentro de esta carpeta; hashes en
`MANIFEST.sha256`.
