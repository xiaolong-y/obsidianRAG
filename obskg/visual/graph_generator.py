"""Visual graph generation utilities.

This module provides classes to build D3.js compatible force‑directed
graphs from notes and their connections.  The ``KnowledgeGraphGenerator``
class accepts a list of notes and their relationships and returns a
dictionary representation that can be consumed by D3.js on the web.

This minimal implementation demonstrates the expected API but does not
compute complex layouts or physics; those are handled client‑side by
D3.js.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


class KnowledgeGraphGenerator:
    """Generate force‑directed graphs for knowledge visualization."""

    def generate(self, notes: Iterable[Dict[str, Any]], connections: Iterable[Tuple[str, str]]) -> Dict[str, Any]:
        """Generate a D3.js compatible graph structure.

        Parameters
        ----------
        notes : iterable of dict
            Each note must define at least an ``id`` and ``label`` field.
        connections : iterable of tuple(str, str)
            Each tuple represents a directed or undirected edge between
            two note IDs.

        Returns
        -------
        dict
            A dictionary with ``nodes`` and ``links`` keys.  Nodes
            preserve any extra fields from the input notes.  Links have
            ``source``, ``target``, ``value`` and ``type``.
        """
        node_list: List[Dict[str, Any]] = []
        for note in notes:
            node = {
                "id": note["id"],
                "label": note.get("label", note["id"]),
                "group": note.get("group", "default"),
                "size": note.get("size", 1.0),
                "color": note.get("color", "#cccccc"),
            }
            node_list.append(node)
        link_list: List[Dict[str, Any]] = []
        for source_id, target_id in connections:
            link_list.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "value": 1.0,
                    "type": "related",
                }
            )
        return {
            "nodes": node_list,
            "links": link_list,
            "metadata": {
                "layout": "force-directed",
                "physics": {"charge": -300, "linkDistance": 50},
            },
        }