from alembic import op
import sqlalchemy as sa
revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    role=sa.Enum("admin","analyst","viewer",name="userrole")
    role.create(op.get_bind(),checkfirst=True)
    op.create_table("users",sa.Column("id",sa.String(36),primary_key=True),sa.Column("email",sa.String(320),nullable=False,unique=True),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("role",role,nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_users_email","users",["email"],unique=True)
    op.create_table("evidence",sa.Column("id",sa.String(36),primary_key=True),sa.Column("case_reference",sa.String(100),nullable=False),sa.Column("filename",sa.String(255),nullable=False),sa.Column("media_type",sa.String(150),nullable=False),sa.Column("byte_size",sa.BigInteger(),nullable=False),sa.Column("sha256",sa.String(64),nullable=False),sa.Column("storage_key",sa.String(80),nullable=False,unique=True),sa.Column("uploaded_by",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("status",sa.String(24),nullable=False))
    op.create_index("ix_evidence_case_reference","evidence",["case_reference"]);op.create_index("ix_evidence_sha256","evidence",["sha256"])
    op.create_table("evidence_versions",sa.Column("id",sa.String(36),primary_key=True),sa.Column("evidence_id",sa.String(36),sa.ForeignKey("evidence.id"),nullable=False),sa.Column("version_number",sa.Integer(),nullable=False),sa.Column("sha256",sa.String(64),nullable=False),sa.Column("byte_size",sa.BigInteger(),nullable=False),sa.Column("storage_key",sa.String(80),nullable=False,unique=True),sa.Column("created_by",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_evidence_versions_evidence_id","evidence_versions",["evidence_id"])
    op.create_table("audit_events",sa.Column("id",sa.String(36),primary_key=True),sa.Column("actor_id",sa.String(36),sa.ForeignKey("users.id"),nullable=True),sa.Column("action",sa.String(100),nullable=False),sa.Column("resource_type",sa.String(80),nullable=False),sa.Column("resource_id",sa.String(36),nullable=True),sa.Column("detail",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_audit_events_action","audit_events",["action"])
    op.create_table("blockchain_anchors",sa.Column("id",sa.String(36),primary_key=True),sa.Column("evidence_id",sa.String(36),sa.ForeignKey("evidence.id"),nullable=False),sa.Column("sha256",sa.String(64),nullable=False),sa.Column("status",sa.String(24),nullable=False),sa.Column("tx_hash",sa.String(80),nullable=True),sa.Column("block_number",sa.Integer(),nullable=True),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_blockchain_anchors_evidence_id","blockchain_anchors",["evidence_id"])
def downgrade():
    op.drop_table("blockchain_anchors");op.drop_table("audit_events");op.drop_table("evidence_versions");op.drop_table("evidence")
    op.drop_index("ix_users_email",table_name="users");op.drop_table("users")
    sa.Enum(name="userrole").drop(op.get_bind(),checkfirst=True)
