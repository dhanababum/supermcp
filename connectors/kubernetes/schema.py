from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class AuthType(str, Enum):
    """Authentication types supported by Kubernetes connector"""
    BEARER_TOKEN = "bearer_token"
    KUBECONFIG = "kubeconfig"


class KubernetesConfig(BaseModel):
    """Configuration model for Kubernetes Connector"""

    cluster_url: str = Field(
        description="Kubernetes API server URL (e.g., https://k8s-cluster:6443)"
    )
    auth_type: AuthType = Field(
        default=AuthType.BEARER_TOKEN,
        description="Authentication method (bearer_token or kubeconfig)"
    )
    token: Optional[str] = Field(
        default=None,
        description="Bearer token for authentication (service account token)"
    )
    kubeconfig_data: Optional[str] = Field(
        default=None,
        description="Kubeconfig file content as YAML string"
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )
    default_namespace: str = Field(
        default="default",
        description="Default namespace for operations"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    db_name: Optional[str] = Field(
        default="default",
        description="Identifier for this Kubernetes cluster instance"
    )


class NamespaceParams(BaseModel):
    """Parameters for namespace operations"""
    name: str = Field(description="Namespace name")


class PodParams(BaseModel):
    """Parameters for pod operations"""
    name: str = Field(description="Pod name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class PodLogsParams(BaseModel):
    """Parameters for getting pod logs"""
    name: str = Field(description="Pod name")
    namespace: Optional[str] = Field(default=None, description="Namespace")
    container: Optional[str] = Field(default=None, description="Container name")
    tail_lines: Optional[int] = Field(default=100, description="Number of lines from end")
    previous: bool = Field(default=False, description="Get logs from previous container instance")


class DeploymentParams(BaseModel):
    """Parameters for deployment operations"""
    name: str = Field(description="Deployment name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class CreateDeploymentParams(BaseModel):
    """Parameters for creating a deployment"""
    name: str = Field(description="Deployment name")
    namespace: Optional[str] = Field(default=None, description="Namespace")
    image: str = Field(description="Container image")
    replicas: int = Field(default=1, description="Number of replicas")
    port: Optional[int] = Field(default=None, description="Container port")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Labels")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")


class ScaleDeploymentParams(BaseModel):
    """Parameters for scaling a deployment"""
    name: str = Field(description="Deployment name")
    namespace: Optional[str] = Field(default=None, description="Namespace")
    replicas: int = Field(description="Target number of replicas")


class ServiceParams(BaseModel):
    """Parameters for service operations"""
    name: str = Field(description="Service name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class CreateServiceParams(BaseModel):
    """Parameters for creating a service"""
    name: str = Field(description="Service name")
    namespace: Optional[str] = Field(default=None, description="Namespace")
    selector: Dict[str, str] = Field(description="Pod selector labels")
    port: int = Field(description="Service port")
    target_port: Optional[int] = Field(default=None, description="Target container port")
    service_type: str = Field(default="ClusterIP", description="Service type")


class ConfigMapParams(BaseModel):
    """Parameters for ConfigMap operations"""
    name: str = Field(description="ConfigMap name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class CreateConfigMapParams(BaseModel):
    """Parameters for creating a ConfigMap"""
    name: str = Field(description="ConfigMap name")
    namespace: Optional[str] = Field(default=None, description="Namespace")
    data: Dict[str, str] = Field(description="ConfigMap data")


class SecretParams(BaseModel):
    """Parameters for Secret operations"""
    name: str = Field(description="Secret name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class CreateSecretParams(BaseModel):
    """Parameters for creating a Secret"""
    name: str = Field(description="Secret name")
    namespace: Optional[str] = Field(default=None, description="Namespace")
    data: Dict[str, str] = Field(description="Secret data (will be base64 encoded)")
    secret_type: str = Field(default="Opaque", description="Secret type")


class PVCParams(BaseModel):
    """Parameters for PVC operations"""
    name: str = Field(description="PVC name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class IngressParams(BaseModel):
    """Parameters for Ingress operations"""
    name: str = Field(description="Ingress name")
    namespace: Optional[str] = Field(default=None, description="Namespace")


class ListParams(BaseModel):
    """Parameters for list operations"""
    namespace: Optional[str] = Field(default=None, description="Namespace (None for all namespaces)")
    label_selector: Optional[str] = Field(default=None, description="Label selector")
    limit: int = Field(default=100, description="Maximum number of items to return")
