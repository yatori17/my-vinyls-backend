from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

import app as app_module

# flask_openapi3 wraps each view function to parse body/query/path from the
# real request before calling it. `functools.wraps` is used internally, so
# `.__wrapped__` gives back the plain function we actually wrote - the one
# that just takes `body`/`query`/`path` as normal arguments. Falling back to
# the function itself keeps this working even if a given route isn't wrapped.
_home = getattr(app_module.home, "__wrapped__", app_module.home)
_get_vinyls = getattr(app_module.get_vinyls, "__wrapped__", app_module.get_vinyls)
_add_vinyl = getattr(app_module.add_vinyl, "__wrapped__", app_module.add_vinyl)
_get_vinyl = getattr(app_module.get_vinyl, "__wrapped__", app_module.get_vinyl)
_update_vinyl = getattr(app_module.update_vinyl, "__wrapped__", app_module.update_vinyl)
_delete_vinyl = getattr(app_module.delete_vinyl, "__wrapped__", app_module.delete_vinyl)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def mock_session(monkeypatch):
    """Replaces app.Session so Session() returns one controllable mock."""
    session_instance = MagicMock(name="session_instance")
    session_class = MagicMock(name="Session", return_value=session_instance)
    monkeypatch.setattr(app_module, "Session", session_class)
    return session_instance


@pytest.fixture
def mock_vinyl_class(monkeypatch):
    """Replaces app.Vinyl with a MagicMock class so we can inspect construction calls."""
    vinyl_class = MagicMock(name="Vinyl")
    monkeypatch.setattr(app_module, "Vinyl", vinyl_class)
    return vinyl_class


@pytest.fixture
def mock_presenters(monkeypatch):
    """Replaces app.present_vinyl / app.present_vinyls with inspectable stand-ins."""
    present_vinyl = MagicMock(name="present_vinyl", return_value={"presented": "one"})
    present_vinyls = MagicMock(name="present_vinyls", return_value={"presented": "many"})
    monkeypatch.setattr(app_module, "present_vinyl", present_vinyl)
    monkeypatch.setattr(app_module, "present_vinyls", present_vinyls)
    return present_vinyl, present_vinyls


# --------------------------------------------------------------------------
# home()
# --------------------------------------------------------------------------

def test_home_returns_welcome_message():
    # home() calls jsonify(...), which needs an active Flask app context.
    with app_module.app.app_context():
        response, status = _home()
        body = response.get_json()

    assert status == 200
    assert "Virtual Digging" in body["message"]


# --------------------------------------------------------------------------
# get_vinyls()
# --------------------------------------------------------------------------

def test_get_vinyls_empty(mock_session, mock_presenters):
    mock_session.query.return_value.all.return_value = []

    body, status = _get_vinyls()

    assert status == 200
    assert body == {"vinyls": []}
    mock_session.close.assert_called_once()


def test_get_vinyls_returns_presented_list(mock_session, mock_presenters):
    present_vinyl, present_vinyls = mock_presenters
    fake_vinyls = [MagicMock(), MagicMock()]
    mock_session.query.return_value.all.return_value = fake_vinyls

    body, status = _get_vinyls()

    assert status == 200
    present_vinyls.assert_called_once_with(fake_vinyls)
    assert body == {"presented": "many"}


def test_get_vinyls_exception_returns_400(mock_session, mock_presenters):
    mock_session.query.side_effect = Exception("db unreachable")

    body, status = _get_vinyls()

    assert status == 400
    assert "db unreachable" in body["mesg"]


# --------------------------------------------------------------------------
# add_vinyl(body)
# --------------------------------------------------------------------------

