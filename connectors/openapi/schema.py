from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class AuthType(str, Enum):
    none = "none"
    bearer_token = "bearer_token"
    api_key = "api_key"
    custom_header = "custom_header"


class OpenAPIConfig(BaseModel):
    """Configuration model for OpenAPI connector."""

    spec_url: Optional[str] = Field(
        default=None,
        description="URL to Swagger/OpenAPI JSON or YAML file"
    )
    spec_raw: Optional[str] = Field(
        default=None,
        description="Swagger/OpenAPI content as JSON or YAML string"
    )
    timeout: int = Field(
        default=30,
        description="HTTP timeout in seconds when loading spec_url"
    )
    auth_type: AuthType = Field(
        default=AuthType.none,
        description="Authentication method to use when calling the target API"
    )
    auth_token: Optional[str] = Field(
        default=None,
        description="Token or API key used for target API calls"
    )
    auth_header_name: Optional[str] = Field(
        default=None,
        description="Header name for api_key or custom_header authentication"
    )

    @model_validator(mode="after")
    def validate_config(self):
        if bool(self.spec_url) == bool(self.spec_raw):
            raise ValueError(
                "Exactly one of spec_url or spec_raw must be provided"
            )
        if self.auth_type != AuthType.none and not self.auth_token:
            raise ValueError("auth_token is required when auth_type is not none")
        if self.auth_type == AuthType.custom_header and not self.auth_header_name:
            raise ValueError(
                "auth_header_name is required when auth_type is custom_header"
            )
        return self
