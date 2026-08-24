"""services/semantic_ai/rehydrate_firebase_memory.py
Script oficial para rehidratar el LearningStore persistente desde el snapshot forense de Firebase.
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RehydrateFirebaseMemory")

# Añadir el raíz al path
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from services.semantic_ai.learning_store import learning_store

def main():
    snapshot_path = base_dir / "backups" / "firebase_ultrarentable_recovery_snapshot.json"
    if not snapshot_path.exists():
        logger.error(f"Snapshot no encontrado en {snapshot_path}")
        sys.exit(1)

    logger.info(f"Iniciando rehidratación forense desde {snapshot_path} hacia {learning_store.db_path}...")
    result = learning_store.rehydrate_from_firebase_snapshot(str(snapshot_path))
    logger.info(f"Resultado de la rehidratación: {result}")

    stats = learning_store.get_failure_statistics()
    logger.info(f"Estadísticas consolidadas del LearningStore: {stats}")

    print("\n=======================================================")
    print("✅ REHIDRATACIÓN FORENSE COMPLETADA EXITOSAMENTE")
    print(f"  - Estrategias Rehidratadas: {result['rehydrated_strategies']}")
    print(f"  - Validation Snapshots:     {result['rehydrated_validation_snapshots']}")
    print(f"  - Registros de Fallo:       {result['rehydrated_failure_records']}")
    print(f"  - Patrones de Aprendizaje:  {stats['total_learning_patterns']}")
    print(f"  - Archivo de Base de Datos: {learning_store.db_path}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
