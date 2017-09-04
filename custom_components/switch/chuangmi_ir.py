"""
Support for Chuang Mi IR Remote Controller.

Thank rytilahti for his great work
"""
import logging
from datetime import timedelta
import asyncio
from random import randint
import voluptuous as vol
from socket import timeout

import homeassistant.loader as loader
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_SWITCHES,
                                 CONF_COMMAND_OFF, CONF_COMMAND_ON,
                                 CONF_TIMEOUT, CONF_HOST, CONF_TOKEN,
                                 CONF_TYPE, CONF_NAME, )
import homeassistant.helpers.config_validation as cv
from homeassistant.util.dt import utcnow
from homeassistant.exceptions import PlatformNotReady

REQUIREMENTS = ['python-mirobo']

_LOGGER = logging.getLogger(__name__)

DEVICE_DEFAULT_NAME = 'chuang_mi_ir'
SWITCH_DEFAULT_NAME = 'chuang_mi_ir_switch'
DOMAIN = "chuangmi"
DEFAULT_TIMEOUT = 10
DEFAULT_RETRY = 3
SERVICE_LEARN = "learn_command"
SERVICE_SEND = "send_packet"
ATTR_PACKET = 'packet'
CONF_RETRIES = 'retries'

SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_COMMAND_OFF, default=None):
        vol.All(cv.string, vol.Length(min=1)),
    vol.Optional(CONF_COMMAND_ON, default=None):
        vol.All(cv.string, vol.Length(min=1)),
    vol.Optional(CONF_NAME, default=SWITCH_DEFAULT_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SWITCHES, default={}):
        vol.Schema({cv.slug: SWITCH_SCHEMA}),
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
    vol.Optional(CONF_NAME, default=DEVICE_DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    vol.Optional(CONF_RETRIES, default=DEFAULT_RETRY): cv.positive_int
})

CHUANGMIIR_SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_PACKET): vol.All(cv.string, vol.Length(min=1)),
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the smart mi fan platform."""
    from mirobo import Device, DeviceException
    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)
    devices = config.get(CONF_SWITCHES, {})
    retries = config.get(CONF_RETRIES)
    persistent_notification = loader.get_component('persistent_notification')

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])

    try:
        ir_remote = Device(host, token)
    except DeviceException:
        _LOGGER.info("Connection failed.")
        raise PlatformNotReady

    @asyncio.coroutine
    def _learn_command(call):

        key = randint(1, 1000000)
        ir_remote.send("miIO.ir_learn", {'key': str(key)})

        _LOGGER.info(
            "Press the key of your remote control you want to capture")
        start_time = utcnow()
        while (utcnow() - start_time) < timedelta(seconds=DEFAULT_TIMEOUT):
            res = ir_remote.send("miIO.ir_read", {'key': str(key)})
            if res["code"]:
                log_msg = 'Captured infrared command: %s' % res["code"]
                _LOGGER.info(log_msg)
                persistent_notification.async_create(
                    hass, log_msg, title='Chuang Mi IR Remote Controller')
                return
            yield from asyncio.sleep(1, loop=hass.loop)

        log_msg = 'Timeout. No infrared command captured.'
        _LOGGER.error(log_msg)
        persistent_notification.async_create(
            hass, log_msg, title='Chuang Mi IR Remote Controller')

    @asyncio.coroutine
    def _send_packet(call):
        packet = str(call.data.get(ATTR_PACKET))
        if packet:
            for retry in range(retries):
                try:
                    ir_remote.send(
                        "miIO.ir_play", {'freq': 38400, 'code': packet})
                    break
                except (timeout, ValueError):
                    _LOGGER.error("Send packet failed.")
        else:
            _LOGGER.debug("Empty packet skipped.")

    hass.services.register(
        DOMAIN, SERVICE_LEARN + '_' + host.replace('.', '_'), _learn_command)

    hass.services.register(
        DOMAIN, SERVICE_SEND + '_' + host.replace('.', '_'), _send_packet)

    switches = []
    for object_id, device_config in devices.items():
        switches.append(
            ChuangMiInfraredSwitch(
                ir_remote,
                device_config.get(CONF_NAME, object_id),
                device_config.get(CONF_COMMAND_ON),
                device_config.get(CONF_COMMAND_OFF)
            )
        )

    add_devices(switches)


class ChuangMiInfraredSwitch(SwitchDevice):
    """Representation of an Chuang Mi IR switch."""

    def __init__(self, device, name, command_on, command_off):
        """Initialize the switch."""
        self._name = name
        self._state = False
        self._command_on = command_on or None
        self._command_off = command_off or None
        self._device = device

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def assumed_state(self):
        """Return false if unable to access real state of entity."""
        return False

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._send_packet(self._command_on):
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._send_packet(self._command_off):
            self._state = False
            self.schedule_update_ha_state()

    def _send_packet(self, packet):
        """Send packet to device."""

        packet = str(packet)
        if not packet:
            _LOGGER.debug("Empty packet skipped.")
            return True
        try:
            self._device.send(
                "miIO.ir_play", {'freq': 38400, 'code': packet})
        except (timeout, ValueError) as error:
            _LOGGER.error(error)
            return False
        return True
