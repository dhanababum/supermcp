"""Kubernetes MCP Connector - Main Entry Point"""

from mcp_pkg.dynamic_mcp import (
    create_dynamic_mcp,
    get_current_server_id,
    get_current_server_config
)
from typing import Dict, Any, Optional, List
import os
import logging

from schema import KubernetesConfig
from session_manager import SessionManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp, app = create_dynamic_mcp(
    name="kubernetes",
    config=KubernetesConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__),
        "media/kubernetes-48.png"),
    stateless_http=True,
)

ui_schema = {
    "cluster_url": {
        "ui:widget": "text",
        "ui:placeholder": "https://kubernetes.example.com:6443",
        "ui:help": "Kubernetes API server URL",
    },
    "auth_type": {
        "ui:widget": "radio",
        "ui:help": "Authentication method",
    },
    "token": {
        "ui:widget": "password",
        "ui:help": "Bearer token (service account token)",
    },
    "kubeconfig_data": {
        "ui:widget": "textarea",
        "ui:options": {"rows": 8},
        "ui:placeholder": "Paste kubeconfig YAML content here",
        "ui:help": "Kubeconfig file content as YAML",
    },
    "verify_ssl": {
        "ui:widget": "checkbox",
        "ui:help": "Verify SSL certificates",
    },
    "default_namespace": {
        "ui:widget": "text",
        "ui:placeholder": "default",
        "ui:help": "Default namespace for operations",
    },
    "timeout": {
        "ui:widget": "updown",
        "ui:help": "Request timeout in seconds",
    },
}
mcp.register_ui_schema(ui_schema)

session_manager: SessionManager = SessionManager(
    global_max_sessions=100,
    per_target_max=10,
    idle_ttl=300
)


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: KubernetesConfig):
    """Initialize Kubernetes client when MCP server starts."""
    try:
        logger.info(f"Initializing Kubernetes connection for {server_config.cluster_url}")
        await session_manager.get_session(server_id, server_config)
        db_name = server_config.db_name or "default"
        logger.info(f"Kubernetes connection established for server: {db_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes connection: {str(e)}")
        raise


@mcp.on_server_destroy()
async def on_server_stop():
    """Cleanup Kubernetes client when MCP server stops."""
    server_id = get_current_server_id()
    await session_manager.close_session(server_id)
    logger.info(f"Closing Kubernetes connection for server {server_id}")


# Connection
@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """
    Test the connection to the Kubernetes cluster.
    
    Returns cluster version info and connection status.
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.test_connection(server_id, server_config)


# Namespaces
@mcp.tool()
async def list_namespaces() -> List[Dict[str, Any]]:
    """List all namespaces in the cluster."""
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_namespaces(server_id, server_config)


@mcp.tool()
async def get_namespace(name: str) -> Dict[str, Any]:
    """
    Get details of a specific namespace.
    
    Args:
        name: Namespace name
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_namespace(server_id, server_config, name)


