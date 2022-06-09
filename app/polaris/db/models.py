from sqlalchemy import Column, Text
from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import MetaData

from app.db import UpdatedAtMixin

metadata = MetaData()
Base: AutomapBase = automap_base(metadata=metadata)


class AccountHolder(Base, UpdatedAtMixin):
    __tablename__ = "account_holder"

    accountholderprofile_collection = relationship(
        "AccountHolderProfile", backref="account_holder", cascade="all, delete-orphan"
    )
    accountholderreward_collection = relationship(
        "AccountHolderReward", backref="account_holder", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        return f"{self.email} ({self.id}, {self.retailerconfig.slug})"


class AccountHolderProfile(Base):
    __tablename__ = "account_holder_profile"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AccountHolderReward(Base):
    __tablename__ = "account_holder_reward"

    def __str__(self) -> str:
        return self.code


class RetailerConfig(Base, UpdatedAtMixin):
    __tablename__ = "retailer_config"

    marketing_preference_config = Column(Text, nullable=False, default="")

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class AccountHolderCampaignBalance(Base, UpdatedAtMixin):
    __tablename__ = "account_holder_campaign_balance"

    def __str__(self) -> str:
        return f"{self.campaign_slug}: ({self.balance})"


class AccountHolderMarketingPreference(Base, UpdatedAtMixin):
    __tablename__ = "account_holder_marketing_preference"

    def __str__(self) -> str:
        return f"{self.key_name}: {self.value}"


class AccountHolderPendingReward(Base):
    __tablename__ = "account_holder_pending_reward"

    def __str__(self) -> str:
        return f"{self.reward_slug}: {self.value}"


class EmailTemplate(Base, UpdatedAtMixin):
    __tablename__ = "email_template"

    def __repr__(self) -> str:
        return f"{self.retailerconfig.slug}: {self.type}"


class EmailTemplateKey(Base, UpdatedAtMixin):
    __tablename__ = "email_template_key"

    def __repr__(self) -> str:
        return self.name


class EmailTemplateRequiredKey(Base):
    __tablename__ = "email_template_required_key"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.email_template.type}, {self.email_template_key.name})"
