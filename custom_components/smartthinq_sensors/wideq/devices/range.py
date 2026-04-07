"""------------------for Oven"""

from __future__ import annotations
import logging

from ..const import BIT_OFF, RangeFeatures, StateOptions, TemperatureUnit
from ..core_async import ClientAsync
from ..device import Device, DeviceStatus
from ..device_info import DeviceInfo

_LOGGER = logging.getLogger(__name__)

OVEN_TEMP_UNIT = {
    "@OV_TERM_FAHRENHEIT_W": TemperatureUnit.FAHRENHEIT,
    "@OV_TERM_CELSIUS_W": TemperatureUnit.CELSIUS,
    "0": TemperatureUnit.FAHRENHEIT,
    "1": TemperatureUnit.CELSIUS,
}

REFR_ROOT_DATA = "ovenState"

ITEM_STATE_OFF = "@OV_STATE_INITIAL_W"

ITEM_STATE_ENABLE = "ENABLE"


class RangeDevice(Device):
    """A higher-level interface for a cooking range."""

    def __init__(self, client: ClientAsync, device_info: DeviceInfo):
        super().__init__(client, device_info, RangeStatus(self))

    async def poll(self) -> RangeStatus | None:
        """Poll the device's current state."""

        res = await self._device_poll(REFR_ROOT_DATA)
        _LOGGER.debug("RangeDevice._device_poll('%s'): %s", REFR_ROOT_DATA, res)
        if not res:
            return None

        self._status = RangeStatus(self, res)
        return self._status

    def reset_status(self):
        self._status = RangeStatus(self)
        return self._status

class RangeStatus(DeviceStatus):
    """
    Higher-level information about an range's current status.

    :param device: The Device instance.
    :param data: JSON data from the API.
    """

    _device: RangeDevice

    def __init__(self, device: RangeDevice, data: dict | None = None):
        """Initialize device status."""
        super().__init__(device, data)
        self._oven_internal_temp_unit = None
        self._oven_user_temp_unit = None

    def _get_oven_internal_temp_unit(self):
        """Get the used temperature unit."""
        if not self._oven_internal_temp_unit:
            val = self.lookup_enum("MonTempUnit")
            if not val:
                self._oven_internal_temp_unit = StateOptions.NONE
            else:
                self._oven_internal_temp_unit = OVEN_TEMP_UNIT.get(val, StateOptions.NONE)
        
        return self._oven_internal_temp_unit
    
    def _get_oven_user_temp_unit(self):
        """Get the used temperature unit."""
        if not self._oven_user_temp_unit:
            val = self.lookup_enum("AdjustTempUnit")
            if not val:
                self._oven_user_temp_unit = StateOptions.NONE
            else:
                self._oven_user_temp_unit = OVEN_TEMP_UNIT.get(val, StateOptions.NONE)
        
        return self._oven_user_temp_unit
    
    def _get_user_temp(self, keyF: str, keyC: str):
        unit = self.oven_internal_temp_unit
        if unit == TemperatureUnit.CELSIUS:
            keys_to_check = [keyC, keyF]
        elif unit == TemperatureUnit.FAHRENHEIT:
            keys_to_check = [keyF, keyC]
        else:
            return None
        key = self._get_data_key(keys_to_check)
        status = self.to_int_or_none(self._data.get(key))
        if status is None:
            return None
        return status
    
    def _get_is_enabled(self, key: str):        
        status = self._data.get(key)
        if status is None or status != ITEM_STATE_ENABLE:
            return False
        return True

    @property
    def is_on(self):
        """Return if device is on."""        
        status = self.lookup_enum("UpperOvenState")
        if status is None:
            return None
        if status == ITEM_STATE_OFF:
            return False
        return True

    @property
    def oven_internal_temp_unit(self):
        """Return used temperature unit."""
        return self._get_oven_internal_temp_unit()
    
    @property
    def oven_user_temp_unit(self):
        """Return used temperature unit."""
        return self._get_oven_user_temp_unit()
        
    @property
    def oven_state(self):
        status = self.lookup_enum("UpperOvenState")
        if status is None:
            return None
        return self._update_feature(RangeFeatures.OVEN_STATE, status)

    @property
    def oven_mode(self):
        status = self.lookup_enum("UpperCookMode")
        if status is None:
            return None
        return self._update_feature(RangeFeatures.OVEN_MODE, status)
    
    @property
    def remote_start_enabled(self):
        return self._get_is_enabled("UpperRemoteStart")
    
    @property
    def is_timer_set(self):
        return self._get_is_enabled("UpperTimerSet")
    
    @property
    def oven_target_temp(self):
        return self._get_user_temp("UpperTargetTemp_F", "UpperTargetTemp_C")

    @property
    def oven_current_temp(self):
        return self._get_user_temp("UpperCookTemp_F", "UpperCookTemp_C")

    @property
    def oven_cook_time_hours(self):
        val = self._data.get("UpperCookTimeHour")
        return self.to_int_or_none(val)
    
    @property
    def oven_cook_time_minutes(self):
        val = self._data.get("UpperCookTimeMin")
        return self.to_int_or_none(val)
    
    @property
    def oven_timer_hours(self):
        val = self._data.get("UpperTimerHour")
        return self.to_int_or_none(val)
    
    @property
    def oven_timer_minutes(self):
        val = self._data.get("UpperTimerMin")
        return self.to_int_or_none(val)
    
    def _update_features(self):
        _ = [
            self.oven_state,
            self.oven_mode,
        ]
