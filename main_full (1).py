#***************************************************
# MSSV: 202418977
# Họ và tên: Đào Quý Sang
#***************************************************
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Generic, Optional, Sequence, TypeVar


class DeviceStatus(Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"


class DuplicateIdException(Exception):
    def __init__(self, duplicate_id):
        super().__init__(f"Mã {duplicate_id} đã có trong kho")  # ( )
        self.duplicate_id = duplicate_id


class NoSuitableItemException(Exception):
    def __init__(self, message="Không có thiết bị phù hợp"):  # ( )
        super().__init__(message)


class DeviceNotReadyException(Exception):
    def __init__(self, device_id, current_status):
        super().__init__(f"Thiết bị {device_id} chưa sẵn sàng ({current_status.value})")  # ( )
        self.device_id = device_id
        self.current_status = current_status


class InvalidReturnException(Exception):
    # Note: ngoại lệ bổ sung. Lý do: đề yêu cầu Return() chỉ thành công khi đang Borrowed
    # nhưng không có lớp ngoại lệ cho lỗi này; DeviceNotReady mang nghĩa "chưa sẵn sàng để mượn".
    def __init__(self, device_id, current_status):
        super().__init__(f"Thiết bị {device_id} không ở trạng thái Borrowed ({current_status.value})")  # ( )
        self.device_id = device_id
        self.current_status = current_status


class IIdentifiable(ABC):
    @property
    @abstractmethod
    def id(self): ...


def _check_percent(value, name):
    if not 0 <= value <= 100:
        raise ValueError(f"{name} phải trong khoảng 0..100")


class TeachingDevice(IIdentifiable):
    def __init__(self, device_id, name, storage_location):
        if not device_id or not device_id.strip():
            raise ValueError("Mã thiết bị không được rỗng")
        if not name or not name.strip():
            raise ValueError("Tên thiết bị không được rỗng")
        if not storage_location or not storage_location.strip():
            raise ValueError("Vị trí lưu trữ không được rỗng")
        self._id = device_id.strip()
        self.name = name.strip()
        self.storage_location = storage_location.strip()
        self._status = DeviceStatus.AVAILABLE  

    @property
    def id(self):
        return self._id

    @property
    def status(self): 
        return self._status

    @abstractmethod
    def is_ready_for_use(self): ...

    @abstractmethod
    def get_default_priority_score(self): ...

    def borrow(self):
        if not self.is_ready_for_use():
            raise DeviceNotReadyException(self.id, self._status)
        self._status = DeviceStatus.BORROWED

    def return_device(self): 
        if self._status != DeviceStatus.BORROWED:
            raise InvalidReturnException(self.id, self._status)
        self._status = DeviceStatus.AVAILABLE

    def send_to_maintenance(self):
        if self._status == DeviceStatus.BORROWED:
            raise InvalidReturnException(self.id, self._status)
        self._status = DeviceStatus.UNDER_MAINTENANCE

    def _is_available(self):
        return self._status == DeviceStatus.AVAILABLE

    def __str__(self):
        return f"{type(self).__name__} {self.id} [{self._status.value}]"


class ProjectorRemote(TeachingDevice):
    MIN_BATTERY = 20  # ( )

    def __init__(self, device_id, name, storage_location, battery_level):
        super().__init__(device_id, name, storage_location)
        _check_percent(battery_level, "Mức pin")
        self.battery_level = battery_level

    def is_ready_for_use(self):
        return self._is_available() and self.battery_level >= self.MIN_BATTERY

    def get_default_priority_score(self):
        return self.battery_level


class AirConditionerRemote(TeachingDevice):
    def __init__(self, device_id, name, storage_location, compatible_rooms):
        super().__init__(device_id, name, storage_location)
        self.compatible_rooms = frozenset(compatible_rooms) 
    def is_compatible_with(self, room_id):
        return room_id in self.compatible_rooms

    def is_ready_for_use(self):
        return self._is_available()

    def get_default_priority_score(self):
        return 100 if self.compatible_rooms else 0

    def score_for_room(self, room_id):
        return 100 if self.is_compatible_with(room_id) else 0


class WirelessMicrophone(TeachingDevice):
    MIN_BATTERY = 30  # ( )
    MIN_SIGNAL = 40   # ( )

    def __init__(self, device_id, name, storage_location, battery_level, signal_quality):
        super().__init__(device_id, name, storage_location)
        _check_percent(battery_level, "Mức pin")
        _check_percent(signal_quality, "Chất lượng tín hiệu")
        self.battery_level = battery_level
        self.signal_quality = signal_quality

    def is_ready_for_use(self):
        return (self._is_available() and self.battery_level >= self.MIN_BATTERY
                and self.signal_quality >= self.MIN_SIGNAL)

    def get_default_priority_score(self):
        return (self.battery_level + self.signal_quality) / 2


T = TypeVar("T")
TId = TypeVar("TId", bound=IIdentifiable)
TDevice = TypeVar("TDevice", bound=TeachingDevice)


class IRepository(ABC, Generic[TId]):
    @abstractmethod
    def add(self, item): ...

    @abstractmethod
    def remove(self, item_id): ...

    @abstractmethod
    def find_by_id(self, item_id): ...

    @abstractmethod
    def get_all(self): ...

    @abstractmethod
    def find_all(self, condition): ...


class InMemoryRepository(IRepository[TId]):
    def __init__(self):
        self._items = {}

    def add(self, item):
        if not isinstance(item, IIdentifiable):  
            raise TypeError("Chỉ nhận đối tượng IIdentifiable")
        if item.id in self._items:
            raise DuplicateIdException(item.id)
        self._items[item.id] = item

    def remove(self, item_id):
        return self._items.pop(item_id, None) is not None

    def find_by_id(self, item_id):
        return self._items.get(item_id)

    def get_all(self):
        return tuple(self._items.values()) 

    def find_all(self, condition):
        return tuple(i for i in self._items.values() if condition(i))


class ISelectionStrategy(ABC, Generic[T]):
    @abstractmethod
    def select(self, candidates): ...


class HighestPriorityStrategy(ISelectionStrategy[T]):
    def __init__(self, score_selector: Callable[[T], float]):
        self._score_selector = score_selector  

    def select(self, candidates):
        if not candidates:
            raise NoSuitableItemException()
        return max(candidates, key=self._score_selector)  


class FirstAvailableStrategy(ISelectionStrategy[T]):
    def select(self, candidates):
        if not candidates:
            raise NoSuitableItemException()
        return candidates[0]


class FunctionStrategy(ISelectionStrategy[T]):
    def __init__(self, chooser: Callable[[Sequence[T]], T]):
        self._chooser = chooser

    def select(self, candidates):
        if not candidates:
            raise NoSuitableItemException()
        return self._chooser(candidates)


class AllocationService(Generic[TDevice]):
    def __init__(self, repository, strategy):
        if repository is None or strategy is None:
            raise ValueError("Repository và strategy không được None")
        self._repository = repository
        self._strategy = strategy

    def change_strategy(self, new_strategy):
        if new_strategy is None:
            raise ValueError("Strategy không được None")
        self._strategy = new_strategy

    def allocate(self, additional_condition=None):
        candidates = self._repository.find_all(
            lambda d: d.is_ready_for_use() and (additional_condition is None or additional_condition(d)))
        chosen = self._strategy.select(candidates)
        chosen.borrow() 
        return chosen

    def release(self, device_id):
        device = self._repository.find_by_id(device_id)
        if device is None:
            raise NoSuitableItemException(f"Không tìm thấy thiết bị {device_id}")  # ( )
        device.return_device()
        return device


def thu(nhan, ham, *tham_so):
    """Chạy một tình huống có thể lỗi, in kết quả."""
    try:
        kq = ham(*tham_so)
        print(f"{nhan}: {kq}")
    except (DuplicateIdException, NoSuitableItemException, DeviceNotReadyException,
            InvalidReturnException, ValueError, TypeError) as e:
        print(f"{nhan}: {type(e).__name__} - {e}")


def ids(danh_sach):
    return [d.id for d in danh_sach]


def main():
    proj = [ProjectorRemote("PJ01", "ĐK máy chiếu Epson", "Kho A", 90),
            ProjectorRemote("PJ02", "ĐK máy chiếu Sony", "Kho A", 15),   
            ProjectorRemote("PJ03", "ĐK máy chiếu BenQ", "Kho A", 60)]
    acs = [AirConditionerRemote("AC01", "ĐK điều hòa Daikin", "Kho B", {"A101", "A203"}),
           AirConditionerRemote("AC02", "ĐK điều hòa LG", "Kho B", {"B105"})]
    mics = [WirelessMicrophone("MIC01", "Micro Shure", "Kho C", 25, 90),  # pin yếu
            WirelessMicrophone("MIC02", "Micro Sennheiser", "Kho C", 50, 45),
            WirelessMicrophone("MIC03", "Micro Rode", "Kho C", 90, 95)]

    print("== 1. Thêm vào kho (cùng một lớp InMemoryRepository cho 3 loại) ==")
    proj_repo = InMemoryRepository[ProjectorRemote]()
    ac_repo = InMemoryRepository[AirConditionerRemote]()
    mic_repo = InMemoryRepository[WirelessMicrophone]()
    for repo, items in ((proj_repo, proj), (ac_repo, acs), (mic_repo, mics)):
        for d in items:
            repo.add(d)
    print("Máy chiếu:", ids(proj_repo.get_all()), "| Điều hòa:", ids(ac_repo.get_all()),
          "| Micro:", ids(mic_repo.get_all()))

    print("\n== 2. Thêm trùng mã ==")
    thu("Thêm PJ01 lần 2", proj_repo.add, ProjectorRemote("PJ01", "Bản sao", "Kho A", 50))
    thu("Thêm None", proj_repo.add, None)

    print("\n== 3. Tìm theo mã ==")
    thu("Tìm PJ03", lambda: proj_repo.find_by_id("PJ03"))
    thu("Tìm PJ99", lambda: proj_repo.find_by_id("PJ99"))

    print("\n== 4. Lọc thiết bị sẵn sàng ==")
    print("Máy chiếu sẵn sàng:", ids(proj_repo.find_all(lambda d: d.is_ready_for_use())))
    print("Micro sẵn sàng:", ids(mic_repo.find_all(lambda d: d.is_ready_for_use())))

    print("\n== 5. Máy chiếu điểm cao nhất ==")
    proj_service = AllocationService(proj_repo, HighestPriorityStrategy(lambda d: d.get_default_priority_score()))
    thu("Cấp phát", lambda: proj_service.allocate(lambda d: True))

    print("\n== 6. Điều hòa tương thích phòng A203 ==")
    ac_service = AllocationService(ac_repo, HighestPriorityStrategy(lambda d: d.score_for_room("A203")))
    thu("Cấp phát", lambda: ac_service.allocate(lambda d: d.is_compatible_with("A203")))

    print("\n== 7. Micro đầu tiên sẵn sàng ==")
    mic_service = AllocationService(mic_repo, FirstAvailableStrategy())
    thu("Cấp phát", mic_service.allocate)

    print("\n== 8. Đổi chiến lược lúc chạy ==")
    thu("Trả MIC02", lambda: mic_service.release("MIC02"))
    thu("FirstAvailable ", mic_service.allocate)  
    mic_service.release("MIC02")
    mic_service.change_strategy(HighestPriorityStrategy(lambda d: d.get_default_priority_score()))
    thu("HighestPriority", mic_service.allocate)   
    mic_service.change_strategy(FunctionStrategy(lambda c: min(c, key=lambda d: d.battery_level)))
    thu("Pin thấp nhất  ", mic_service.allocate)   

    print("\n== 9. Không có ứng viên phù hợp ==")
    thu("Phòng Z999", lambda: ac_service.allocate(lambda d: d.is_compatible_with("Z999")))
    thu("Hết máy chiếu", lambda: [proj_service.allocate(), proj_service.allocate()])

    print("\n== 10. Thiết bị được chọn chuyển sang Borrowed ==")
    print("Trạng thái PJ01:", proj_repo.find_by_id("PJ01").status.value)
    print("Trạng thái PJ03:", proj_repo.find_by_id("PJ03").status.value)
    thu("Mượn lại PJ01", proj_repo.find_by_id("PJ01").borrow)
    thu("Trả PJ01", lambda: proj_service.release("PJ01"))
    thu("Trả PJ01 lần 2", lambda: proj_service.release("PJ01"))

    print("\n== 11. Một kho generic cho nhiều loại thiết bị ==")
    print("Cùng lớp:", type(proj_repo) is type(ac_repo) is type(mic_repo), "->", type(proj_repo).__name__)
    print("Kiểu phần tử:", type(proj_repo.get_all()[0]).__name__, type(ac_repo.get_all()[0]).__name__,
          type(mic_repo.get_all()[0]).__name__)

    print("\n== Dữ liệu sai ở constructor ==")
    thu("Pin 120", ProjectorRemote, "PJ09", "x", "Kho", 120)
    thu("Mã rỗng", WirelessMicrophone, " ", "x", "Kho", 50, 50)


if __name__ == "__main__":
    main()
