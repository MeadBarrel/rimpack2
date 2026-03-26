from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Hashable
from dataclasses import dataclass, field
from heapq import heappop, heappush


class CycleError(ValueError):
    """Raised when the dependency graph contains a cycle."""


@dataclass(frozen=True)
class ToposortItem[T: Hashable]:
    item: T
    before: Collection[T] = field(default_factory=tuple)
    after: Collection[T] = field(default_factory=tuple)


def stable_toposort[T: Hashable](
    items: Collection[ToposortItem[T]],
) -> list[T]:
    """
    Topologically sort items while preserving original order as much as possible.

    Priority is based not only on an item's own original position, but also on
    the earliest original position of any item it directly helps unblock.

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
            if dep not in index:
                raise KeyError(f"{node!r} has unknown 'after' dependency {dep!r}")
            if dep == node:
                raise CycleError(f"Self-cycle detected at {node!r}")
            deps_by_node[node].add(dep)

        for dependent in entry.before:
            if dependent not in index:
                raise KeyError(f"{node!r} has unknown 'before' target {dependent!r}")
            if dependent == node:
                raise CycleError(f"Self-cycle detected at {node!r}")
            deps_by_node[dependent].add(node)

    indegree: dict[T, int] = {}
    for node, deps in deps_by_node.items():
        indegree[node] = len(deps)
        for dep in deps:
            dependents_by_node[dep].append(node)

    # A node's priority is the earliest original position it directly influences,
    # or its own position if that is earlier.
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
