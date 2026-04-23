from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
from importlib import import_module
import logging
import os
from pathlib import Path
import sys
import time
from types import ModuleType
from typing import Protocol, cast, final
from urllib.parse import parse_qs, urlparse

from rimpack.constants import RIMWORLD_STEAM_APP_ID
from rimpack.core.mod.modfolder import ModFolder, load_mod_folder

type SteamworksOperation = Callable[[int], object]
type SteamworksFactory = Callable[[], object]
type SteamworksInitializer = Callable[[], object]

WORKSHOP_RESOLVE_TIMEOUT_SECONDS = 60.0
WORKSHOP_RESOLVE_POLL_INTERVAL_SECONDS = 0.5
logger = logging.getLogger(__name__)


class _Closable(Protocol):
    def close(self) -> None: ...


class SteamworksError(RuntimeError):
    """Base error for Steamworks integration failures."""


class SteamworksUnavailableError(SteamworksError):
    """Raised when the Steamworks client cannot be loaded or initialized."""


class SteamworksSubscriptionError(SteamworksError):
    """Raised when Steamworks rejects a workshop subscription request."""


class SteamworksResolutionError(SteamworksError):
    """Raised when a workshop item cannot be resolved into a local mod folder."""


@final
class Steamworks:
    def __init__(self) -> None:
        self._client = _create_steamworks_client()

    def subscribe(self, workshop_id: str | int):
        logging.getLogger(__name__).debug("Subscribing to %s", workshop_id)
        return _subscribe_to_workshop_item(workshop_id, self._client)

    def unsubscribe(self, workshop_id: str | int):
        logging.getLogger(__name__).debug("Unsubscribing from %s", workshop_id)
        return _unsubscribe_from_workshop_item(workshop_id, self._client)


def resolve_rimworld_workshop_mod_by_id(
    steamworks: Steamworks,
    workshop_root: Path,
    workshop_id: str | int,
    unsubscribe: bool = False,
) -> ModFolder:
    workshop_id = coerce_workshop_item_id(workshop_id)
    mod_path = workshop_root / str(workshop_id)
    pre_existing = _try_load_workshop_mod(mod_path)
    if pre_existing:
        return pre_existing
    _ = steamworks.subscribe(workshop_id)
    logging.getLogger(__name__).info("Waiting for a mod in %s", mod_path)
    result = _wait_for_workshop_mod(mod_path)
    if result is None:
        raise SteamworksError(f"Deadline expired while waiting for data in {mod_path}")
    if unsubscribe and not pre_existing:
        steamworks.unsubscribe(workshop_id)
    return result


def is_steamworks_available() -> bool:
    """Return whether the Steamworks Python module can be imported."""
    try:
        _ = _load_steamworks_module()
    except SteamworksUnavailableError:
        return False
    return True


def _create_steamworks_client() -> object:
    """Create and initialize a Steamworks client."""
    logger.info("Initializing Steamworks client")
    with ExitStack() as exit_stack:
        module = _load_steamworks_module()
        _prepare_steamworks_runtime(exit_stack, module)
        factory = _get_required_callable(
            module,
            ("STEAMWORKS",),
            error_message="steamworks.STEAMWORKS is not available",
            callable_type="factory",
        )
        client = factory()
        initializer = _get_required_callable(
            client,
            ("initialize", "Initialize"),
            error_message="Steamworks client does not expose an initialize method",
            callable_type="initializer",
        )
        initialized = initializer()
        if initialized is False:
            raise SteamworksUnavailableError("Steamworks client initialization failed")
        logger.info("Steamworks client initialized")
        return client


def _subscribe_to_workshop_item(
    workshop_id: int | str, steamworks_client: object | None = None
) -> None:
    """Request a Steam Workshop subscription for the given published file ID."""
    published_file_id = _coerce_workshop_item_id(workshop_id)
    logger.info("Subscribing to workshop item %s", published_file_id)
    client = (
        steamworks_client
        if steamworks_client is not None
        else _create_steamworks_client()
    )
    operation = _get_workshop_operation(
        client,
        "SubscribeItem",
        "subscribe_item",
        direct_method_names=("Workshop_SubscribeItem",),
    )
    result = operation(published_file_id)
    if result is False:
        raise SteamworksSubscriptionError(
            f"Steamworks refused to subscribe to workshop item {published_file_id}"
        )
    logger.info("Subscribed to workshop item %s", published_file_id)


