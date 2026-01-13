import json
from pathlib import Path

from opengov_oscal_pycore.models import Catalog
from opengov_oscal_pycore.repo import OscalRepository


def test_roundtrip_workbench_catalog(tmp_path: Path):
    fixture = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))

    cat = Catalog.model_validate(data)

    repo = OscalRepository[Catalog](tmp_path)
    repo.save("roundtrip.json", cat)

    out = json.loads((tmp_path / "roundtrip.json").read_text(encoding="utf-8"))

    assert "groups" in out
    assert "metadata" in out

    # Ensure typical Workbench prop fields survive roundtrip
    gov01 = out["groups"][0]["controls"][0]
    assert any(p.get("name") == "legal" and "group" in p and "remarks" in p for p in gov01.get("props", []))