# Pods
@mcp.tool()
async def list_pods(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List pods in a namespace or all namespaces.
    
    Args:
        namespace: Namespace to list pods from (None for all)
        label_selector: Filter by labels (e.g., "app=nginx")
        limit: Maximum number of pods to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_pods(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_pod(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific pod.
    
    Args:
        name: Pod name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_pod(server_id, server_config, name, namespace)


@mcp.tool()
async def delete_pod(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a pod.
    
    Args:
        name: Pod name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.delete_pod(server_id, server_config, name, namespace)


@mcp.tool()
async def get_pod_logs(
    name: str,
    namespace: Optional[str] = None,
    container: Optional[str] = None,
    tail_lines: int = 100,
    previous: bool = False
) -> str:
    """
    Get logs from a pod.
    
    Args:
        name: Pod name
        namespace: Namespace (uses default if not specified)
        container: Container name (for multi-container pods)
        tail_lines: Number of lines from the end to return
        previous: Get logs from previous container instance
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_pod_logs(
        server_id, server_config, name, namespace, container, tail_lines, previous
    )


# Deployments
@mcp.tool()
async def list_deployments(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List deployments.
    
    Args:
        namespace: Namespace (None for all namespaces)
        label_selector: Filter by labels
        limit: Maximum number of deployments to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_deployments(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_deployment(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific deployment.
    
    Args:
        name: Deployment name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_deployment(server_id, server_config, name, namespace)


@mcp.tool()
async def create_deployment(
    name: str,
    image: str,
    namespace: Optional[str] = None,
    replicas: int = 1,
    port: Optional[int] = None,
    labels: Optional[Dict[str, str]] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a new deployment.
    
    Args:
        name: Deployment name
        image: Container image (e.g., "nginx:latest")
        namespace: Namespace (uses default if not specified)
        replicas: Number of replicas
        port: Container port to expose
        labels: Labels for the deployment and pods
        env: Environment variables
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.create_deployment(
        server_id, server_config, name, image, namespace, replicas, port, labels, env
    )


@mcp.tool()
async def update_deployment(
    name: str,
    namespace: Optional[str] = None,
    image: Optional[str] = None,
    replicas: Optional[int] = None
) -> Dict[str, Any]:
    """
    Update an existing deployment.
    
    Args:
        name: Deployment name
        namespace: Namespace (uses default if not specified)
        image: New container image
        replicas: New replica count
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.update_deployment(
        server_id, server_config, name, namespace, image, replicas
    )


@mcp.tool()
async def delete_deployment(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a deployment.
    
    Args:
        name: Deployment name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.delete_deployment(server_id, server_config, name, namespace)


@mcp.tool()
async def scale_deployment(
    name: str,
    replicas: int,
    namespace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scale a deployment to a specific number of replicas.
    
    Args:
        name: Deployment name
        replicas: Target number of replicas
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.scale_deployment(
        server_id, server_config, name, replicas, namespace
    )


# Services
@mcp.tool()
async def list_services(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List services.
    
    Args:
        namespace: Namespace (None for all namespaces)
        label_selector: Filter by labels
        limit: Maximum number of services to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_services(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_service(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific service.
    
    Args:
        name: Service name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_service(server_id, server_config, name, namespace)


@mcp.tool()
async def create_service(
    name: str,
    selector: Dict[str, str],
    port: int,
    namespace: Optional[str] = None,
    target_port: Optional[int] = None,
    service_type: str = "ClusterIP"
) -> Dict[str, Any]:
    """
    Create a new service.
    
    Args:
        name: Service name
        selector: Pod selector labels (e.g., {"app": "nginx"})
        port: Service port
        namespace: Namespace (uses default if not specified)
        target_port: Target container port (defaults to port)
        service_type: Service type (ClusterIP, NodePort, LoadBalancer)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.create_service(
        server_id, server_config, name, selector, port, namespace, target_port, service_type
    )


@mcp.tool()
async def delete_service(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a service.
    
    Args:
        name: Service name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.delete_service(server_id, server_config, name, namespace)


# ConfigMaps
@mcp.tool()
async def list_configmaps(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List ConfigMaps.
    
    Args:
        namespace: Namespace (None for all namespaces)
        label_selector: Filter by labels
        limit: Maximum number of ConfigMaps to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_configmaps(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_configmap(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific ConfigMap.
    
    Args:
        name: ConfigMap name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_configmap(server_id, server_config, name, namespace)


@mcp.tool()
async def create_configmap(
    name: str,
    data: Dict[str, str],
    namespace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new ConfigMap.
    
    Args:
        name: ConfigMap name
        data: Key-value data for the ConfigMap
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.create_configmap(
        server_id, server_config, name, data, namespace
    )


@mcp.tool()
async def delete_configmap(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a ConfigMap.
    
    Args:
        name: ConfigMap name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.delete_configmap(server_id, server_config, name, namespace)


# Secrets
@mcp.tool()
async def list_secrets(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List Secrets (metadata only, data excluded for security).
    
    Args:
        namespace: Namespace (None for all namespaces)
        label_selector: Filter by labels
        limit: Maximum number of Secrets to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_secrets(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_secret(
    name: str,
    namespace: Optional[str] = None,
    decode: bool = False
) -> Dict[str, Any]:
    """
    Get details of a specific Secret.
    
    Args:
        name: Secret name
        namespace: Namespace (uses default if not specified)
        decode: Whether to decode base64 data
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_secret(
        server_id, server_config, name, namespace, decode
    )


@mcp.tool()
async def create_secret(
    name: str,
    data: Dict[str, str],
    namespace: Optional[str] = None,
    secret_type: str = "Opaque"
) -> Dict[str, Any]:
    """
    Create a new Secret.
    
    Args:
        name: Secret name
        data: Key-value data (will be base64 encoded)
        namespace: Namespace (uses default if not specified)
        secret_type: Secret type (Opaque, kubernetes.io/tls, etc.)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.create_secret(
        server_id, server_config, name, data, namespace, secret_type
    )


@mcp.tool()
async def delete_secret(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a Secret.
    
    Args:
        name: Secret name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.delete_secret(server_id, server_config, name, namespace)


# PVCs
@mcp.tool()
async def list_pvcs(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List PersistentVolumeClaims.
    
    Args:
        namespace: Namespace (None for all namespaces)
        label_selector: Filter by labels
        limit: Maximum number of PVCs to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_pvcs(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_pvc(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific PersistentVolumeClaim.
    
    Args:
        name: PVC name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_pvc(server_id, server_config, name, namespace)


# Ingresses
@mcp.tool()
async def list_ingresses(
    namespace: Optional[str] = None,
    label_selector: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List Ingresses.
    
    Args:
        namespace: Namespace (None for all namespaces)
        label_selector: Filter by labels
        limit: Maximum number of Ingresses to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_ingresses(
        server_id, server_config, namespace, label_selector, limit
    )


@mcp.tool()
async def get_ingress(name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific Ingress.
    
    Args:
        name: Ingress name
        namespace: Namespace (uses default if not specified)
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.get_ingress(server_id, server_config, name, namespace)


# Events
@mcp.tool()
async def list_events(
    namespace: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List cluster events.
    
    Args:
        namespace: Namespace (None for all namespaces)
        limit: Maximum number of events to return
    """
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    return await session_manager.list_events(server_id, server_config, namespace, limit)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8031")),
        reload=False,
        workers=int(os.getenv("WORKERS", "1")),
    )