def _unsubscribe_from_workshop_item(
    workshop_id: int | str,
    steamworks_client: object | None = None,
) -> None:
    """Request a Steam Workshop unsubscription for the given published file ID."""
    published_file_id = _coerce_workshop_item_id(workshop_id)
    logger.info("Unsubscribing from workshop item %s", published_file_id)
    client = (
        steamworks_client
        if steamworks_client is not None
        else _create_steamworks_client()
    )
    operation = _get_workshop_operation(
        client,
        "UnsubscribeItem",
        "unsubscribe_item",
        direct_method_names=("Workshop_UnsubscribeItem",),
    )
    result = operation(published_file_id)
    if result is False:
        raise SteamworksSubscriptionError(
            f"Steamworks refused to unsubscribe from workshop item {published_file_id}"
        )
    logger.info("Unsubscribed from workshop item %s", published_file_id)


def _load_steamworks_module() -> ModuleType:
    try:
        return import_module("steamworks")
    except ModuleNotFoundError:
        pass

    steamworkspy_root = _load_steamworkspy_package()
    if steamworkspy_root is None:
        raise SteamworksUnavailableError(
            "steamworks package is not installed; install it before using Steam Workshop actions"
        )

    try:
        _ = _install_steamworks_package_shim(steamworkspy_root)
        return import_module("steamworks.steamworks")
    except (ImportError, ModuleNotFoundError) as exc:
        raise SteamworksUnavailableError(
            "steamworks package is not installed; install it before using Steam Workshop actions"
        ) from exc


def _load_steamworkspy_package() -> ModuleType | None:
    try:
        return import_module("steamworkspy")
    except ModuleNotFoundError:
        return None


def _install_steamworks_package_shim(steamworkspy_root: ModuleType) -> ModuleType:
    existing_module = sys.modules.get("steamworks")
    if isinstance(existing_module, ModuleType):
        return existing_module

    module_file = getattr(steamworkspy_root, "__file__", None)
    if not isinstance(module_file, str):
        raise SteamworksUnavailableError("steamworkspy package path is unavailable")

    package_root = Path(module_file).resolve().parent
    shim_module = ModuleType("steamworks")
    shim_module.__file__ = str(package_root / "__init__.py")
    shim_module.__package__ = "steamworks"
    shim_module.__path__ = [str(package_root)]  # type: ignore[attr-defined]
    sys.modules["steamworks"] = shim_module
    return shim_module


def _prepare_steamworks_runtime(exit_stack: ExitStack, module: ModuleType) -> None:
    module_root = _get_steamworks_module_root(module)
    _ensure_windows_dll_directory(exit_stack, module_root)
    _ensure_required_native_files(module_root)
    _ensure_steam_appid_file(exit_stack)


def _get_steamworks_module_root(module: ModuleType) -> Path:
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str):
        raise SteamworksUnavailableError("Steamworks module path is unavailable")
    return Path(module_file).resolve().parent.parent


def _ensure_windows_dll_directory(exit_stack: ExitStack, module_root: Path) -> None:
    if sys.platform != "win32":
        return

    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory is None:
        return

    dll_handle = cast(_Closable | object, add_dll_directory(str(module_root)))
    close = getattr(dll_handle, "close", None)
    if callable(close):
        _ = exit_stack.callback(close)


def _ensure_required_native_files(module_root: Path) -> None:
    if sys.platform == "win32":
        required_files = ("SteamworksPy64.dll", "steam_api64.dll")
    else:
        required_files = ()

    missing_files = [
        file_name
        for file_name in required_files
        if not (module_root / file_name).is_file()
    ]
    if missing_files:
        missing_text = ", ".join(missing_files)
        raise SteamworksUnavailableError(
            (
                "Steamworks native libraries are missing from the installed package: "
                f"{missing_text}"
            )
        )


