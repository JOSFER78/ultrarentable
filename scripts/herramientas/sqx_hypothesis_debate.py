"""Debate semántico de agentes para proponer hipótesis de mejora de UNA estrategia.

Los agentes piensan; los programas ejecutan y miden. Este módulo prepara un dosier
determinista (contrato, diagnóstico de órdenes, catálogo de parámetros mutables,
variantes ya exploradas y criterios), lo somete a dos proponentes independientes
con lentes distintas, a un crítico que intenta refutar cada propuesta y a un
árbitro que selecciona como máximo `max_variants` sin forzar consenso. Cada
propuesta se valida con el motor de mutaciones antes de llegar al crítico: lo
que no se puede construir no se debate como si fuera ejecutable.

Guardas (de la práctica publicada sobre debates de agentes, ver
INVESTIGACION_DEBATE_SEMANTICO.md): proponentes ciegos entre sí (evita la
adulación y la homogeneización), evidencia solo del dosier (los agentes no
inventan cifras), desacuerdos conservados en el registro, presupuesto de
búsqueda contabilizado (número de hipótesis consideradas) para la corrección
por pruebas múltiples, y salida JSON con esquema.

Proveedores: `anthropic` (SDK oficial; para el servicio en la VPS),
`claude-cli` (Claude Code en modo impresión, para demostraciones desde el PC) y
`replay` (respuestas grabadas, para pruebas sin red).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sqx_variant_mutations as mutations  # noqa: E402

SCHEMA = 'ultrarentable.hypothesis_debate.v1'
DEFAULT_MODEL = 'claude-opus-5'

CHANGE_SCHEMA = {
    'type': 'object',
    'properties': {
        'direction': {'type': 'string', 'enum': ['long', 'short', 'both']},
        'exit': {'type': 'string', 'enum': list(mutations.EXIT_KEYS)},
        'value': {'type': 'string'},
        'atr_period': {'type': 'string'},
        'param_path': {'type': 'string'},
        'filter': {'type': 'string', 'enum': list(mutations.FILTER_KINDS)},
        'from': {'type': 'integer'},
        'to': {'type': 'integer'},
        'days': {'type': 'array', 'items': {'type': 'string'}},
    },
    'additionalProperties': False,
}
PROPOSAL_SCHEMA = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'title': {'type': 'string'},
        'problem': {'type': 'string'},
        'evidence_codes': {'type': 'array', 'items': {'type': 'string'}},
        'mechanism': {'type': 'string'},
        'change': {'type': 'string'},
        'changes': {'type': 'array', 'items': CHANGE_SCHEMA, 'minItems': 1, 'maxItems': 6},
        'expected': {'type': 'string'},
        'destination_expectation': {'type': 'object', 'properties': {'fondeo': {'type': 'string'}, 'ultra': {'type': 'string'}},
                                    'required': ['fondeo', 'ultra'], 'additionalProperties': False},
        'acceptance': {'type': 'string'},
        'risks': {'type': 'string'},
        'confidence': {'type': 'string', 'enum': ['baja', 'media', 'alta']},
    },
    'required': ['id', 'title', 'problem', 'evidence_codes', 'mechanism', 'change', 'changes', 'expected',
                 'destination_expectation', 'acceptance', 'risks', 'confidence'],
    'additionalProperties': False,
}
PROPOSER_SCHEMA = {
    'type': 'object',
    'properties': {
        'analysis': {'type': 'string'},
        'proposals': {'type': 'array', 'items': PROPOSAL_SCHEMA, 'maxItems': 3},
        'capability_gaps': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['analysis', 'proposals', 'capability_gaps'],
    'additionalProperties': False,
}
CRITIC_SCHEMA = {
    'type': 'object',
    'properties': {
        'verdicts': {'type': 'array', 'items': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'verdict': {'type': 'string', 'enum': ['ACEPTAR', 'REFUTAR', 'REVISAR']},
                'reasons': {'type': 'array', 'items': {'type': 'string'}},
                'overfitting_risk': {'type': 'string', 'enum': ['bajo', 'medio', 'alto']},
                'revised_acceptance': {'type': 'string'},
            },
            'required': ['id', 'verdict', 'reasons', 'overfitting_risk', 'revised_acceptance'],
            'additionalProperties': False,
        }},
        'general_objections': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['verdicts', 'general_objections'],
    'additionalProperties': False,
}
ARBITER_SCHEMA = {
    'type': 'object',
    'properties': {
        'selected_ids': {'type': 'array', 'items': {'type': 'string'}},
        'rationale': {'type': 'string'},
        'dissent': {'type': 'array', 'items': {'type': 'string'}},
        'next_round_if_all_fail': {'type': 'string'},
    },
    'required': ['selected_ids', 'rationale', 'dissent', 'next_round_if_all_fail'],
    'additionalProperties': False,
}

SYSTEM_COMMON = (
    'Eres parte del motor de mejora de estrategias de Ultrarentable. Trabajas SOLO con el dosier '
    'que recibes: no inventes cifras, indicadores ni resultados; cita los códigos de hallazgo y los '
    'números del dosier. Un cambio solo es válido si se expresa con el vocabulario de cambios permitido. '
    'Las decisiones de aceptación las tomarán programas deterministas con los criterios pre-registrados '
    'del dosier: tu trabajo es razonar, no medir. Responde en español y únicamente con el JSON pedido.'
)
LENSES = {
    'proponente_salidas_riesgo': 'Lente: salidas y gestión del riesgo por operación (objetivo, stop, trailing, tiempo en mercado).',
    'proponente_estructura_frecuencia': 'Lente: estructura de la señal, frecuencia de oportunidades y relevancia para el destino (parámetros de '
                                        'indicadores, validez de la orden, filtros de hora o día con justificación estructural de la sesión, '
                                        'dirección operada).',
}
# Tablas por segmento (hora, día, dirección) que solo se muestran de la muestra de construcción:
# elegir un filtro mirando el OOS convertiría la comprobación de desarrollo en ajuste.
SEGMENT_TABLES = ('by_entry_hour_local', 'by_weekday', 'by_direction')
SEGMENT_FINDING_CODES = ('LOSS_CONCENTRATED_SEGMENT',)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, path)


# ----------------------------------------------------------------- dosier

def compact_sample(sample: dict, hide_segments: bool = False) -> dict:
    keep = {
        'summary': sample['summary'],
        'concentration': sample['concentration'],
        'exit_types': {k: v['trades'] for k, v in sample['exit_efficiency']['close_types'].items()},
        'exit_efficiency': {k: v for k, v in sample['exit_efficiency'].items() if k != 'close_types'},
        'r_multiples': sample['r_multiples'],
        'by_entry_hour_local': {k: (v['trades'], v['net']) for k, v in sample['time']['by_entry_hour_local'].items()},
        'by_weekday': {k: (v['trades'], v['net']) for k, v in sample['time']['by_weekday'].items()},
        'by_direction': {k: (v['trades'], v['net'], v['profit_factor']) for k, v in sample['time']['by_direction'].items()},
        'by_year': {k: (v['trades'], v['net']) for k, v in sample['time']['by_year'].items()},
        'frequency': sample['frequency'],
        'exam_screen_5d': {sid: s['horizons']['5'] for sid, s in sample['exam_screen_provisional'].items()},
    }
    if hide_segments:
        for table in SEGMENT_TABLES:
            keep.pop(table, None)
        keep['segment_tables_hidden'] = 'Las tablas por hora, día y dirección de esta muestra no se muestran: el OOS es la comprobación de desarrollo y no se ajusta sobre él.'
    return keep


def visible_findings(findings: list[dict]) -> list[dict]:
    """Hallazgos del dosier: en OOS, los de segmento conservan el código pero no el segmento concreto."""
    out = []
    for finding in findings:
        if finding.get('sample') == 'OOS' and finding.get('code') in SEGMENT_FINDING_CODES:
            evidence = {k: v for k, v in (finding.get('evidence') or {}).items() if k in ('dimension',)}
            out.append({**finding, 'evidence': {**evidence, 'segment': 'oculto (no ajustar sobre OOS)'}, 'segment_hidden': True})
        else:
            out.append(finding)
    return out


def build_dossier(contract: dict, diagnosis: dict, rules_xml: bytes, explored: dict, criteria: dict) -> dict:
    catalogue = mutations.mutable_parameters(rules_xml)
    exits, current_filters = {}, {}
    root = mutations.ET.fromstring(rules_xml)
    for direction in ('long', 'short'):
        exits[direction] = {name: mutations.read_exit(rules_xml, direction, name) for name in mutations.EXIT_KEYS}
        try:
            current_filters[direction] = mutations.entry_filters(mutations._entry_rule(root, direction))
        except ValueError as error:
            current_filters[direction] = {'error': str(error)}
    bars_valid = {e.get('direction'): e.get('bars_valid') for e in contract['rules'].get('entries', [])}
    return {
        'strategy': {
            'name': contract['identity']['name'], 'symbol': contract['market']['symbol'],
            'timeframe': contract['market']['timeframe'], 'instrument': contract['market'].get('instrument_name'),
            'period': contract['period'], 'costs': contract['costs'], 'sizing': contract['sizing'],
            'options': contract['options'], 'rules': contract['rules'],
            'destination_hints': contract['destination_hints'],
        },
        'diagnosis': {
            'timezone': diagnosis['timezone'], 'point_value': diagnosis['point_value'],
            'samples': {k: compact_sample(v, hide_segments=(k != 'IS')) for k, v in diagnosis['samples'].items()},
            'findings': visible_findings(diagnosis['findings']),
            'exposure_study_fondeo': {k: v.get('by_contracts') for k, v in (diagnosis.get('exposure_study_fondeo') or {}).items()},
            'limitations': diagnosis['limitations'],
        },
        'mutation_vocabulary': {
            'exits': {'description': 'Cambios de salida por dirección: {"direction": "long|short", "exit": <nombre>, "value": "<número>"} '
                                     'o "atr_period". Nombres: ' + ', '.join(mutations.EXIT_KEYS),
                      'current': exits},
            'parameters': {'description': 'Cambios de parámetro numérico por ruta: {"param_path": "<path>", "value": "<número>"}. '
                                          'Solo rutas de este catálogo; respeta min/max declarados.',
                           'catalogue': catalogue},
            'filters': {
                'description': 'Filtros de entrada añadidos como condiciones nativas de SQX a la regla de entrada de la dirección indicada '
                               '("direction": "long"|"short"|"both"). '
                               '{"filter": "hour_range", "direction": ..., "from": H1, "to": H2}: la señal solo se toma si H1 <= hora de la barra < H2 '
                               '(horas enteras 0-24, zona horaria de los datos = la misma de by_entry_hour_local). '
                               '{"filter": "exclude_weekdays", "direction": ..., "days": ["Monday", ...]}: sin señal esos días (máximo tres; nombres en inglés o español). '
                               '{"filter": "disable_direction", "direction": "long"|"short"}: esa dirección deja de operar. '
                               'Semántica comprobada en SQX (2026-09-06): la hora filtrada es la de apertura de la barra que acaba de cerrar y '
                               'genera la señal; la orden stop queda activa desde la barra siguiente, así que en H1 el primer relleno posible cae '
                               'en la hora from+1 y el último primer relleno en la hora to (para permitir primeros rellenos entre las A y las B, '
                               'usa from=A-1, to=B-1; la tabla by_entry_hour_local está en horas de relleno). La orden sigue válida BarsValid '
                               f'barras ({bars_valid}), así que puede rellenarse después de la ventana, y una orden de la víspera puede '
                               'rellenarse en un día excluido (observado en la apertura de las 08:30). Un filtro cambia la muestra de operaciones: '
                               'la evaluación emparejada por día lo admite, pero exige mejora en construcción Y en desarrollo.',
                'current': current_filters,
                'timeframe': contract['market'].get('timeframe'),
                'guard': 'Un filtro elegido solo porque una celda de la tabla IS pierde es minería de datos: exige una razón estructural '
                         '(apertura/cierre de sesión, liquidez, publicación de datos) y declara en risks cuántas celdas de hora/día miraste.',
            },
            'not_supported_yet': ['añadir o quitar indicadores', 'salidas parciales', 'cambiar la hora de salida EOD u otras opciones de trading '
                                  '(son comunes a control y variantes en el recálculo)', 'cambiar tamaño de posición (se estudia aparte como exposición)',
                                  'cambiar datos o periodo'],
        },
        'explored_variants': [{'hypothesis': v.get('hypothesis'), 'label': v.get('label'), 'changes': v.get('changes'),
                               'class': v.get('class'), 'development': v.get('development'), 'oos_evidence': v.get('oos_evidence')}
                              for v in explored.get('variants', {}).values()],
        'criteria': criteria,
        'search_budget': {'max_variants_this_experiment': criteria.get('max_variants', 2),
                          'hypotheses_already_tested_for_this_strategy': len(explored.get('variants', {}))},
    }


# ------------------------------------------------------------- proveedores

class Provider:
    name = 'abstract'

    def complete(self, role: str, system: str, user: str, schema: dict) -> dict:
        raise NotImplementedError


class AnthropicProvider(Provider):
    """SDK oficial; salida con esquema JSON (output_config.format)."""
    name = 'anthropic'

    def __init__(self, model=DEFAULT_MODEL, effort='high'):
        import anthropic  # noqa: F401  (import perezoso: el SDK solo hace falta en el servicio)
        self.anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model, self.effort = model, effort

    def complete(self, role, system, user, schema):
        response = self.client.messages.create(
            model=self.model, max_tokens=16000, system=system,
            output_config={'effort': self.effort, 'format': {'type': 'json_schema', 'schema': schema}},
            messages=[{'role': 'user', 'content': user}],
        )
        if response.stop_reason == 'refusal':
            raise RuntimeError(f'El modelo rechazó la petición ({role})')
        text = next(b.text for b in response.content if b.type == 'text')
        usage = response.usage
        return {'data': json.loads(text), 'raw': text, 'model': response.model,
                'usage': {'input_tokens': usage.input_tokens, 'output_tokens': usage.output_tokens,
                          'cache_read_input_tokens': getattr(usage, 'cache_read_input_tokens', None)}}


class ClaudeCliProvider(Provider):
    """Claude Code en modo impresión (`claude -p --bare`), sin herramientas ni terminal visible."""
    name = 'claude-cli'

    def __init__(self, model='opus', binary=None, timeout=900):
        import shutil
        self.model, self.timeout = model, timeout
        self.binary = binary or shutil.which('claude') or 'claude'

    def complete(self, role, system, user, schema):
        # El dosier supera el límite de la línea de órdenes de Windows: va por stdin.
        prompt = user + '\n\nDevuelve ÚNICAMENTE un objeto JSON válido (sin texto alrededor ni bloque de código) que cumpla este esquema JSON:\n' + json.dumps(schema, ensure_ascii=False)
        # Sin --bare: en 2.1.259 el modo mínimo termina con exit 1 y cero tokens (comprobado 2026-09-06).
        command = [self.binary, '-p', '--output-format', 'json', '--model', self.model,
                   '--system-prompt', system, '--disallowedTools', 'Bash,Edit,Write,Read,Glob,Grep,WebSearch,WebFetch,Agent']
        started = time.monotonic()
        for attempt in range(2):
            result = subprocess.run(command, input=prompt, capture_output=True, text=True, encoding='utf-8', timeout=self.timeout)
            if result.returncode != 0:
                raise RuntimeError(f'claude CLI falló ({role}): {result.stderr[-800:]}')
            envelope = json.loads(result.stdout)
            text = envelope.get('result', '')
            match = re.search(r'\{.*\}', text, re.S)
            try:
                data = json.loads(match.group(0) if match else text)
                return {'data': data, 'raw': text, 'model': ','.join(envelope.get('modelUsage', {}).keys()) or self.model,
                        'usage': {k: envelope.get('usage', {}).get(k) for k in ('input_tokens', 'output_tokens', 'cache_read_input_tokens')},
                        'cost_usd': envelope.get('total_cost_usd'), 'seconds': round(time.monotonic() - started, 1)}
            except json.JSONDecodeError:
                prompt = prompt + '\n\nLa respuesta anterior no era JSON válido. Repite SOLO el JSON.'
        raise RuntimeError(f'El modelo no devolvió JSON válido ({role})')


class OmnirouteProvider(Provider):
    """Endpoint de IA del sistema (decisión de Emilio, 2026-09-06): el omnirouter de la VPS de
    Oracle, API compatible con OpenAI. El código no fija un modelo: pide un modelo virtual por
    tarea (`ultrarentable/mejora-<rol>`) y en el panel de superadmin se decide qué IA lo sirve.
    Si ese alias no existe todavía, se usa el alias por defecto y se deja constancia."""
    name = 'omniroute'
    # Comprobado 2026-09-06: la API OpenAI-compatible vive bajo el basePath del contenedor
    # (/pro/omniroute/api/v1); el proxy /v1 de nginx apunta a una ruta inexistente. El combo
    # `auto` enruta a OpenRouter (sin créditos); `auto/best-reasoning` responde vía Antigravity.
    DEFAULT_URL = 'https://omniroute.143-47-35-167.sslip.io/pro/omniroute/api'
    DEFAULT_MODEL = 'auto/best-reasoning'

    def __init__(self, url=None, api_key=None, default_model=None, insecure=None, timeout=600):
        import ssl
        import urllib.request
        self.url = (url or os.environ.get('OMNIROUTE_URL') or self.DEFAULT_URL).rstrip('/')
        self.api_key = api_key or os.environ.get('OMNIROUTE_API_KEY') or ''
        self.default_model = default_model or os.environ.get('OMNIROUTE_DEFAULT_MODEL') or self.DEFAULT_MODEL
        self.timeout = timeout
        self.insecure = (os.environ.get('OMNIROUTE_INSECURE') == '1') if insecure is None else insecure
        self.ssl = ssl
        self.context = ssl._create_unverified_context() if self.insecure else ssl.create_default_context()
        self.request = urllib.request
        self.tls_note = 'unverified' if self.insecure else 'verified'

    @staticmethod
    def task_model(role: str) -> str:
        # Sin barra: en OmniRoute "proveedor/modelo" se interpreta como proveedor, y un
        # proveedor inexistente responde 401 "No active credentials for provider" (comprobado).
        return f'ultrarentable-mejora-{role.split("_")[0]}'  # proponente / critico / arbitro

    def _post(self, payload: dict) -> dict:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        request = self.request.Request(self.url + '/v1/chat/completions', data=json.dumps(payload).encode('utf-8'),
                                       headers=headers, method='POST')
        try:
            response = self.request.urlopen(request, timeout=self.timeout, context=self.context)
        except self.request.URLError as error:
            # El certificado sslip.io del omnirouter no está en el almacén del sistema; se
            # degrada a conexión sin verificar y se deja constancia en el registro de la llamada.
            if isinstance(getattr(error, 'reason', None), self.ssl.SSLError) and not self.insecure:
                self.insecure, self.tls_note = True, 'unverified (certificado no reconocido; degradado)'
                self.context = self.ssl._create_unverified_context()
                response = self.request.urlopen(request, timeout=self.timeout, context=self.context)
            else:
                raise
        with response:
            body = json.loads(response.read().decode('utf-8'))
            decision = response.headers.get('X-OmniRoute-Decision')
        return {'body': body, 'decision': decision}

    def complete(self, role, system, user, schema):
        prompt = user + '\n\nDevuelve ÚNICAMENTE un objeto JSON válido (sin texto alrededor ni bloque de código) que cumpla este esquema JSON:\n' + json.dumps(schema, ensure_ascii=False)
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}]
        started = time.monotonic()
        model, fallback_used = self.task_model(role), False
        last_error = None
        for attempt in range(3):
            payload = {'model': model, 'messages': messages, 'temperature': 0.2, 'max_tokens': 8000}
            try:
                result = self._post(payload)
            except self.request.HTTPError as error:
                detail = error.read().decode('utf-8', errors='replace')[:400]
                # Alias de tarea aún no definido en el panel: 400/404 o 401 "No active credentials for provider".
                if 400 <= error.code < 500 and error.code != 429 and not fallback_used and model != self.default_model:
                    self.fallback_reason = f'HTTP {error.code} para {model}: {detail[:160]}'
                    model, fallback_used = self.default_model, True
                    continue
                raise RuntimeError(f'omniroute HTTP {error.code} ({role}, modelo {model}): {detail}')
            body = result['body']
            text = body['choices'][0]['message']['content'] if body.get('choices') else ''
            match = re.search(r'\{.*\}', text, re.S)
            try:
                data = json.loads(match.group(0) if match else text)
                usage = body.get('usage') or {}
                return {'data': data, 'raw': text, 'model': f"{body.get('model') or model} via {model}" + (' (fallback)' if fallback_used else ''),
                        'usage': {'input_tokens': usage.get('prompt_tokens'), 'output_tokens': usage.get('completion_tokens')},
                        'routing_decision': result['decision'], 'tls': self.tls_note,
                        'fallback_reason': getattr(self, 'fallback_reason', None) if fallback_used else None,
                        'seconds': round(time.monotonic() - started, 1)}
            except json.JSONDecodeError as error:
                last_error = error
                messages = messages[:2] + [{'role': 'assistant', 'content': text[:4000]},
                                           {'role': 'user', 'content': 'La respuesta anterior no era JSON válido. Repite SOLO el JSON.'}]
        raise RuntimeError(f'El modelo no devolvió JSON válido ({role}, modelo {model}): {last_error}')


class ReplayProvider(Provider):
    """Respuestas grabadas por rol (pruebas sin red)."""
    name = 'replay'

    def __init__(self, responses: dict):
        self.responses = responses

    def complete(self, role, system, user, schema):
        if role not in self.responses:
            raise KeyError(f'Sin respuesta grabada para {role}')
        return {'data': self.responses[role], 'raw': json.dumps(self.responses[role]), 'model': 'replay', 'usage': {}}


def make_provider(name: str, model: str | None = None) -> Provider:
    if name == 'omniroute':
        return OmnirouteProvider(default_model=model)
    if name == 'anthropic':
        return AnthropicProvider(model or DEFAULT_MODEL)
    if name == 'claude-cli':
        return ClaudeCliProvider(model or 'opus')
    raise ValueError(f'Proveedor desconocido: {name}')


# ------------------------------------------------------------------ rondas

def validate_proposals(proposals: list[dict], rules_xml: bytes) -> list[dict]:
    """Construye cada propuesta con el motor de mutaciones: aplicable o no, con el error exacto."""
    out = []
    for proposal in proposals:
        entry = dict(proposal)
        try:
            built = mutations.build_variant(rules_xml, proposal['changes'])
            entry['validation'] = {'applicable': True, 'semantic_rules_sha256': built['semantic_rules_sha256'],
                                   'verified_changes': built['changes']}
        except (ValueError, KeyError, TypeError) as error:
            entry['validation'] = {'applicable': False, 'error': str(error)}
        out.append(entry)
    return out


def proposer_prompt(dossier: dict, lens: str) -> str:
    return (
        f'{lens}\n\nAnaliza la estrategia del dosier y propón como máximo tres hipótesis de mejora, cada una con un '
        'cambio concreto expresado en el vocabulario de mutaciones (mutation_vocabulary: salidas, parámetros por ruta y '
        'filtros de hora/día/dirección). Reglas: cita los códigos de hallazgo (diagnosis.findings) y cifras del dosier; '
        'apoya cada hipótesis en la muestra de construcción (IS) y en los agregados OOS disponibles, sin pedir tablas OOS por '
        'segmento (no existen a propósito); no repitas variantes ya exploradas (explored_variants); declara qué resultado, '
        'medido con los criterios del dosier, aceptaría o rechazaría la hipótesis (acceptance); si necesitas una capacidad no '
        'soportada, anótala en capability_gaps en lugar de forzar un cambio. Un filtro de hora o día necesita una razón '
        'estructural, no solo una celda perdedora. Distingue mejora de la estrategia y aumento de exposición.\n\nDOSIER:\n'
        + json.dumps(dossier, ensure_ascii=False)
    )


def critic_prompt(dossier: dict, proposals: list[dict]) -> str:
    return (
        'Eres el crítico. Intenta refutar cada propuesta con el dosier: riesgo de sobreajuste o minería de datos, muestra '
        'insuficiente, mecanismo incoherente con los tipos de cierre y los múltiplos R, efecto irrelevante para el destino, '
        'duplicado de una variante explorada, o cambio no aplicable (validation.applicable=false es refutación automática). '
        'Para filtros de hora, día o dirección: refuta si la única razón es una celda perdedora de la tabla IS (minería de '
        'datos con muchas celdas comparadas), si el segmento excluido tiene pocas operaciones, o si el filtro deja la '
        'frecuencia por debajo de lo que exige el destino; acepta solo con razón estructural y muestra suficiente. '
        'Sé concreto y cita cifras. Emite ACEPTAR, REFUTAR o REVISAR por propuesta, y objeciones generales.\n\nDOSIER:\n'
        + json.dumps(dossier, ensure_ascii=False) + '\n\nPROPUESTAS:\n' + json.dumps(proposals, ensure_ascii=False)
    )


def arbiter_prompt(dossier: dict, proposals: list[dict], critique: dict, max_variants: int) -> str:
    return (
        f'Eres el árbitro. Selecciona como máximo {max_variants} propuestas para recalcular ahora. Solo puedes elegir '
        'propuestas aplicables (validation.applicable=true) y no refutadas; prefiere mecanismos distintos entre sí y '
        'apoyo en ambas muestras; no fuerces consenso: registra el desacuerdo en dissent. Explica la selección y qué '
        'habría que hacer si todas fallan.\n\nDOSIER (resumen de criterios):\n' + json.dumps(dossier['criteria'], ensure_ascii=False)
        + '\n\nPROPUESTAS:\n' + json.dumps(proposals, ensure_ascii=False) + '\n\nCRÍTICA:\n' + json.dumps(critique, ensure_ascii=False)
    )


def run_debate(cycle: Path, provider: Provider, max_variants: int = 2, output: Path | None = None) -> dict:
    output = output or (cycle / 'debate')
    contract = read_json(cycle / 'contract.json')
    diagnosis_path = cycle / 'diagnosis_base_fresh.json' if (cycle / 'diagnosis_base_fresh.json').exists() else cycle / 'diagnosis_base.json'
    diagnosis = read_json(diagnosis_path)
    criteria = read_json(cycle / 'criteria.json') if (cycle / 'criteria.json').exists() else {}
    explored = read_json(cycle / 'explored.json') if (cycle / 'explored.json').exists() else {}
    with zipfile.ZipFile(contract['provenance']['archive_path']) as archive:
        rules_xml = archive.read('strategy_Portfolio.xml')
    dossier = build_dossier(contract, diagnosis, rules_xml, explored, {**criteria, 'max_variants': max_variants})
    write_json(output / 'dossier.json', dossier)
    log = {'schema': SCHEMA, 'started_utc': now(), 'provider': provider.name, 'cycle': str(cycle),
           'dossier_sha256': sha(json.dumps(dossier, sort_keys=True, ensure_ascii=False).encode()), 'calls': []}

    def call(role, system, user, schema):
        started = time.monotonic()
        result = provider.complete(role, system, user, schema)
        record = {'role': role, 'model': result.get('model'), 'usage': result.get('usage'), 'cost_usd': result.get('cost_usd'),
                  'routing_decision': result.get('routing_decision'), 'tls': result.get('tls'),
                  'fallback_reason': result.get('fallback_reason'),
                  'seconds': round(time.monotonic() - started, 1), 'prompt_sha256': sha((system + user).encode()), 'utc': now()}
        log['calls'].append(record)
        write_json(output / f'{role}.json', {**record, 'response': result['data'], 'raw': result.get('raw')})
        return result['data']

    proposals = []
    for role, lens in LENSES.items():
        data = call(role, SYSTEM_COMMON, proposer_prompt(dossier, lens), PROPOSER_SCHEMA)
        for index, proposal in enumerate(data.get('proposals', []), 1):
            proposal['id'] = re.sub(r'[^A-Za-z0-9_]', '_', f"{proposal.get('id') or 'H'}_{role.split('_')[1][:3]}{index}")[:40]
            proposal['proposer'] = role
        proposals.extend(data.get('proposals', []))
        log.setdefault('capability_gaps', []).extend(data.get('capability_gaps', []))
    proposals = validate_proposals(proposals, rules_xml)
    explored_hashes = set(explored.get('variants', {}))
    for proposal in proposals:
        v = proposal['validation']
        if v.get('applicable') and v['semantic_rules_sha256'] in explored_hashes:
            v.update(applicable=False, error='Variante ya explorada (mismo hash semántico de reglas)')
    critique = call('critico', SYSTEM_COMMON, critic_prompt(dossier, proposals), CRITIC_SCHEMA) if proposals else {'verdicts': [], 'general_objections': ['Sin propuestas']}
    verdicts = {v['id']: v for v in critique.get('verdicts', [])}
    arbitration = call('arbitro', SYSTEM_COMMON, arbiter_prompt(dossier, proposals, critique, max_variants), ARBITER_SCHEMA) if proposals else {'selected_ids': [], 'rationale': 'Sin propuestas', 'dissent': [], 'next_round_if_all_fail': ''}
    selected = []
    for pid in arbitration.get('selected_ids', []):
        proposal = next((p for p in proposals if p['id'] == pid), None)
        if proposal is None or not proposal['validation'].get('applicable'):
            continue
        if verdicts.get(pid, {}).get('verdict') == 'REFUTAR':
            continue
        selected.append(proposal)
        if len(selected) >= max_variants:
            break
    hypotheses = [{'id': p['id'], 'title': p['title'], 'problem': p['problem'], 'change': p['change'], 'expected': p['expected'],
                   'acceptance': p['acceptance'], 'evidence_codes': p['evidence_codes'], 'destination_expectation': p['destination_expectation'],
                   'changes': p['changes'], 'proposer': p['proposer'], 'critic_verdict': verdicts.get(p['id'], {}).get('verdict'),
                   'critic_reasons': verdicts.get(p['id'], {}).get('reasons', []), 'confidence': p['confidence']} for p in selected]
    summary = {
        'schema': SCHEMA, 'finished_utc': now(), 'provider': provider.name,
        'models': sorted({c.get('model') or '' for c in log['calls']}),
        'search_budget': {'proposed': len(proposals), 'applicable': sum(1 for p in proposals if p['validation'].get('applicable')),
                          'refuted_by_critic': sum(1 for v in verdicts.values() if v['verdict'] == 'REFUTAR'),
                          'selected': len(selected), 'previously_tested': dossier['search_budget']['hypotheses_already_tested_for_this_strategy']},
        'cost_usd_total': round(sum(c.get('cost_usd') or 0 for c in log['calls']), 4),
        'seconds_total': round(sum(c.get('seconds') or 0 for c in log['calls']), 1),
        'dissent': arbitration.get('dissent', []), 'rationale': arbitration.get('rationale'),
        'next_round_if_all_fail': arbitration.get('next_round_if_all_fail'),
        'general_objections': critique.get('general_objections', []),
        'capability_gaps': log.get('capability_gaps', []),
        'proposals': [{'id': p['id'], 'proposer': p['proposer'], 'title': p['title'], 'applicable': p['validation'].get('applicable'),
                       'validation_error': p['validation'].get('error'), 'critic': verdicts.get(p['id'], {}).get('verdict'),
                       'selected': p in selected} for p in proposals],
    }
    write_json(output / 'hypotheses.json', {'schema': 'ultrarentable.hypotheses.v1', 'source': 'AGENT_DEBATE',
                                            'generated_utc': now(), 'hypotheses': hypotheses})
    write_json(output / 'summary.json', summary)
    write_json(output / 'log.json', log)
    # Intervenciones en el formato que la web de /estrategias/mejora/debate ya espera (dato real, no pregrabado).
    intervenciones = []
    for call_record in log['calls']:
        payload = read_json(output / f"{call_record['role']}.json")['response']
        if call_record['role'].startswith('proponente'):
            texto = payload.get('analysis', '')
        elif call_record['role'] == 'critico':
            texto = ' | '.join(payload.get('general_objections', []))
        else:
            texto = payload.get('rationale', '')
        intervenciones.append({'agente': call_record['role'], 'modelo': call_record.get('model'), 'texto': texto, 'utc': call_record['utc']})
    write_json(output / 'intervenciones.json', {'estrategia': contract['identity']['name'], 'intervenciones': intervenciones,
                                                'veredicto_colegiado': f"{len(selected)} hipótesis seleccionadas de {len(proposals)} propuestas",
                                                'puntuacion_consenso': None, 'nota': 'Debate real registrado; ninguna hipótesis está validada hasta recalcularse y evaluarse.'})
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cycle', type=Path, required=True, help='Directorio del ciclo con contract.json, diagnosis_base*.json, criteria.json y opcionalmente explored.json')
    parser.add_argument('--provider', choices=('omniroute', 'anthropic', 'claude-cli'), default='omniroute',
                        help='omniroute = endpoint de IA del sistema (Oracle); los otros son respaldos de prueba')
    parser.add_argument('--model', help='omniroute: alias por defecto si el alias de tarea no existe; otros: modelo')
    parser.add_argument('--max-variants', type=int, default=2)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run_debate(args.cycle, make_provider(args.provider, args.model), args.max_variants, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
