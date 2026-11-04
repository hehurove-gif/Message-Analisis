"""tools/validar_exportacion_local.py: protección de rutas (dentro del repositorio, enlaces simbólicos y
unidades distintas de Windows). El caso de unidades se prueba con `ntpath`, que se comporta igual en
cualquier sistema operativo, así que no se necesita Windows."""
import importlib.util
import ntpath
import os
import shutil

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('validador', os.path.join(ROOT, 'tools', 'validar_exportacion_local.py'))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp', 'A01_android24_coma_es.txt')


def test_ruta_interna_externa():
    assert V.is_inside(FIXTURE, ROOT) is True
    assert V.is_inside(ROOT, ROOT) is True
    assert V.is_inside('/tmp/otro/chat.txt', ROOT) is False
    assert V.is_inside(ROOT + '-hermano/chat.txt', ROOT) is False        # prefijo igual, directorio distinto


def test_unidades_distintas_son_externas_y_no_lanzan():
    with pytest.raises(ValueError):                                      # el problema original
        ntpath.commonpath([r'D:\exportaciones\chat.txt', r'C:\repo'])
    assert V.is_inside(r'D:\exportaciones\chat.txt', r'C:\repo', pm=ntpath) is False


def test_misma_unidad_windows_dentro_y_fuera_sin_distinguir_mayusculas():
    assert V.is_inside(r'C:\repo\tests\chat.txt', r'C:\repo', pm=ntpath) is True
    assert V.is_inside(r'c:\REPO\tests\chat.txt', r'C:\repo', pm=ntpath) is True
    assert V.is_inside(r'C:\otra\chat.txt', r'C:\repo', pm=ntpath) is False
    assert V.is_inside(r'C:\repo-viejo\chat.txt', r'C:\repo', pm=ntpath) is False


def test_main_rechaza_archivo_interno(capsys):
    with pytest.raises(SystemExit) as e:
        V.main([FIXTURE])
    assert 'dentro del repositorio' in str(e.value)
    assert capsys.readouterr().out == ''                 # no se imprimió ningún reporte


def test_main_rechaza_enlace_simbolico_hacia_el_repositorio(tmp_path, capsys):
    enlace = tmp_path / 'inocente.txt'
    try:
        os.symlink(FIXTURE, enlace)
    except (OSError, NotImplementedError):
        pytest.skip('el sistema no permite crear enlaces simbólicos')
    with pytest.raises(SystemExit):
        V.main([str(enlace)])
    assert capsys.readouterr().out == ''


def test_main_acepta_archivo_externo(tmp_path, capsys):
    copia = tmp_path / 'chat.txt'
    shutil.copy(FIXTURE, copia)
    V.main([str(copia)])
    out = capsys.readouterr().out
    assert '"decision_importacion": "accepted"' in out
    assert 'Ana' not in out                              # sin nombres ni contenido


def test_main_con_unidad_distinta_no_falla(monkeypatch, tmp_path):
    copia = tmp_path / 'chat.txt'
    shutil.copy(FIXTURE, copia)
    def otra_unidad(_):
        raise ValueError("Paths don't have the same drive")
    monkeypatch.setattr(V.os.path, 'commonpath', otra_unidad)
    V.main([str(copia)])                                 # tratada como externa: no lanza ValueError
