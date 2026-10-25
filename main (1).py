#***************************************************
# MSSV: 20248977
# Họ và tên: Đào Quý Sang
#***************************************************
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Generic, TypeVar


class DeviceStatus(Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"


# ---- ngoại lệ ----
class DuplicateIdException(Exception):
    pass

class NoSuitableItemException(Exception):
    pass

class DeviceNotReadyException(Exception):
    pass


# ---- thiết bị ----
class IIdentifiable(ABC):
    @property
    @abstractmethod
    def id(self):
        pass


class TeachingDevice(IIdentifiable):
    def __init__(self, device_id, name, storage_location):
        self._id = device_id
        self.name = name
        self.storage_location = storage_location
        self.status = DeviceStatus.AVAILABLE

    @property
    def id(self):
        return self._id

    @abstractmethod
    def is_ready_for_use(self):
        pass

    @abstractmethod
    def get_default_priority_score(self):
        pass

    def borrow(self):
        pass

    def return_device(self):
        pass


class ProjectorRemote(TeachingDevice):
    def __init__(self, device_id, name, storage_location, battery_level):
        super().__init__(device_id, name, storage_location)
        self.battery_level = battery_level

    def is_ready_for_use(self):
        pass

    def get_default_priority_score(self):
        pass


class AirConditionerRemote(TeachingDevice):
    def __init__(self, device_id, name, storage_location, compatible_rooms):
        super().__init__(device_id, name, storage_location)
        self.compatible_rooms = compatible_rooms

    def is_compatible_with(self, room_id):
        pass

    def is_ready_for_use(self):
        pass

    def get_default_priority_score(self):
        pass


class WirelessMicrophone(TeachingDevice):
    def __init__(self, device_id, name, storage_location, battery_level, signal_quality):
        super().__init__(device_id, name, storage_location)
        self.battery_level = battery_level
        self.signal_quality = signal_quality

    def is_ready_for_use(self):
        pass

    def get_default_priority_score(self):
        pass


# ---- kho lưu trữ generic ----
T = TypeVar("T")
TId = TypeVar("TId", bound=IIdentifiable)
TDevice = TypeVar("TDevice", bound=TeachingDevice)


class IRepository(ABC, Generic[TId]):
    @abstractmethod
    def add(self, item):
        pass

    @abstractmethod
    def remove(self, item_id):
        pass

    @abstractmethod
    def find_by_id(self, item_id):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def find_all(self, condition):
        pass


class InMemoryRepository(IRepository[TId]):
    def __init__(self):
        self._items = []

    def add(self, item):
        pass

    def remove(self, item_id):
        pass

    def find_by_id(self, item_id):
        pass

    def get_all(self):
        pass

    def find_all(self, condition):
        pass


# ---- chiến lược chọn ----
class ISelectionStrategy(ABC, Generic[T]):
    @abstractmethod
    def select(self, candidates):
        pass


class HighestPriorityStrategy(ISelectionStrategy[T]):
    def __init__(self, score_selector: Callable[[T], float]):
        self._score_selector = score_selector

    def select(self, candidates):
        pass


class FirstAvailableStrategy(ISelectionStrategy[T]):
    def select(self, candidates):
        pass


# ---- dịch vụ cấp phát ----
class AllocationService(Generic[TDevice]):
    def __init__(self, repository, strategy):
        self._repository = repository
        self._strategy = strategy

    def change_strategy(self, new_strategy):
        pass

    def allocate(self, additional_condition=None):
        pass


def main():
    pass


if __name__ == "__main__":
    main()
