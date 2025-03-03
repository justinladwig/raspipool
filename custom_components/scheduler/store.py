import logging
import secrets
from collections import OrderedDict
from typing import MutableMapping, cast

import attr
from homeassistant.core import (callback, HomeAssistant)
from homeassistant.loader import bind_hass
from homeassistant.const import (
    ATTR_NAME,
    CONF_CONDITIONS,
)


from . import const

_LOGGER = logging.getLogger(__name__)

DATA_REGISTRY = f"{const.DOMAIN}_storage"
STORAGE_KEY = f"{const.DOMAIN}.storage"
STORAGE_VERSION = 1
SAVE_DELAY = 10


@attr.s(slots=True, frozen=True)
class ActionEntry:
    """Action storage Entry."""

    service = attr.ib(type=str, default="")
    entity_id = attr.ib(type=str, default=None)
    service_data = attr.ib(type=dict, default={})


@attr.s(slots=True, frozen=True)
class ConditionEntry:
    """Condition storage Entry."""

    entity_id = attr.ib(type=str, default=None)
    attribute = attr.ib(type=str, default=None)
    value = attr.ib(type=str, default=None)
    match_type = attr.ib(type=str, default=None)


@attr.s(slots=True, frozen=True)
class TimeslotEntry:
    """Timeslot storage Entry."""

    start = attr.ib(type=str, default=None)
    stop = attr.ib(type=str, default=None)
    conditions = attr.ib(type=[ConditionEntry], default=[])
    condition_type = attr.ib(type=str, default=None)
    actions = attr.ib(type=[ActionEntry], default=[])


@attr.s(slots=True, frozen=True)
class ScheduleEntry:
    """Schedule storage Entry."""

    schedule_id = attr.ib(type=str, default=None)
    weekdays = attr.ib(type=list, default=[])
    timeslots = attr.ib(type=[TimeslotEntry], default=[])
    repeat_type = attr.ib(type=str, default=None)
    name = attr.ib(type=str, default=None)
    enabled = attr.ib(type=bool, default=True)


def parse_schedule_data(data: dict):
    if const.ATTR_TIMESLOTS in data:
        timeslots = []
        for item in data[const.ATTR_TIMESLOTS]:
            timeslot = TimeslotEntry(**item)
            if CONF_CONDITIONS in item and item[CONF_CONDITIONS]:
                conditions = []
                for condition in item[CONF_CONDITIONS]:
                    conditions.append(ConditionEntry(**condition))
                timeslot = attr.evolve(timeslot, **{CONF_CONDITIONS: conditions})
            if const.ATTR_ACTIONS in item and item[const.ATTR_ACTIONS]:
                actions = []
                for action in item[const.ATTR_ACTIONS]:
                    actions.append(ActionEntry(**action))
                timeslot = attr.evolve(timeslot, **{const.ATTR_ACTIONS: actions})
            timeslots.append(timeslot)
        data[const.ATTR_TIMESLOTS] = timeslots
    return data


