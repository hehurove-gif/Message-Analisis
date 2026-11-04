"""Objetos que entrega el parser. Todo vive en memoria; nada se escribe a disco."""
import copy
from dataclasses import dataclass, field, replace

CONTRACT_VERSION = '0.2'


@dataclass(frozen=True)
class Message:
    seq: int
    linea_inicial: int
    linea_final: int
    tipo: str                     # texto | media | system | deleted
    participante: str | None      # A, B… ; None si y solo si tipo == 'system'
    timestamp_original: str
    timestamp_local: str | None   # ISO 8601 sin zona; None si el orden de fecha no se resolvió
    precision: str                # minuto | segundo
    texto: str                    # contenido ORIGINAL
    texto_normalizado: str        # derivado, para análisis (no sustituye a `texto`)
    media_kind: str | None = None

    def to_dict(self):
        d = {k: getattr(self, k) for k in ('seq', 'linea_inicial', 'linea_final', 'tipo', 'participante',
                                           'timestamp_original', 'timestamp_local', 'precision', 'texto',
                                           'texto_normalizado')}
        if self.media_kind:
            d['media_kind'] = self.media_kind
        return d

    def __repr__(self):           # sin texto: un repr o un traceback no debe filtrar contenido privado
        return f'Message(seq={self.seq}, tipo={self.tipo}, participante={self.participante})'


@dataclass(frozen=True)
class ImportResult:
    _report: dict                                 # estado interno protegido: solo números, códigos y líneas
    messages: tuple | None                        # None si la importación no se aceptó
    _anonymization: dict = field(default_factory=dict, repr=False)   # nombre real -> etiqueta; solo memoria
    _losses: frozenset = frozenset()
    _confirmed: bool = False

    def __post_init__(self):
        # Copia profunda al entrar: quien construyó el resultado no conserva una referencia al estado interno.
        object.__setattr__(self, '_report', copy.deepcopy(self._report))
        object.__setattr__(self, '_anonymization', dict(self._anonymization))

    @property
    def report(self):
        """Vista de lectura del reporte: una copia profunda nueva en cada acceso. Modificarla (campos o listas
        anidadas) no altera el resultado; las decisiones se toman solo con el estado interno."""
        return copy.deepcopy(self._report)

    # --- lectura ---
    @property
    def accepted(self):
        return self._report['decision_importacion'] == 'accepted'

    def anonymization_map(self):
        """Nombre real → etiqueta, solo en memoria. No forma parte del reporte."""
        return dict(self._anonymization)

    @property
    def pending_requirements(self):
        req = list(self._report['requisitos_analisis'])
        if self._confirmed and 'CONFIRMAR_TIPO_CONVERSACION' in req:
            req.remove('CONFIRMAR_TIPO_CONVERSACION')
        unp = {x['linea'] for x in self._report['lineas_no_procesadas']}
        if 'REVISAR_LINEAS_NO_PROCESADAS' in req and unp <= set(self._losses):
            req.remove('REVISAR_LINEAS_NO_PROCESADAS')
        return req

    @property
    def analysis_enabled(self):
        """El análisis solo se habilita tras resolver o aceptar expresamente cada requisito pendiente."""
        return self.accepted and not self.pending_requirements

    # --- decisiones explícitas del usuario (nunca automáticas) ---
    def accept_losses(self, lines):
        """Acepta expresamente la pérdida de líneas concretas. Debe nombrar líneas realmente no procesadas."""
        unp = {x['linea'] for x in self._report['lineas_no_procesadas']}
        lines = set(lines)
        if not lines <= unp:
            raise ValueError('solo pueden aceptarse líneas que figuran como no procesadas')
        return replace(self, _losses=self._losses | frozenset(lines))

    def confirm_individual(self):
        """El usuario confirma que es una conversación individual. Solo sobre importaciones aceptadas con el
        tipo pendiente de confirmación: no sobre una bloqueada (fechas ambiguas) ni sobre una rechazada."""
        if not self.accepted:
            raise ValueError('solo puede confirmarse una importación aceptada (esta fue rechazada o está bloqueada)')
        if self._report['estado_tipo_conversacion'] != 'pending_confirmation':
            raise ValueError('la conversación no está pendiente de confirmación')
        return replace(self, _confirmed=True)

    def to_report_dict(self):
        d = copy.deepcopy(self._report)
        d['perdidas_aceptadas'] = sorted(self._losses)
        d['tipo_conversacion_confirmado'] = self._confirmed
        d['analisis_habilitado'] = self.analysis_enabled
        d['requisitos_analisis'] = self.pending_requirements
        return d

    def __repr__(self):
        r = self._report
        return (f"ImportResult(decision={r['decision_importacion']}, calidad={r['estado_calidad']}, "
                f"mensajes={0 if self.messages is None else len(self.messages)})")
