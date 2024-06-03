from flask.json.provider import DefaultJSONProvider
from datetime import datetime

class FhirJSONProvider(DefaultJSONProvider):
    def __init__(self, app):
        super().__init__(app)

    def default(self, o):
        if isinstance(o, datetime):
            return str(o.isoformat())
        return super().default(self, o)