def _ensure_steam_appid_file(exit_stack: ExitStack) -> None:
    app_id_path = Path.cwd() / "steam_appid.txt"
    if app_id_path.is_file():
        return

    _ = app_id_path.write_text(f"{RIMWORLD_STEAM_APP_ID}\n", encoding="utf-8")
    _ = exit_stack.callback(app_id_path.unlink, missing_ok=True)


def _coerce_workshop_item_id(workshop_id: int | str) -> int:
    if isinstance(workshop_id, int):
        if workshop_id <= 0:
            raise ValueError("workshop_id must be a positive integer")
        return workshop_id

    normalized_id = _normalize_workshop_item_id_text(workshop_id)
    if not normalized_id or not normalized_id.isdigit():
        raise ValueError("workshop_id must be a positive integer")

    parsed_id = int(normalized_id)
    if parsed_id <= 0:
        raise ValueError("workshop_id must be a positive integer")
    return parsed_id


def coerce_workshop_item_id(workshop_id: int | str) -> int:
    """Normalize a workshop ID or supported sharedfiles URL into a published file ID."""
    return _coerce_workshop_item_id(workshop_id)


def _normalize_workshop_item_id_text(workshop_id: str) -> str:
    normalized_id = workshop_id.strip()
    parsed_url = urlparse(normalized_id)
    if (
        parsed_url.scheme in {"http", "https"}
        and parsed_url.netloc in {"steamcommunity.com", "www.steamcommunity.com"}
        and parsed_url.path.rstrip("/") == "/sharedfiles/filedetails"
    ):
        id_values = parse_qs(parsed_url.query).get("id")
        if id_values:
            return id_values[0].strip()
    return normalized_id


def _get_workshop_operation(
    steamworks_client: object,
    method_name: str,
    fallback_method_name: str,
    *,
    direct_method_names: tuple[str, ...] = (),
) -> SteamworksOperation:
    direct_operation = _get_optional_callable(steamworks_client, *direct_method_names)
    if direct_operation is not None:
        return direct_operation

    workshop = _get_optional_attribute(steamworks_client, "Workshop")
    for target in (workshop, steamworks_client):
        if target is None:
            continue
        operation = _get_optional_callable(target, method_name, fallback_method_name)
        if operation is not None:
            return operation
    raise SteamworksUnavailableError(
        f"Steamworks client does not expose a workshop method for {method_name}"
    )


def _get_required_callable(
    value: object,
    attribute_names: tuple[str, ...],
    *,
    error_message: str,
    callable_type: str,
) -> SteamworksFactory | SteamworksInitializer:
    operation = _get_optional_callable(value, *attribute_names)
    if operation is None:
        raise SteamworksUnavailableError(error_message)
    if callable_type == "factory":
        return cast(SteamworksFactory, operation)
    return cast(SteamworksInitializer, operation)


def _get_optional_callable(
    value: object, *attribute_names: str
) -> SteamworksOperation | None:
    for attribute_name in attribute_names:
        candidate = _get_optional_attribute(value, attribute_name)
        if candidate is None or not callable(candidate):
            continue
        return cast(SteamworksOperation, candidate)
    return None


def _get_optional_attribute(value: object, attribute_name: str) -> object | None:
    try:
        return cast(object, getattr(value, attribute_name))
    except AttributeError:
        return None


def _wait_for_workshop_mod(
    mod_path: Path,
) -> ModFolder | None:
    logger.debug("Waiting for workshop mod at %s", mod_path)
    deadline = time.monotonic() + WORKSHOP_RESOLVE_TIMEOUT_SECONDS
    while True:
        mod = _try_load_workshop_mod(mod_path)
        if mod is not None:
            return mod
        if time.monotonic() >= deadline:
            return None
        time.sleep(WORKSHOP_RESOLVE_POLL_INTERVAL_SECONDS)


def _try_load_workshop_mod(mod_path: Path) -> ModFolder | None:
    try:
        return load_mod_folder(mod_path)
    except Exception:
        return None
