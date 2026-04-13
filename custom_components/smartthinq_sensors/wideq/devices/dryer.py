"""------------------for Dryer"""

from __future__ import annotations
import logging

from ..const import DryerFeatures, StateOptions
from ..core_async import ClientAsync
from ..core_exceptions import InvalidDeviceStatus
from ..device import Device, DeviceStatus
from ..device_info import DeviceInfo, DeviceType

_LOGGER = logging.getLogger(__name__)

REFR_ROOT_DATA = "washerDryer"

class DryerDevice(Device):
    
    def __init__(self, client: ClientAsync, device_info: DeviceInfo):
        super().__init__(client, device_info, DryerStatus(self))
        self._is_running = False
    
    async def poll(self) -> DryerStatus | None:
        """Poll the device's current state."""
        
        res = await self._device_poll(REFR_ROOT_DATA)
        _LOGGER.debug("DryerDevice._device_poll('%s'): %s", REFR_ROOT_DATA, res)
        if not res:
            return None

        self._status = DryerStatus(self, res)
        return self._status
    
    async def set(
        self, ctrl_key, command, *, key=None, value=None, data=None, ctrl_path=None
    ):
        """Set a device's control for `key` to `value`."""
        await super().set(
            ctrl_key,
            command,
            key=key,
            value=value,
            data=data,
            ctrl_path=ctrl_path,
        )
    
    def update_is_running(self, state):
        self._is_running = state

    @property
    def is_running(self) -> bool:
        if not self._is_running:
            return False
        return self._is_running
    
    async def power_off(self):
        await self.set(["WMControl", "WMOff"])
        if self._status:
            self._status.update_status(DryerFeatures.RUN_STATE, "POWEROFF")

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
        self._internal_run_state = None

    @property
    def is_on(self):
        """Return if device is on."""
        _LOGGER.debug("GET PROPERTY: is_on")
        if not self.has_data:
            return False
        run_state = self.internal_run_state
        if run_state != "POWEROFF":
            return True
        return False
    
    @property
    def internal_run_state(self):
        _LOGGER.debug("GET PROPERTY: internal_run_state")
        if self._data and not self._internal_run_state:
            self._internal_run_state = self._data[DryerFeatures.RUN_STATE]
            #self._device.update_is_running(self._internal_run_state in ["RUNNING", "PAUSE"])
        return self._internal_run_state

    @property
    def run_state(self):
        _LOGGER.debug("GET PROPERTY: run_state")
        status = self.lookup_enum(DryerFeatures.RUN_STATE)
        if status is None:
            return None
        return self._update_feature(DryerFeatures.RUN_STATE, status)
    
    @property
    def standby_state(self):
        _LOGGER.debug("GET PROPERTY: standby_state")
        status = self.lookup_enum(DryerFeatures.STANDBY)
        if status is None:
            return None
        return self._update_feature(DryerFeatures.STANDBY, status)

    @property
    def current_course(self):
        _LOGGER.debug("GET PROPERTY: current_course")
        state = self.lookup_reference("courseDryer24inchBase", ref_key="name")        
        if state is None:
            return None
        return self._device.localize(state)
    
    @property
    def process(self):
        _LOGGER.debug("GET PROPERTY: process")
        state = self.lookup_enum(DryerFeatures.PROCESS)
        if state is None:
            return None
        return self._device.localize(state)
    
    def _update_features(self):
        _ = [
            self.run_state,
            self.standby_state,
            self.register_enum_feature(DryerFeatures.DRY_LEVEL),
            self.register_enum_feature(DryerFeatures.ERROR),
            self.register_enum_feature(DryerFeatures.ECHO_HYBRID),
            self.register_bit_feature(DryerFeatures.REMOTE_START),
        ]