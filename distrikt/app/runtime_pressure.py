"""Read local Linux PSI averages only; unavailable metrics stay unknown."""
import math
from pathlib import Path


def resource_pressure(root=Path('/proc/pressure')):
    readings={}
    for resource,kind in (('cpu','some'),('memory','full'),('io','full')):
        try:
            raw=(root/resource).read_text()[:4096]
            line=next(line for line in raw.splitlines() if line.split() and line.split()[0]==kind)
            values=dict(part.split('=',1) for part in line.split()[1:])
            value=float(values['avg60'])
            if math.isfinite(value) and 0<=value<=100:readings[resource]=value
        except (OSError,ValueError,KeyError,StopIteration,IndexError):continue
    thresholds={'cpu':80,'memory':10,'io':20}
    return {'available':bool(readings),'scope':'system','window_seconds':60,'readings':readings,
            'high':any(value>=thresholds[key] for key,value in readings.items())}
