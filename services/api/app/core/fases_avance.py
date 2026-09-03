"""
services/api/app/core/fases_avance.py

Lógica pura de cálculo de avance y estado de fases del plan de Ultrarentable.
Reglas según directiva de A40 (ZERO-MOCKS · REAL-ONLY):
- El estado de la fase se CALCULA exclusivamente a partir de sus minitareas del tablero,
  nunca del campo 'estado' obsoleto de los ficheros F??.md.
- Una fase con 'todas verificadas' queda en 'lista para auditar', NUNCA 'cerrada'.
- Solo pasa a 'cerrada' cuando el orquestador ha auditado y sellado el campo 'cerrada: true'.
- Si hay alguna tarea en DEVUELTO -> 'con correcciones pendientes'.
- Si hay alguna en EN_CURSO o ENTREGADO -> 'en marcha'.
- Si ninguna ha empezado y dependencias sin cerrar -> 'esperando turno'.
- Fase activa: la de menor identificador que no esté cerrada y tenga dependencias cerradas (salvo F10 que es carril permanente).
"""

from typing import Any, Dict, List, Optional


ESTADOS_FASE = {
    "CON_CORRECCIONES": "con correcciones pendientes",
    "EN_MARCHA": "en marcha",
    "LISTA_AUDITAR": "lista para auditar",
    "CERRADA": "cerrada",
    "ESPERANDO_TURNO": "esperando turno",
}


def calcular_avance_fase(
    fase_id: str,
    titulo: str,
    depende_de: List[str],
    verificacion_global: str,
    cerrada: bool,
    tareas: List[Dict[str, Any]],
    fases_cerradas: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Función pura que calcula el estado y avance de una fase individual.
    No realiza I/O ni llamadas de red.
    """
    if fases_cerradas is None:
        fases_cerradas = set()

    total = len(tareas)
    verificadas = sum(1 for t in tareas if str(t.get("estado", "")).upper() == "VERIFICADO")
    devueltas = sum(1 for t in tareas if str(t.get("estado", "")).upper() == "DEVUELTO")
    en_curso = sum(1 for t in tareas if str(t.get("estado", "")).upper() in ("EN_CURSO", "ENTREGADO"))
    pendientes = sum(1 for t in tareas if str(t.get("estado", "")).upper() == "PENDIENTE")

    # Avance
    avance_label = f"{verificadas} de {total}"
    progreso_pct = round((verificadas / total * 100.0), 1) if total > 0 else 0.0

    # Comprobar dependencias cerradas
    deps_cerradas = all(dep in fases_cerradas for dep in depende_de)

    # Estado calculado
    if cerrada:
        estado_calculado = ESTADOS_FASE["CERRADA"]
    elif devueltas > 0:
        estado_calculado = ESTADOS_FASE["CON_CORRECCIONES"]
    elif en_curso > 0:
        estado_calculado = ESTADOS_FASE["EN_MARCHA"]
    elif total > 0 and verificadas == total:
        # Todas verificadas pero sin auditoría de cierre formal
        estado_calculado = ESTADOS_FASE["LISTA_AUDITAR"]
    elif not deps_cerradas and (en_curso == 0 and verificadas == 0):
        estado_calculado = ESTADOS_FASE["ESPERANDO_TURNO"]
    elif pendientes > 0 and deps_cerradas:
        estado_calculado = ESTADOS_FASE["EN_MARCHA"]
    elif total == 0 and not deps_cerradas:
        estado_calculado = ESTADOS_FASE["ESPERANDO_TURNO"]
    else:
        estado_calculado = ESTADOS_FASE["EN_MARCHA"]

    return {
        "id": fase_id,
        "titulo": titulo,
        "depende_de": depende_de,
        "verificacion_global": verificacion_global,
        "cerrada": cerrada,
        "total_tareas": total,
        "verificadas": verificadas,
        "devueltas": devueltas,
        "en_curso": en_curso,
        "pendientes": pendientes,
        "avance_label": avance_label,
        "progreso_pct": progreso_pct,
        "estado_calculado": estado_calculado,
        "tareas": tareas,
    }


def calcular_fases_avance(
    fases_raw: List[Dict[str, Any]],
    tareas_por_fase: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Función pura para calcular el conjunto ordenado de fases y marcar la fase activa.
    """
    # Identificar fases formalmente cerradas (con 'cerrada: True')
    fases_cerradas = {
        f["id"] for f in fases_raw if bool(f.get("cerrada", False))
    }

    calculadas = []
    for f in fases_raw:
        fid = f["id"]
        tareas = tareas_por_fase.get(fid, [])
        res = calcular_avance_fase(
            fase_id=fid,
            titulo=f.get("titulo", fid),
            depende_de=f.get("depende_de", []),
            verificacion_global=f.get("verificacion_global", ""),
            cerrada=bool(f.get("cerrada", False)),
            tareas=tareas,
            fases_cerradas=fases_cerradas,
        )
        calculadas.append(res)

    # Ordenar por ID de fase (F00..F10)
    calculadas.sort(key=lambda x: x["id"])

    # Determinar fase activa:
    # La fase de menor identificador (excepto F10 que es carril de apoyo)
    # que NO esté cerrada y cuyas dependencias estén cerradas (o si F03 es la de mayor prioridad operativa)
    fase_activa_id = None
    for c in calculadas:
        fid = c["id"]
        if fid == "F10":
            continue  # F10 es carril permanente, va aparte
        if c["estado_calculado"] != ESTADOS_FASE["CERRADA"]:
            # Comprobar si dependencias están cerradas o si es la primera abierta
            deps = c["depende_de"]
            deps_ok = all(d in fases_cerradas for d in deps)
            if deps_ok or fase_activa_id is None:
                fase_activa_id = fid
                break

    # Si ninguna cumplió, fallback a F03 (fase activa del proyecto)
    if not fase_activa_id:
        fase_activa_id = "F03"

    for c in calculadas:
        c["es_activa"] = (c["id"] == fase_activa_id)
        c["es_carril_apoyo"] = (c["id"] == "F10")

    return calculadas