class ScheduleStorage:
    """Class to hold scheduler data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the storage."""
        self.hass = hass
        self.schedules: MutableMapping[str, ScheduleEntry] = {}
        self._store = hass.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self) -> None:
        """Load the registry of schedule entries."""
        data = await self._store.async_load()
        schedules: "OrderedDict[str, ScheduleEntry]" = OrderedDict()

        if data is not None:
            for entry in data["schedules"]:
                entry = parse_schedule_data(entry)
                schedules[entry[const.ATTR_SCHEDULE_ID]] = ScheduleEntry(
                    schedule_id=entry[const.ATTR_SCHEDULE_ID],
                    weekdays=entry[const.ATTR_WEEKDAYS],
                    timeslots=entry[const.ATTR_TIMESLOTS],
                    repeat_type=entry[const.ATTR_REPEAT_TYPE],
                    name=entry[ATTR_NAME],
                    enabled=entry[const.ATTR_ENABLED],
                )
        self.schedules = schedules

    @callback
    def async_schedule_save(self) -> None:
        """Schedule saving the registry of schedules."""
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

    async def async_save(self) -> None:
        """Save the registry of schedules."""
        await self._store.async_save(self._data_to_save())

    @callback
    def _data_to_save(self) -> dict:
        """Return data for the registry for schedules to store in a file."""
        store_data = {}

        store_data["schedules"] = []

        for entry in self.schedules.values():
            item = {
                const.ATTR_SCHEDULE_ID: entry.schedule_id,
                const.ATTR_TIMESLOTS: [],
                const.ATTR_WEEKDAYS: entry.weekdays,
                const.ATTR_REPEAT_TYPE: entry.repeat_type,
                ATTR_NAME: entry.name,
                const.ATTR_ENABLED: entry.enabled,
            }
            for slot in entry.timeslots:
                timeslot = {
                    const.ATTR_START: slot.start,
                    const.ATTR_STOP: slot.stop,
                    CONF_CONDITIONS: [],
                    const.ATTR_CONDITION_TYPE: slot.condition_type,
                    const.ATTR_ACTIONS: [],
                }
                if slot.conditions:
                    for condition in slot.conditions:
                        timeslot[CONF_CONDITIONS].append(attr.asdict(condition))
                if slot.actions:
                    for action in slot.actions:
                        timeslot[const.ATTR_ACTIONS].append(attr.asdict(action))
                item[const.ATTR_TIMESLOTS].append(timeslot)
            store_data["schedules"].append(item)

        return store_data

    async def async_delete(self):
        """Delete config."""
        _LOGGER.warning("Removing scheduler configuration data!")
        self.schedules = {}
        await self._store.async_remove()

    @callback
    def async_get_schedule(self, entity_id) -> dict:
        """Get an existing ScheduleEntry by id."""
        res = self.schedules.get(entity_id)
        return attr.asdict(res) if res else None

    @callback
    def async_get_schedules(self) -> dict:
        """Get an existing ScheduleEntry by id."""
        res = {}
        for (key, val) in self.schedules.items():
            res[key] = attr.asdict(val)
        return res

    @callback
    def async_create_schedule(self, data: dict) -> ScheduleEntry:
        """Create a new ScheduleEntry."""
        if const.ATTR_SCHEDULE_ID in data:
            # migrate existing schedule to store
            schedule_id = data[const.ATTR_SCHEDULE_ID]
            del data[const.ATTR_SCHEDULE_ID]
            if schedule_id in self.schedules:
                return
            _LOGGER.info("Migrating schedule {}".format(schedule_id))
        else:
            schedule_id = secrets.token_hex(3)
            while schedule_id in self.schedules:
                schedule_id = secrets.token_hex(3)

        data = parse_schedule_data(data)
        new_schedule = ScheduleEntry(**data, schedule_id=schedule_id)
        self.schedules[schedule_id] = new_schedule
        self.async_schedule_save()
        return new_schedule

    @callback
    def async_delete_schedule(self, schedule_id: int) -> None:
        """Delete ScheduleEntry."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self.async_schedule_save()
            return True
        return False

    @callback
    def async_update_schedule(self, schedule_id: int, changes: dict) -> ScheduleEntry:
        """Update existing ScheduleEntry."""
        old = self.schedules[schedule_id]
        changes = parse_schedule_data(changes)
        new = self.schedules[schedule_id] = attr.evolve(old, **changes)
        self.async_schedule_save()
        return new


@bind_hass
async def async_get_registry(hass: HomeAssistant) -> ScheduleStorage:
    """Return alarmo storage instance."""
    task = hass.data.get(DATA_REGISTRY)

    if task is None:

        async def _load_reg() -> ScheduleStorage:
            registry = ScheduleStorage(hass)
            await registry.async_load()
            return registry

        task = hass.data[DATA_REGISTRY] = hass.async_create_task(_load_reg())

    return cast(ScheduleStorage, await task)
