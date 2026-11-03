"""El lector de referencia (tools/referencia/ref_latency.py) no es el parser del sistema, pero debe
cumplir el principio del contrato v0.2: ninguna línea se anexa o descarta sin clasificar, y los
resultados de los tres chats sintéticos de la Fase 0 no cambian."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'referencia'))
import ref_latency as R  # noqa: E402

SYN = os.path.join(ROOT, 'data', 'synthetic')


def _write(tmp_path, text):
    p = tmp_path / 'chat.txt'
    p.write_text(text, encoding='utf-8')
    return str(p)


def test_continuacion_legitima_se_anexa(tmp_path):
    p = _write(tmp_path, '05/10/2026 09:00 - Ana: hola\nsegunda línea\n05/10/2026 09:01 - Luis: ok\n')
    msgs, anomalies, system = R.load_checked(p)
    assert [m['txt'] for m in msgs] == ['hola\nsegunda línea', 'ok']
    assert anomalies == [] and system == []


def test_timestamp_invalido_se_reporta_y_no_se_anexa(tmp_path):
    p = _write(tmp_path, '05/10/2026 09:00 - Ana: hola\n31/02/2026 10:00 - Ana: imposible\ncola\n')
    msgs, anomalies, _ = R.load_checked(p)
    assert msgs[0]['txt'] == 'hola'                       # nada se anexó al mensaje anterior
    assert anomalies == [(2, 'TIMESTAMP_INVALID'), (3, 'ORPHAN_AFTER_UNPROCESSED')]


def test_aspecto_de_timestamp_no_reconocido(tmp_path):
    p = _write(tmp_path, '05/10/2026 09:00 - Ana: hola\n05-10-2026 09:01 > Ana: raro\n')
    msgs, anomalies, _ = R.load_checked(p)
    assert msgs[0]['txt'] == 'hola' and anomalies == [(2, 'TIMESTAMP_LIKE_UNRECOGNIZED')]


def test_huerfana_antes_del_primer_mensaje(tmp_path):
    msgs, anomalies, _ = R.load_checked(_write(tmp_path, 'Exportado ayer\n05/10/2026 09:00 - Ana: hola\n'))
    assert len(msgs) == 1 and anomalies == [(1, 'ORPHAN_BEFORE_FIRST_MESSAGE')]


def test_load_estricto_rechaza_sin_mostrar_contenido(tmp_path):
    p = _write(tmp_path, '05/10/2026 09:00 - Ana: hola\n05/10/2026 09:01 > Ana: SECRETO\n')
    with pytest.raises(R.ReferenceLoadError) as e:
        R.load(p)
    assert 'SECRETO' not in str(e.value) and 'línea 2' in str(e.value)


def test_no_se_descarta_ninguna_linea_no_vacia(tmp_path):
    texto = ('05/10/2026 08:00 - Los mensajes y las llamadas están cifrados de extremo a extremo.\n'
             '05/10/2026 09:00 - Ana: a\ncont\n\n05/10/2026 09:01 > x\nhuérfana\n')
    msgs, anomalies, system = R.load_checked(_write(tmp_path, texto))
    no_vacias = len([x for x in texto.split('\n') if x.strip()])
    asignadas = len(system) + len(msgs) + 1 + len(anomalies)    # +1: la continuación "cont"
    assert asignadas == no_vacias


# ---- Resultados de Fase 0 que no deben cambiar (ver docs/definiciones_operativas.md y los .esperado.md) ----
@pytest.mark.parametrize('chat,turnos,por_autor,mediana_general', [
    ('01_amistad_equilibrada.txt', 56, {'Lucía': 28, 'Marco': 28}, 12),
    ('02_interes_romantico_unilateral.txt', 63, None, None),
])
def test_resultados_chats_sinteticos(chat, turnos, por_autor, mediana_general):
    msgs = R.load(os.path.join(SYN, chat))
    s = R.summary(msgs, 6)
    assert s['turnos'] == turnos
    if por_autor:
        assert s['turnos_por_autor'] == por_autor
        assert s['agregado']['mediana_general'] == mediana_general
    else:
        assert sorted(s['turnos_por_autor'].values()) == [30, 33]


def test_chat_00_con_hint_dmy():
    s = R.summary(R.load(os.path.join(SYN, '00_escenarios_validacion.txt')), 6)
    assert (s['sesiones'], s['turnos']) == (7, 11)
    a = s['agregado']
    assert (a['mediana_general'], a['mediana_dentro'], a['n_dentro'], a['mediana_entre'], a['n_entre']) == (375, 17.5, 4, 600, 4)
