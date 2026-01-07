from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AuthType(str, Enum):
    """Authentication types supported by Grafana"""
    SERVICE_ACCOUNT_TOKEN = "service_account_token"
    API_KEY = "api_key"


class GrafanaConfig(BaseModel):
    """Configuration model for Grafana Connector"""

    grafana_url: str = Field(
        description=(
            "Full URL to your Grafana instance "
            "(e.g., https://grafana.example.com)"
        )
    )
    auth_type: AuthType = Field(
        default=AuthType.SERVICE_ACCOUNT_TOKEN,
        description=(
            "Authentication method "
            "(service_account_token recommended for Grafana 9.0+)"
        )
    )
    service_account_token: Optional[str] = Field(
        default=None,
        description="Service account token for authentication (Grafana 9.0+)"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API Key for authentication (legacy method)"
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates (recommended for production)"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    additional_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional HTTP headers as JSON object (optional)"
    )
    db_name: Optional[str] = Field(
        default="default",
        description="Identifier for this Grafana instance"
    )


class GetDashboardParams(BaseModel):
    """Parameters for getting a dashboard"""
    uid: str = Field(description="Dashboard UID")


class CreateDashboardParams(BaseModel):
    """Parameters for creating a dashboard"""
    dashboard: Dict[str, Any] = Field(
        description="Dashboard JSON object"
    )
    folder_uid: Optional[str] = Field(
        default=None,
        description="UID of the folder to create dashboard in (optional)"
    )
    message: Optional[str] = Field(
        default=None,
        description="Commit message for dashboard creation (optional)"
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite existing dashboard with same UID"
    )


class UpdateDashboardParams(BaseModel):
    """Parameters for updating a dashboard"""
    dashboard: Dict[str, Any] = Field(
        description="Dashboard JSON object with updated content"
    )
    overwrite: bool = Field(
        default=True,
        description="Whether to overwrite the existing dashboard"
    )
    message: Optional[str] = Field(
        default=None,
        description="Commit message for dashboard update (optional)"
    )


class DeleteDashboardParams(BaseModel):
    """Parameters for deleting a dashboard"""
    uid: str = Field(description="Dashboard UID to delete")


class SearchDashboardsParams(BaseModel):
    """Parameters for searching dashboards"""
    query: Optional[str] = Field(
        default=None,
        description="Search query string (searches title and tags)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="List of tags to filter by"
    )
    folder_ids: Optional[List[int]] = Field(
        default=None,
        description="List of folder IDs to search in"
    )
    limit: int = Field(
        default=100,
        description="Maximum number of results to return"
    )


class CloneDashboardTemplate(BaseModel):
    """Template for cloning a dashboard"""
    source_uid: str = Field(
        description="UID of the dashboard to clone"
    )
    new_title: str = Field(
        description="Title for the cloned dashboard"
    )
    folder_uid: Optional[str] = Field(
        default=None,
        description="UID of the folder to create cloned dashboard in"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags to add to the cloned dashboard"
    )


class BackupDashboardTemplate(BaseModel):
    """Template for backing up a dashboard"""
    uid: str = Field(
        description="UID of the dashboard to backup"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include dashboard metadata (version, timestamps)"
    )


class GetDatasourceParams(BaseModel):
    """Parameters for getting a datasource by name"""
    name: str = Field(
        description="Name of the datasource to find"
    )

