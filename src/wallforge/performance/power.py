"""Battery / power state detection."""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

kernel32 = ctypes.windll.kernel32


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wt.BYTE),
        ("BatteryFlag", wt.BYTE),
        ("BatteryLifePercent", wt.BYTE),
        ("Reserved1", wt.BYTE),
        ("BatteryLifeTime", wt.DWORD),
        ("BatteryFullLifeTime", wt.DWORD),
    ]


def get_power_status() -> dict:
    s = SYSTEM_POWER_STATUS()
    if kernel32.GetSystemPowerStatus(ctypes.byref(s)):
        # ACLineStatus: 0=offline(battery), 1=online(AC), 255=unknown
        return {
            "on_ac": s.ACLineStatus == 1,
            "battery_percent": s.BatteryLifePercent
            if s.BatteryLifePercent != 255 else None,
        }
    return {"on_ac": True, "battery_percent": None}