def make_vinyl_body(**overrides):
    defaults = dict(
        name="Nevermind",
        genre="Grunge",
        year=1991,
        artist="Nirvana",
        conservation_state="Good",
        photo_url="http://example.com/cover.jpg",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_add_vinyl_success(mock_session, mock_vinyl_class, mock_presenters):
    present_vinyl, _ = mock_presenters
    body = make_vinyl_body()

    result, status = _add_vinyl(body)

    mock_vinyl_class.assert_called_once_with(
        name="Nevermind",
        genre="Grunge",
        year=1991,
        artist="Nirvana",
        conservation_state="Good",
        photo_url="http://example.com/cover.jpg",
    )
    mock_session.add.assert_called_once_with(mock_vinyl_class.return_value)
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()
    present_vinyl.assert_called_once_with(mock_vinyl_class.return_value)
    assert status == 201
    assert result == {"presented": "one"}


def test_add_vinyl_integrity_error_returns_400(mock_session, mock_vinyl_class, mock_presenters):
    mock_session.commit.side_effect = IntegrityError("stmt", {}, Exception("duplicate"))

    body, status = _add_vinyl(make_vinyl_body())

    assert status == 400
    assert body == {"mesg": "Database integrity error."}
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


def test_add_vinyl_generic_exception_returns_400(mock_session, mock_vinyl_class, mock_presenters):
    mock_session.commit.side_effect = Exception("disk full")

    body, status = _add_vinyl(make_vinyl_body())

    assert status == 400
    assert "disk full" in body["mesg"]
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


# --------------------------------------------------------------------------
# get_vinyl(query)
# --------------------------------------------------------------------------

def test_get_vinyl_found(mock_session, mock_presenters):
    present_vinyl, _ = mock_presenters
    fake_vinyl = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = fake_vinyl

    result, status = _get_vinyl(SimpleNamespace(name="Nevermind"))

    assert status == 200
    present_vinyl.assert_called_once_with(fake_vinyl)
    assert result == {"presented": "one"}
    mock_session.close.assert_called_once()


def test_get_vinyl_not_found_returns_404(mock_session, mock_presenters):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    body, status = _get_vinyl(SimpleNamespace(name="Unknown Album"))

    assert status == 404
    assert body == {"mesg": "Vinyl not found in the collection."}
    mock_session.close.assert_called_once()


def test_get_vinyl_exception_returns_400(mock_session, mock_presenters):
    mock_session.query.side_effect = Exception("connection lost")

    body, status = _get_vinyl(SimpleNamespace(name="Nevermind"))

    assert status == 400
    assert "connection lost" in body["mesg"]


# --------------------------------------------------------------------------
# update_vinyl(path, body)
# --------------------------------------------------------------------------

def test_update_vinyl_success(mock_session, mock_presenters):
    present_vinyl, _ = mock_presenters
    fake_vinyl = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = fake_vinyl

    path = SimpleNamespace(id=1)
    body = make_vinyl_body(name="Nevermind (Remastered)")

    result, status = _update_vinyl(path, body)

    assert fake_vinyl.name == "Nevermind (Remastered)"
    assert fake_vinyl.artist == "Nirvana"
    mock_session.commit.assert_called_once()
    present_vinyl.assert_called_once_with(fake_vinyl)
    assert status == 200
    assert result == {"presented": "one"}


def test_update_vinyl_not_found_returns_404(mock_session, mock_presenters):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    body, status = _update_vinyl(SimpleNamespace(id=999), make_vinyl_body())

    assert status == 404
    assert body == {"mesg": "Vinyl not found for update."}


def test_update_vinyl_exception_returns_400(mock_session, mock_presenters):
    mock_session.query.side_effect = Exception("timeout")

    body, status = _update_vinyl(SimpleNamespace(id=1), make_vinyl_body())

    assert status == 400
    assert "timeout" in body["mesg"]
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


# --------------------------------------------------------------------------
# delete_vinyl(path)
# --------------------------------------------------------------------------

def test_delete_vinyl_success(mock_session):
    fake_vinyl = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = fake_vinyl

    body, status = _delete_vinyl(SimpleNamespace(id=7))

    mock_session.delete.assert_called_once_with(fake_vinyl)
    mock_session.commit.assert_called_once()
    assert status == 200
    assert body == {"mesg": "Vinyl successfully removed", "id": 7}


def test_delete_vinyl_not_found_returns_404(mock_session):
    mock_session.query.return_value.filter.return_value.first.return_value = None

    body, status = _delete_vinyl(SimpleNamespace(id=42))

    assert status == 404
    assert body == {"mesg": "Vinyl not found for removal."}


def test_delete_vinyl_exception_returns_400(mock_session):
    mock_session.query.side_effect = Exception("locked row")

    body, status = _delete_vinyl(SimpleNamespace(id=1))

    assert status == 400
    assert "locked row" in body["mesg"]
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
