from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

IntegrationStatus = Literal["ready", "disabled", "missing_dependency", "needs_configuration"]


@dataclass(slots=True)
class IntegrationDescriptor:
    """Describes an external system that can feed state into the drift engine."""

    name: str
    display_name: str
    collector_name: str
    description: str
    enabled: bool
    status: IntegrationStatus
    resource_types: list[str]
    optional_dependencies: list[str] = field(default_factory=list)
    required_configuration: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    setup_hint: str = ""

    def to_document(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "collector_name": self.collector_name,
            "description": self.description,
            "enabled": self.enabled,
            "status": self.status,
            "resource_types": self.resource_types,
            "optional_dependencies": self.optional_dependencies,
            "required_configuration": self.required_configuration,
            "missing": self.missing,
            "settings": self.settings,
            "setup_hint": self.setup_hint,
        }
