from rimpack.types import ModReference


class RimworldConfigParseError(ValueError):
    pass


class ModListError(ValueError): ...


class ModListPackDoesNotExistError(ModListError):
    def __init__(self, pack: str) -> None:
        super().__init__(f"Mod list pack does not exist: {pack}")


class ModListPackAlreadyExistsError(ModListError):
    def __init__(self, pack: str) -> None:
        super().__init__(f"Mod list pack already exists: {pack}")


class ModListModAlreadyExistsError(ModListError):
    def __init__(self, reference: ModReference) -> None:
        super().__init__(
            f"Mod already exists: {reference.kind}:{reference.reference}"
        )


class ModListModDoesNotExistError(ModListError):
    def __init__(self, reference: ModReference) -> None:
        super().__init__(
            f"Mod does not exist: {reference.kind}:{reference.reference}"
        )


class AboutXmlError(ValueError):
    """Raised when About.xml does not match the expected structure."""


class ModFolderError(ValueError):
    """Raised when a mod folder does not contain the expected files."""


class SteamworksError(RuntimeError):
    """Base error for Steamworks integration failures."""


class SteamworksUnavailableError(SteamworksError):
    """Raised when the Steamworks client cannot be loaded or initialized."""


class SteamworksSubscriptionError(SteamworksError):
    """Raised when Steamworks rejects a workshop subscription request."""


class SteamworksResolutionError(SteamworksError):
    """Raised when a workshop item cannot be resolved into a local mod folder."""


class CycleError(ValueError):
    """Raised when the dependency graph contains a cycle."""
