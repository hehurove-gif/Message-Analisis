"""Privacidad (contrato v0.2, sección 10): sin escritura a disco, sin red, sin nombres ni fragmentos de
contenido en reportes o errores, y mapa de anonimización solo en memoria."""
import builtins
import glob
import json
import os
import socket

import pytest

from parsers import load_config, parse_bytes, parse_file, parse_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp')
FIXTURES = sorted(glob.glob(os.path.join(FIX, '*.txt')))
SECRETO = 'contraseña-del-banco-4471'
CHAT = ('14/10/2026, 09:10 - Zoilo Peñaloza: hola, mi clave es ' + SECRETO + '\n'
        '14/10/2026, 09:11 - Brígida Ñúñez: ok\n'
        '14/10/2026, 25:61 - Zoilo Peñaloza: línea inválida con ' + SECRETO + '\n')


def test_no_se_escribe_nada_a_disco(tmp_path, monkeypatch):
    real_open = builtins.open
    escrituras = []

    def vigilado(file, mode='r', *a, **k):
        if any(c in str(mode) for c in 'wax+'):
            escrituras.append(file)
        return real_open(file, mode, *a, **k)

    monkeypatch.setattr(builtins, 'open', vigilado)
    monkeypatch.chdir(tmp_path)
    antes = set(os.listdir(tmp_path)) | set(os.listdir(os.path.dirname(str(tmp_path))))
    for p in FIXTURES:
        parse_file(p)
    parse_text(CHAT)
    parse_bytes(CHAT.encode())
    assert escrituras == []
    assert set(os.listdir(tmp_path)) | set(os.listdir(os.path.dirname(str(tmp_path)))) == antes


def test_sin_llamadas_de_red(monkeypatch):
    def prohibido(*a, **k):
        raise AssertionError('el parser intentó usar la red')

    for fn in ('socket', 'create_connection', 'getaddrinfo', 'gethostbyname'):
        monkeypatch.setattr(socket, fn, prohibido)
    for p in FIXTURES:
        parse_file(p)
    parse_text(CHAT)


def test_el_codigo_del_parser_no_importa_modulos_de_red_ni_de_escritura():
    prohibidos = ('socket', 'urllib', 'http', 'requests', 'httpx', 'ftplib', 'smtplib', 'subprocess',
                  'tempfile', 'shutil', 'pickle', 'logging')
    for src in glob.glob(os.path.join(ROOT, 'parsers', '*.py')):
        with open(src, encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                s = line.strip()
                if s.startswith(('import ', 'from ')):
                    mod = s.split()[1].split('.')[0]
                    assert mod not in prohibidos, f'{os.path.basename(src)}:{n} importa {mod}'


def test_allow_network_true_no_se_ignora():
    cfg = load_config()
    assert cfg.allow_network is False                 # config.yaml: privacy.allow_network
    from dataclasses import replace
    with pytest.raises(ValueError):
        parse_text(CHAT, replace(cfg, allow_network=True))


def test_reportes_sin_nombres_ni_contenido():
    for res in (parse_text(CHAT), parse_bytes(CHAT.encode()), parse_text(CHAT, date_order_hint='dmy')):
        blob = json.dumps(res.to_report_dict(), ensure_ascii=False) + repr(res) + str(res.report)
        for nombre in ('Zoilo', 'Peñaloza', 'Brígida', 'Ñúñez', SECRETO, 'hola', 'clave'):
            assert nombre not in blob


def test_mapa_de_anonimizacion_solo_en_memoria():
    res = parse_text(CHAT)
    assert res.anonymization_map() == {'Zoilo Peñaloza': 'A', 'Brígida Ñúñez': 'B'}
    assert 'Zoilo' not in json.dumps(res.to_report_dict())
    assert 'Zoilo' not in repr(res) and 'Zoilo' not in repr(res.messages)
    # modificar la copia devuelta no altera el estado interno
    res.anonymization_map().clear()
    assert res.anonymization_map()
    # ningún mensaje conserva el nombre real como participante
    assert {m.participante for m in res.messages} <= {'A', 'B', None}


def test_errores_no_revelan_contenido():
    res = parse_bytes(('hola ' + SECRETO).encode() + b'\xff\xfe')
    assert SECRETO not in json.dumps(res.to_report_dict()) and 'hola' not in repr(res)
    ok = parse_text(CHAT)
    for accion in (lambda: ok.accept_losses([1]), lambda: ok.accept_losses([99]),
                   lambda: parse_text(CHAT).confirm_individual().accept_losses([2])):
        try:
            accion()
        except ValueError as e:
            assert SECRETO not in str(e) and 'Zoilo' not in str(e)
    rechazado = parse_text('14/10/2026, 09:10 - A: x ' + SECRETO + '\n')
    with pytest.raises(ValueError) as e:
        rechazado.confirm_individual()
    assert SECRETO not in str(e.value)


def test_sin_impresiones_ni_registros(capsys):
    parse_text(CHAT)
    parse_bytes(b'\xff')
    out = capsys.readouterr()
    assert out.out == '' and out.err == ''
