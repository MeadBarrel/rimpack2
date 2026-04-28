from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Collection, Hashable, Iterable
from dataclasses import dataclass, field
from heapq import heappop, heappush

from rimpack.core.exceptions import CycleError as CycleError
from rimpack.core.mod.about import AboutModMetadata
from rimpack.tools import normalize_rimworld_version


@dataclass(frozen=True)
class ToposortItem[T: Hashable]:
    item: T
    before: Collection[T] = field(default_factory=tuple)
    after: Collection[T] = field(default_factory=tuple)


def mod_to_sort_item(
    about: AboutModMetadata, rimworld_version: str
) -> ToposortItem[str]:
    version = normalize_rimworld_version(rimworld_version)
    package_id = about.package_id
    before: set[str] = set()
    after: set[str] = set()
    for item in about.mod_dependencies:
        after.add(item.package_id)
    for item in about.mod_dependencies_by_version:
        if normalize_rimworld_version(item.version) != version:
            continue
        for sub_item in item.dependencies:
            after.add(sub_item.package_id)
    before |= set(about.load_before)
    for item in about.load_before_by_version:
        if normalize_rimworld_version(item.version) != version:
            continue
        before |= set(item.package_ids)
    before |= set(about.force_load_before)
    after |= set(about.load_after)
    for item in about.load_after_by_version:
        if normalize_rimworld_version(item.version) != version:
            continue
        after |= set(item.package_ids)
    after |= set(about.force_load_after)
    return ToposortItem(
        package_id,
        before=before,
        after=after,
    )


def sort_package_ids(items: Collection[ToposortItem[str]]) -> list[str]:
    package_ids = [item.item for item in items]
    lowercase_items = [
        ToposortItem(
            item.item.lower(),
            before=[x.lower() for x in item.before],
            after=[x.lower() for x in item.after],
        )
        for item in items
    ]
    ordered = stable_toposort(lowercase_items)
    return restore_original_order(package_ids, ordered)


def restore_original_order(
    original: Iterable[str],
    shuffled_lower: Iterable[str],
) -> list[str]:
    """
    Reorder `original` to match the order of `shuffled_lower`,
    where matching is done via `.lower()`.

    Handles duplicates correctly.
    """
    buckets: dict[str, deque[str]] = defaultdict(deque)

    for s in original:
        buckets[s.lower()].append(s)

    result: list[str] = []

    for key in shuffled_lower:
        try:
            result.append(buckets[key].popleft())
        except (KeyError, IndexError):
            raise ValueError(f"No available original string for {key!r}")

    return result


def stable_toposort[T: Hashable](
    items: Collection[ToposortItem[T]],
) -> list[T]:
    """
    Topologically sort items while preserving original order as much as possible.

    Missing references in `before` and `after` are ignored.

    Semantics:
    - if X.before contains Y, then X must come before Y
    - if X.after contains Y, then X must come after Y
    """
    items_list = list(items)
    nodes = [entry.item for entry in items_list]
    index = {node: i for i, node in enumerate(nodes)}

    if len(index) != len(nodes):
        raise ValueError("Input contains duplicate items.")

    deps_by_node: dict[T, set[T]] = {node: set() for node in nodes}
    dependents_by_node: dict[T, list[T]] = defaultdict(list)

    for entry in items_list:
        node = entry.item

        for dep in entry.after:
            if dep == node:
                raise CycleError(f"Self-cycle detected at {node!r}")
            if dep not in index:
                continue
            deps_by_node[node].add(dep)

        for dependent in entry.before:
            if dependent == node:
                raise CycleError(f"Self-cycle detected at {node!r}")
            if dependent not in index:
                continue
            deps_by_node[dependent].add(node)

    indegree: dict[T, int] = {}
    for node, deps in deps_by_node.items():
        indegree[node] = len(deps)
        for dep in deps:
            dependents_by_node[dep].append(node)

    # Priority is based on the earliest original position of this node
    # or of any node it directly helps unblock.
    priority: dict[T, int] = {}
    for node in nodes:
        p = index[node]
        for dependent in dependents_by_node[node]:
            p = min(p, index[dependent])
        priority[node] = p

    ready: list[tuple[int, int, T]] = []
    for node in nodes:
        if indegree[node] == 0:
            heappush(ready, (priority[node], index[node], node))

    result: list[T] = []

    while ready:
        _, _, node = heappop(ready)
        result.append(node)

        for dependent in dependents_by_node[node]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heappush(ready, (priority[dependent], index[dependent], dependent))

    if len(result) != len(nodes):
        remaining = [node for node in nodes if indegree[node] > 0]
        raise CycleError(f"Cycle detected involving: {remaining!r}")

    return result
