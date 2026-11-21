

from uuid import uuid4

from app.incidents.service import IncidentService


def test_restore_from_db() -> None:
    from unittest.mock import MagicMock

    db = MagicMock()
    db.list_open_incidents.return_value = [
        {
            "id": str(uuid4()),
            "service_name": "yuki-core-api",
            "status": "open",
            "severity": "P1",
            "error_message": "still down",
        }
    ]
    svc = IncidentService(db=db)
    assert svc.restore_from_db() == 1
    assert len(svc.list_all()) == 1
    assert svc.list_all()[0].service == "yuki-core-api"


def test_restore_without_db() -> None:
    assert IncidentService().restore_from_db() == 0
