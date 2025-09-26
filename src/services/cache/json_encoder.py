"""Custom JSON encoder for cache serialization"""

import json
from datetime import date, datetime


class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects"""

    def default(self, obj):
        if isinstance(obj, datetime | date):
            return obj.isoformat()
        return super().default(obj)
