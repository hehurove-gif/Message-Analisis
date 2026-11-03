"""Aplicación de la política de privacidad en tiempo de ejecución (no basta con declararla en YAML).

El parser no contiene ninguna funcionalidad de red ni de escritura. Aquí se hace explícito: si la
configuración pidiera red (`allow_network: true`), el parser se niega a ejecutarse en vez de ignorarlo."""


def enforce(cfg):
    if cfg.allow_network:
        raise ValueError('privacy.allow_network=true no es compatible con el parser: procesamiento 100% local')
