from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app import _database_uri, create_app
from Backend.models import Denuncia, db


@pytest.fixture()
def app(tmp_path):
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        }
    )
    yield test_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_api_cria_denuncia_sem_categoria(client, app):
    response = client.post(
        "/api/denuncias",
        json={
            "descricao": "Preciso registrar uma situacao delicada com risco.",
            "pedido_urgente": True,
            "aceita_contato": False,
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["denuncia"]["protocolo"].startswith("MM-")
    assert "categoria" not in data["denuncia"]
    assert data["denuncia"]["status"] == "recebido"

    with app.app_context():
        denuncia = Denuncia.query.one()
        assert denuncia.descricao.startswith("Preciso registrar")
        assert denuncia.pedido_urgente is True


def test_formulario_pedido_cria_registro(client, app):
    response = client.post(
        "/pedido",
        data={
            "nome": "Cliente",
            "descricao": "Observacao discreta para registrar no sistema.",
            "pedido_urgente": "on",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with app.app_context():
        assert db.session.query(Denuncia).count() == 1


def test_usuario_cadastra_envia_e_acompanha_pedido(client, app):
    response = client.post(
        "/login",
        data={"nome": "Maria", "senha": "1234", "action": "register"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    response = client.post(
        "/pedido",
        data={
            "produto_id": "base-second-skin",
            "nome": "Maria",
            "descricao": "Quero acompanhar essa solicitacao pelo perfil.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    profile = client.get("/perfil")
    assert profile.status_code == 200
    assert b"Base Liquida Fluid" in profile.data
    assert b"Recebido" in profile.data

    with app.app_context():
        denuncia = Denuncia.query.one()
        assert denuncia.usuario is not None
        assert denuncia.produto_id == "base-second-skin"


def test_admin_atualiza_status_como_ecommerce(client, app):
    client.post(
        "/api/denuncias",
        json={
            "produto_id": "corretivo-4-seasons",
            "descricao": "Solicitacao para atualizacao no painel administrativo.",
        },
    )
    with app.app_context():
        denuncia_id = Denuncia.query.one().id

    login = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    response = client.post(
        f"/admin/denuncias/{denuncia_id}",
        data={"status": "saiu_entrega", "observacoes_admin": "Encaminhado."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Saiu para entrega" in response.data

    with app.app_context():
        assert db.session.get(Denuncia, denuncia_id).status == "saiu_entrega"


def test_barra_de_pesquisa_renderiza_termo_e_dados_de_filtro(client):
    response = client.get("/produtos?q=base")

    assert response.status_code == 200
    assert b'value="base"' in response.data
    assert b"data-search=" in response.data
    assert b"Base Liquida Fluid" in response.data


def test_database_uri_normaliza_postgres_do_render(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/makemana")

    uri = _database_uri(tmp_path / "makemana.db")

    assert uri == "postgresql+psycopg://user:pass@host:5432/makemana"
