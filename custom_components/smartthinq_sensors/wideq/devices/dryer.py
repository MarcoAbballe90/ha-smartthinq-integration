"""------------------for Dryer"""

from __future__ import annotations
import logging

from ..const import DryerFeatures
from ..core_async import ClientAsync
from ..core_exceptions import InvalidDeviceStatus
from ..device import Device, DeviceStatus
from ..device_info import DeviceInfo, DeviceType

_LOGGER = logging.getLogger(__name__)

REFR_ROOT_DATA = "washerDryer"

class DryerDevice(Device):
    
    def __init__(self, client: ClientAsync, device_info: DeviceInfo):
        super().__init__(client, device_info, DryerStatus(self))
    
    async def poll(self) -> DryerStatus | None:
        """Poll the device's current state."""
        
        res = await self._device_poll(REFR_ROOT_DATA)
        _LOGGER.debug("DryerDevice._device_poll('%s'): %s", REFR_ROOT_DATA, res)
        if not res:
            return None

        self._status = DryerStatus(self, res)
        return self._status

class DryerStatus(DeviceStatus):
    """
    Higher-level information about a Dryer current status.

    :param device: The Device instance.
    :param data: JSON data from the API.
    """

    _device: DryerDevice

    def __init__(self, device: DryerDevice, data: dict | None = None):
        """Initialize device status."""
        super().__init__(device, data)

    @property
    def dryer_state(self):
        status = self.lookup_enum("state")
        if status is None:
            return None
        return self._update_feature(DryerFeatures.DRYER_STATE, status)