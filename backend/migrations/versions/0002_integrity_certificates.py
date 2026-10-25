from alembic import op
import sqlalchemy as sa

revision = "0002_integrity_certificates"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "integrity_certificates",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("evidence_id", sa.String(length=36), sa.ForeignKey("evidence.id"), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("issuer_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("signature_algorithm", sa.String(length=32), nullable=False),
        sa.Column("signing_key_id", sa.String(length=100), nullable=False),
        sa.Column("public_key_pem", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("evidence_id", "sha256", name="uq_certificate_evidence_digest"),
    )
    op.create_index("ix_integrity_certificates_evidence_id", "integrity_certificates", ["evidence_id"])
    op.create_index("ix_integrity_certificates_sha256", "integrity_certificates", ["sha256"])
    op.create_index("ix_integrity_certificates_status", "integrity_certificates", ["status"])


def downgrade():
    op.drop_index("ix_integrity_certificates_status", table_name="integrity_certificates")
    op.drop_index("ix_integrity_certificates_sha256", table_name="integrity_certificates")
    op.drop_index("ix_integrity_certificates_evidence_id", table_name="integrity_certificates")
    op.drop_table("integrity_certificates")
