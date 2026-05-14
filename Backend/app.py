from __future__ import annotations

import os
import secrets
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy import func, or_, text
from werkzeug.security import check_password_hash

try:
    from .data import CATEGORY_LABELS, PRODUCTS, TESTIMONIALS, product_by_id, products_by_line
    from .models import Denuncia, Usuario, db
except ImportError:  # Allows running with `python app.py` from Backend.
    from data import CATEGORY_LABELS, PRODUCTS, TESTIMONIALS, product_by_id, products_by_line
    from models import Denuncia, Usuario, db


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "Frontend"
STATUS_CHOICES = {
    "recebido": "Recebido",
    "em_producao": "Em produção",
    "saiu_entrega": "Saiu para entrega",
    "finalizado": "Finalizado",
}
STATUS_MIGRATION = {
    "recebida": "recebido",
    "em_analise": "em_producao",
    "encaminhada": "saiu_entrega",
    "resolvida": "finalizado",
    "arquivada": "finalizado",
}


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    load_dotenv(BACKEND_DIR / ".env")

    app = Flask(__name__, template_folder=str(FRONTEND_DIR), static_folder=None)
    db_path = BACKEND_DIR / "instance" / "makemana.db"
    db_path.parent.mkdir(exist_ok=True)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-this-secret"),
        SQLALCHEMY_DATABASE_URI=_database_uri(db_path),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        JSON_AS_ASCII=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.getenv("RENDER")),
        PREFERRED_URL_SCHEME="https" if os.getenv("RENDER") else "http",
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    register_routes(app)

    with app.app_context():
        db.create_all()
        _ensure_sqlite_schema()
        _normalize_statuses()

    return app


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "current_user": _current_user(),
            "status_choices": STATUS_CHOICES,
            "category_labels": CATEGORY_LABELS,
            "search_query": request.args.get("q", ""),
        }

    @app.get("/style.css")
    def style_css():
        return send_from_directory(FRONTEND_DIR, "style.css")

    @app.get("/backend.css")
    def backend_css():
        return send_from_directory(FRONTEND_DIR, "backend.css")

    @app.get("/app.js")
    def app_js():
        return send_from_directory(FRONTEND_DIR, "app.js")

    @app.get("/variables.css")
    def variables_css():
        return send_from_directory(FRONTEND_DIR, "variables.css")

    @app.get("/img/<path:filename>")
    def images(filename: str):
        return send_from_directory(FRONTEND_DIR / "img", filename)

    @app.get("/")
    @app.get("/index.html")
    def index():
        return render_template(
            "index.html",
            products=[product for product in PRODUCTS if product.get("destaque")],
            testimonials=TESTIMONIALS,
        )

    @app.get("/produtos")
    @app.get("/produtos.html")
    def produtos():
        return render_template(
            "produtos.html",
            title="Sinais",
            subtitle="Todos os",
            products=PRODUCTS,
            selected_line=None,
        )

    @app.get("/kits")
    @app.get("/kits.html")
    def kits():
        return render_template(
            "produtos.html",
            title="Planos",
            subtitle="Nossos",
            products=products_by_line("kits"),
            selected_line="kits",
        )

    @app.get("/skincare")
    @app.get("/skincare.html")
    def skincare():
        return render_template(
            "produtos.html",
            title="Camadas",
            subtitle="Linha de",
            products=products_by_line("skincare"),
            selected_line="skincare",
        )

    @app.get("/maquiagem")
    @app.get("/maquiagem.html")
    def maquiagem():
        return render_template(
            "produtos.html",
            title="Sinais",
            subtitle="Linha de",
            products=products_by_line("maquiagem"),
            selected_line="maquiagem",
        )

    @app.get("/institucional")
    @app.get("/institucional.html")
    def institucional():
        return render_template("institucional.html")

    @app.get("/produto/<product_id>")
    @app.get("/paginadetalhamento.html")
    def produto_detalhe(product_id: str | None = None):
        product = product_by_id(product_id or request.args.get("produto"))
        if not product:
            product = PRODUCTS[0]
        return render_template("paginadetalhamento.html", product=product)

    @app.route("/pedido", methods=["GET", "POST"])
    @app.route("/carrinho", methods=["GET", "POST"])
    @app.route("/carrinhodecompra.html", methods=["GET", "POST"])
    def pedido():
        if request.method == "POST":
            denuncia, errors = denuncia_from_payload(_request_payload())
            if errors:
                for error in errors:
                    flash(error, "error")
                product = product_by_id(request.form.get("produto_id"))
                return render_template("carrinhodecompra.html", form=request.form, product=product), 400

            db.session.add(denuncia)
            db.session.commit()
            return redirect(url_for("pedido_confirmacao", protocolo=denuncia.protocolo))

        product = product_by_id(request.args.get("produto"))
        return render_template("carrinhodecompra.html", form={}, product=product)

    @app.get("/pedido/confirmacao")
    @app.get("/finalizaçaocompra.html")
    def pedido_confirmacao():
        protocolo = request.args.get("protocolo", "")
        denuncia = Denuncia.query.filter_by(protocolo=protocolo).first() if protocolo else None
        product = product_by_id(denuncia.produto_id) if denuncia and denuncia.produto_id else None
        return render_template(
            "finalizaçaocompra.html",
            protocolo=protocolo,
            denuncia=denuncia,
            product=product,
        )

    @app.route("/login", methods=["GET", "POST"])
    @app.route("/usuario/login", methods=["GET", "POST"])
    def usuario_login():
        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            codigo = request.form.get("codigo", "").strip()
            senha = request.form.get("senha", "")
            action = request.form.get("action", "login")

            if action == "register":
                if not nome:
                    flash("Informe seu nome de usuario para criar o acesso.", "error")
                    return render_template("usuario_login.html"), 400
                if not _valid_user_password(senha):
                    flash("A senha do cadastro deve ter exatamente 6 digitos numericos.", "error")
                    return render_template("usuario_login.html"), 400
                usuario = Usuario.query.filter(func.lower(Usuario.nome) == nome.lower()).first()
                if usuario:
                    flash("Esse nome ja existe. Entre com o codigo recebido.", "error")
                    return render_template("usuario_login.html"), 400
                codigo_acesso = _new_user_token()
                usuario = Usuario(nome=nome, codigo_acesso=codigo_acesso)
                usuario.set_password(senha)
                db.session.add(usuario)
                db.session.commit()
                session.clear()
                session["user_id"] = usuario.id
                session["user_nome"] = usuario.nome
                flash(f"Seu codigo de acesso e {codigo_acesso}. Guarde esse codigo para entrar novamente.", "success")
                return redirect(url_for("perfil"))

            if not codigo:
                flash("Informe o codigo de acesso.", "error")
                return render_template("usuario_login.html"), 400
            usuario = Usuario.query.filter(func.lower(Usuario.codigo_acesso) == codigo.lower()).first()
            if not usuario or not usuario.check_token(codigo):
                flash("Codigo de acesso invalido.", "error")
                return render_template("usuario_login.html"), 400
            session.clear()
            session["user_id"] = usuario.id
            session["user_nome"] = usuario.nome
            next_url = _safe_next_url(request.args.get("next")) or url_for("perfil")
            return redirect(next_url)

        return render_template("usuario_login.html")

    @app.get("/perfil")
    @user_required
    def perfil():
        usuario = _current_user()
        denuncias = (
            Denuncia.query.filter_by(usuario_id=usuario.id)
            .order_by(Denuncia.created_at.desc())
            .all()
        )
        return render_template("perfil.html", usuario=usuario, denuncias=denuncias)

    @app.get("/logout")
    def usuario_logout():
        session.clear()
        return redirect(url_for("index"))

    @app.post("/api/denuncias")
    def api_criar_denuncia():
        denuncia, errors = denuncia_from_payload(_request_payload())
        if errors:
            return jsonify({"errors": errors}), 400

        db.session.add(denuncia)
        db.session.commit()
        return jsonify({"denuncia": denuncia.to_dict()}), 201

    @app.get("/api/produtos")
    def api_produtos():
        line = _clean(request.args.get("linha"))
        return jsonify({"produtos": products_by_line(line)})

    @app.get("/api/produtos/<product_id>")
    def api_produto(product_id: str):
        product = product_by_id(product_id)
        if not product:
            abort(404)
        return jsonify({"produto": product})

    @app.get("/api/health")
    def healthcheck():
        return jsonify({"status": "ok"})

    @app.route("/admin/login", methods=["GET", "POST"])
    @app.route("/adminlogin.html", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if _valid_admin_credentials(username, password):
                session.clear()
                session["admin_logged_in"] = True
                session["admin_username"] = username
                return redirect(url_for("admin_dashboard"))

            flash("Usuario ou senha invalidos.", "error")

        return render_template("adminlogin.html")

    @app.get("/admin/logout")
    def admin_logout():
        session.clear()
        return redirect(url_for("admin_login"))

    @app.get("/admin")
    @app.get("/admindashboard.html")
    @admin_required
    def admin_dashboard():
        status_filter = request.args.get("status", "").strip()
        query_text = request.args.get("q", "").strip()

        query = Denuncia.query
        if status_filter in STATUS_CHOICES:
            query = query.filter(Denuncia.status == status_filter)
        if query_text:
            like = f"%{query_text}%"
            query = query.filter(
                or_(
                    Denuncia.protocolo.ilike(like),
                    Denuncia.descricao.ilike(like),
                    Denuncia.local_ocorrencia.ilike(like),
                    Denuncia.contato.ilike(like),
                    Denuncia.produto_nome.ilike(like),
                )
            )

        denuncias = (
            query.order_by(Denuncia.pedido_urgente.desc(), Denuncia.created_at.desc())
            .limit(200)
            .all()
        )
        stats = _dashboard_stats()

        return render_template(
            "admindashboard.html",
            denuncias=denuncias,
            stats=stats,
            status_choices=STATUS_CHOICES,
            status_filter=status_filter,
            query_text=query_text,
        )

    @app.route("/admin/denuncias/<int:denuncia_id>", methods=["GET", "POST"])
    @admin_required
    def admin_denuncia_detail(denuncia_id: int):
        denuncia = db.get_or_404(Denuncia, denuncia_id)

        if request.method == "POST":
            new_status = request.form.get("status", denuncia.status)
            if new_status not in STATUS_CHOICES:
                abort(400)

            denuncia.status = new_status
            denuncia.observacoes_admin = request.form.get("observacoes_admin", "").strip()
            denuncia.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            flash("Registro atualizado.", "success")
            return redirect(url_for("admin_denuncia_detail", denuncia_id=denuncia.id))

        return render_template(
            "admin_denuncia.html",
            denuncia=denuncia,
            status_choices=STATUS_CHOICES,
        )

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Pagina nao encontrada."), 404

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("error.html", code=500, message="Erro interno do servidor."), 500


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("usuario_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def denuncia_from_payload(payload: dict[str, Any]) -> tuple[Denuncia, list[str]]:
    descricao = _clean(payload.get("descricao") or payload.get("observacoes") or payload.get("mensagem"))
    data_ocorrencia, date_error = _parse_optional_date(payload.get("data_ocorrencia"))
    product = product_by_id(_clean(payload.get("produto_id")))
    usuario = _current_user()
    errors: list[str] = []

    if not descricao:
        errors.append("Preencha as observacoes do pedido.")
    elif len(descricao) < 10:
        errors.append("As observacoes precisam ter pelo menos 10 caracteres.")
    if date_error:
        errors.append(date_error)

    denuncia = Denuncia(
        protocolo=_new_protocol(),
        nome=_clean(payload.get("nome")),
        contato=_clean(payload.get("contato")),
        local_ocorrencia=_compose_location(payload),
        data_ocorrencia=data_ocorrencia,
        descricao=descricao,
        pedido_urgente=_is_truthy(payload.get("pedido_urgente") or payload.get("urgente")),
        aceita_contato=_is_truthy(payload.get("aceita_contato") or payload.get("autorizacao_contato")),
        produto_id=product["id"] if product else _clean(payload.get("produto_id")),
        produto_nome=product["nome"] if product else _clean(payload.get("produto_nome")) or "Pedido especial",
        produto_preco=product["preco"] if product else _clean(payload.get("produto_preco")),
        usuario_id=usuario.id if usuario else None,
    )
    return denuncia, errors


def _request_payload() -> dict[str, Any]:
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


def _safe_next_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return None
    if not value.startswith("/"):
        return None
    return value


def _compose_location(payload: dict[str, Any]) -> str | None:
    direct = _clean(payload.get("local_ocorrencia") or payload.get("local"))
    if direct:
        return direct

    parts = [
        _clean(payload.get("endereco")),
        _clean(payload.get("complemento")),
        _clean(payload.get("bairro")),
        _clean(payload.get("cidade")),
        _clean(payload.get("cep")),
    ]
    return " - ".join(part for part in parts if part) or None


def _database_uri(sqlite_path: Path) -> str:
    uri = os.getenv("DATABASE_URL")
    if not uri:
        return f"sqlite:///{sqlite_path}"
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql+psycopg://", 1)
    if uri.startswith("postgresql://"):
        return uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return uri


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_optional_date(value: Any) -> tuple[date | None, str | None]:
    if not value:
        return None, None
    try:
        return date.fromisoformat(str(value)), None
    except ValueError:
        return None, "Informe uma data valida."


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "on", "sim", "yes", "y"}


def _new_protocol() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    while True:
        code = f"MM-{today}-{secrets.token_hex(3).upper()}"
        if not Denuncia.query.filter_by(protocolo=code).first():
            return code


def _new_user_token() -> str:
    while True:
        code = f"MMU-{secrets.token_hex(4).upper()}"
        if not Usuario.query.filter_by(codigo_acesso=code).first():
            return code


def _valid_user_password(password: str) -> bool:
    return len(password) == 6 and password.isdigit()


def _valid_admin_credentials(username: str, password: str) -> bool:
    expected_username = os.getenv("ADMIN_USERNAME", "admin")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    plain_password = os.getenv("ADMIN_PASSWORD", "admin123")

    if username != expected_username:
        return False
    if password_hash:
        return check_password_hash(password_hash, password)
    return secrets.compare_digest(password, plain_password)


def _current_user() -> Usuario | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(Usuario, user_id)


def _dashboard_stats() -> dict[str, int]:
    stats = {status: 0 for status in STATUS_CHOICES}
    rows = db.session.query(Denuncia.status, func.count(Denuncia.id)).group_by(Denuncia.status).all()
    for status, total in rows:
        if status in stats:
            stats[status] = total
    stats["total"] = sum(stats.values())
    stats["urgentes"] = Denuncia.query.filter_by(pedido_urgente=True).count()
    return stats


def _ensure_sqlite_schema() -> None:
    uri = db.engine.url
    if uri.drivername != "sqlite":
        return

    denuncia_columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(denuncias)")).fetchall()
    }
    denuncia_migrations = {
        "produto_id": "ALTER TABLE denuncias ADD COLUMN produto_id VARCHAR(80)",
        "produto_nome": "ALTER TABLE denuncias ADD COLUMN produto_nome VARCHAR(160)",
        "produto_preco": "ALTER TABLE denuncias ADD COLUMN produto_preco VARCHAR(40)",
        "usuario_id": "ALTER TABLE denuncias ADD COLUMN usuario_id INTEGER",
    }
    for column, statement in denuncia_migrations.items():
        if column not in denuncia_columns:
            db.session.execute(text(statement))

    usuario_columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(usuarios)")).fetchall()
    }
    if "codigo_acesso" not in usuario_columns:
        db.session.execute(text("ALTER TABLE usuarios ADD COLUMN codigo_acesso VARCHAR(32)"))
        db.session.flush()
        for usuario in Usuario.query.all():
            usuario.codigo_acesso = _new_user_token()
    db.session.commit()


def _normalize_statuses() -> None:
    for old_status, new_status in STATUS_MIGRATION.items():
        Denuncia.query.filter_by(status=old_status).update({"status": new_status})
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
