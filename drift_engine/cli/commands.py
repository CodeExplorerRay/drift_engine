from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from config.settings import get_settings
from drift_engine.api.dependencies import get_engine
from drift_engine.collectors.base import CollectionContext
from drift_engine.core.models import Baseline

app = typer.Typer(help="System Drift Engine CLI")
console = Console()


@app.command()
def serve(
    host: Annotated[str | None, typer.Option(help="Bind host.")] = None,
    port: Annotated[int | None, typer.Option(help="Bind port.")] = None,
    reload: Annotated[bool, typer.Option(help="Enable auto-reload for development.")] = False,
) -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "drift_engine.api.app:create_app",
        factory=True,
        host=host or settings.host,
        port=port or settings.port,
        reload=reload,
    )


@app.command("collect")
def collect(
    collectors: Annotated[list[str] | None, typer.Option("--collector", "-c")] = None,
    scope_file: Annotated[Path | None, typer.Option(help="JSON scope file.")] = None,
) -> None:
    scope = _load_json(scope_file) if scope_file else {}
    snapshot, results = asyncio.run(
        get_engine().collect_state(
            collector_names=collectors,
            context=CollectionContext(scope=scope),
        )
    )
    console.print_json(data=snapshot.to_document())
    _print_collectors(results)


@app.command("create-baseline")
def create_baseline(
    name: Annotated[str, typer.Argument(help="Baseline name.")],
    resources_file: Annotated[Path, typer.Argument(help="JSON file keyed by resource identity.")],
    version: Annotated[str, typer.Option()] = "1.0.0",
) -> None:
    resources = _load_json(resources_file)
    engine = get_engine()
    baseline = engine.baseline_manager.create(name=name, resources=resources, version=version)
    asyncio.run(engine.baselines.save(baseline))
    console.print_json(data=baseline.to_document())


@app.command("scan")
def scan(
    baseline_file: Annotated[Path, typer.Argument(help="Baseline JSON document.")],
    collectors: Annotated[list[str] | None, typer.Option("--collector", "-c")] = None,
    scope_file: Annotated[Path | None, typer.Option(help="JSON scope file.")] = None,
) -> None:
    engine = get_engine()
    baseline = Baseline.from_document(_load_json(baseline_file))
    asyncio.run(engine.baselines.save(baseline))
    scope = _load_json(scope_file) if scope_file else {}
    result = asyncio.run(
        engine.run_once(
            baseline_id=baseline.id,
            collector_names=collectors,
            context=CollectionContext(scope=scope),
        )
    )
    console.print_json(data=result.report.to_document())


@app.command("collectors")
def list_collectors() -> None:
    engine = get_engine()
    table = Table("Name", "Resource Type", "Enabled")
    for name in engine.collectors.names():
        collector = engine.collectors.get(name)
        table.add_row(name, collector.resource_type, str(collector.config.enabled))
    console.print(table)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise typer.BadParameter("JSON document must be an object")
    return payload


def _print_collectors(results: list[Any]) -> None:
    table = Table("Collector", "Status", "Duration ms", "Errors")
    for result in results:
        table.add_row(
            result.collector_name,
            result.status.value,
            str(result.duration_ms),
            "; ".join(result.errors),
        )
    console.print(table)
