"""Optional UI metadata; the original Danish ValueError contract stays unchanged."""


class UIError(ValueError):
    def __init__(self, key, **params):
        self.ui_key = key
        self.ui_params = params
        super().__init__(key.format(**params))


def error_payload(error):
    result = {'error': str(error)}
    if isinstance(error, UIError):
        result['ui_error'] = {'key': error.ui_key, 'params': dict(error.ui_params)}
    return result
