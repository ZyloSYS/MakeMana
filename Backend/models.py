from __future__ import annotations

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class Denuncia(db.Model):
    __tablename__ = "denuncias"

    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(32), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=True)
    contato = db.Column(db.String(160), nullable=True)
    local_ocorrencia = db.Column(db.String(255), nullable=True)
    data_ocorrencia = db.Column(db.Date, nullable=True)
    descricao = db.Column(db.Text, nullable=False)
    pedido_urgente = db.Column(db.Boolean, nullable=False, default=False)
    aceita_contato = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(32), nullable=False, default="recebido", index=True)
    produto_id = db.Column(db.String(80), nullable=True)
    produto_nome = db.Column(db.String(160), nullable=True)
    produto_preco = db.Column(db.String(40), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True, index=True)
    observacoes_admin = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "protocolo": self.protocolo,
            "nome": self.nome,
            "contato": self.contato,
            "local_ocorrencia": self.local_ocorrencia,
            "data_ocorrencia": self.data_ocorrencia.isoformat() if self.data_ocorrencia else None,
            "descricao": self.descricao,
            "pedido_urgente": self.pedido_urgente,
            "aceita_contato": self.aceita_contato,
            "status": self.status,
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "produto_preco": self.produto_preco,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    denuncias = db.relationship("Denuncia", backref="usuario", lazy=True)

    def set_password(self, password: str) -> None:
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.senha_hash, password)
