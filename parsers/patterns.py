"""Catálogos de marcadores de multimedia/eliminado y de avisos del sistema.

TODOS son SIMULADOS (o extrapolados de documentación de terceros); ninguno está observado en una exportación
real. Están en tablas para poder añadir idiomas o variantes sin reescribir el parser. Un aviso que no esté
aquí NO se descarta: se reporta como `sin_catalogar` (y por eso la evidencia de grupo nunca puede descartarse).
Los marcadores se comparan con el cuerpo COMPLETO del mensaje (un marcador dentro de un texto más largo es texto).
"""
import re

LRM_RLM = '‎‏'


def strip_marks(text):
    """Solo para COMPARAR con los catálogos; nunca altera el contenido guardado."""
    return text.strip(LRM_RLM + ' \t')


# ---- multimedia omitida (cuerpo completo). (patrón, media_kind) ----
MEDIA_PATTERNS = [
    (re.compile(r'<Multimedia omitido>'), 'desconocido'),
    (re.compile(r'<Media omitted>'), 'desconocido'),
    (re.compile(r'(?i)imagen omitida|image omitted'), 'imagen'),
    (re.compile(r'(?i)sticker omitido|sticker omitted'), 'sticker'),
    (re.compile(r'(?i)audio omitido|audio omitted'), 'audio'),
    (re.compile(r'(?i)video omitido|video omitted'), 'video'),
    (re.compile(r'(?i)documento omitido|document omitted'), 'documento'),
]
# Adjunto con nombre de archivo: "IMG-20261014-WA0001.jpg (archivo adjunto)" / "(file attached)".
ATTACHMENT = re.compile(r'(?P<name>\S.*?)\.(?P<ext>\w{2,5}) \((?:archivo adjunto|file attached)\)')
EXT_KIND = {'jpg': 'imagen', 'jpeg': 'imagen', 'png': 'imagen', 'gif': 'imagen',
            'webp': 'sticker', 'mp4': 'video', 'mov': 'video', '3gp': 'video',
            'opus': 'audio', 'mp3': 'audio', 'm4a': 'audio', 'ogg': 'audio', 'aac': 'audio',
            'pdf': 'documento', 'docx': 'documento', 'xlsx': 'documento', 'pptx': 'documento', 'txt': 'documento'}

# ---- mensaje eliminado (cuerpo completo) ----
DELETED_PATTERNS = [re.compile(p) for p in (
    r'Se eliminó este mensaje\.?', r'Eliminaste este mensaje\.?',
    r'You deleted this message\.?', r'This message was deleted\.?')]


def media_kind(body):
    """media_kind si el cuerpo completo es un marcador de multimedia/adjunto, si no None."""
    b = strip_marks(body)
    for pat, kind in MEDIA_PATTERNS:
        if pat.fullmatch(b):
            return kind
    m = ATTACHMENT.fullmatch(b)
    if m:
        return EXT_KIND.get(m.group('ext').lower(), 'desconocido')
    return None


def is_deleted(body):
    b = strip_marks(body)
    return any(p.fullmatch(b) for p in DELETED_PATTERNS)


# ---- avisos del sistema ----
# Los nombres de los actores no pueden contener ":" (`[^:]+`): así un mensaje de persona "Ana: ..." nunca
# coincide con un aviso, y un aviso con ":" en su parte final (E04) sí se reconoce antes de separar el autor.
_ACT = r'[^:]+?'
# (código de evidencia de grupo o None, patrón). Estos avisos son propios de un GRUPO.
GROUP_NOTICES = [(code, re.compile(p)) for code, p in (
    ('GROUP_CREATED', rf'{_ACT} creó el grupo ".*"'),
    ('GROUP_CREATED', rf'{_ACT} created group ".*"'),
    ('MEMBER_ADDED', rf'{_ACT} añadió a .+'),
    ('MEMBER_ADDED', rf'{_ACT} added .+'),
    ('MEMBER_LEFT', rf'{_ACT} salió'),
    ('MEMBER_LEFT', rf'{_ACT} left'),
    ('MEMBER_JOINED_LINK', rf'{_ACT} se unió mediante el enlace de invitación del grupo'),
    ('MEMBER_JOINED_LINK', rf'{_ACT} joined using this group\'s invite link'),
    ('SUBJECT_CHANGED', rf'{_ACT} cambió el asunto (?:de ".*" )?a ".*"'),
    ('SUBJECT_CHANGED', rf'{_ACT} changed the subject (?:from ".*" )?to ".*"'),
    ('ICON_CHANGED', rf'{_ACT} cambió el ícono de este grupo'),
    ('ICON_CHANGED', rf'{_ACT} changed this group\'s icon'),
    ('DESCRIPTION_CHANGED', rf'{_ACT} cambió la descripción del grupo'),
    ('DESCRIPTION_CHANGED', rf'{_ACT} changed the group description'),
)]
# Avisos CONOCIDOS que no indican grupo (también aparecen en chats individuales).
KNOWN_NON_GROUP_NOTICES = [re.compile(p) for p in (
    r'Los mensajes y las llamadas están cifrados de extremo a extremo\b.*',
    r'Messages and calls are end-to-end encrypted\b.*',
    r'Los mensajes temporales están activados\b.*',
    rf'{_ACT} cambió su número de teléfono\b.*',
)]


def classify_notice(body):
    """('grupo', código) | ('conocido', None) | None, comparando el cuerpo COMPLETO con el catálogo."""
    b = strip_marks(body)
    for code, pat in GROUP_NOTICES:
        if pat.fullmatch(b):
            return 'grupo', code
    if any(p.fullmatch(b) for p in KNOWN_NON_GROUP_NOTICES):
        return 'conocido', None
    return None


def is_known_notice_text(text):
    """¿El texto (tras `Autor: `) es un aviso conocido que el archivo mostró con un nombre antepuesto (B01)?
    Solo los avisos conocidos que no son de grupo: es una hipótesis sin verificar con exportaciones reales."""
    b = strip_marks(text)
    return any(p.fullmatch(b) for p in KNOWN_NON_GROUP_NOTICES)
