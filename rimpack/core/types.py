from typing import Literal, Protocol

type ModReferenceKind = Literal["pid", "wid", "loc"]


class ModReference(Protocol):
    @property
    def kind(self) -> ModReferenceKind: ...

    @property
    def reference(self) -> str: ...


def references_match(reference: ModReference, other: ModReference) -> bool:
    return reference.kind == other.kind and reference.reference == other.reference
