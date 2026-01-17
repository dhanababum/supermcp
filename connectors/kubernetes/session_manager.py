import asyncio
import base64
from collections import OrderedDict
import logging
from typing import Any, Dict, Optional, List
import yaml

from kubernetes_asyncio import client
from kubernetes_asyncio.client import ApiClient, Configuration
from kubernetes_asyncio.config import load_kube_config_from_dict

from schema import KubernetesConfig, AuthType


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages Kubernetes API client sessions for multiple clusters.
    """

    def __init__(
        self, global_max_sessions=100, per_target_max=10, idle_ttl=300
    ):
        self.global_max = global_max_sessions
        self.per_target_max = per_target_max
        self.idle_ttl = idle_ttl
        self.sessions: OrderedDict[str, tuple] = OrderedDict()
        self.total_sessions = 0
        self.lock = asyncio.Lock()

    async def _create_configuration(
        self, server_config: KubernetesConfig
    ) -> Configuration:
        """Create Kubernetes client configuration from server config."""
        configuration = Configuration()
        configuration.host = server_config.cluster_url.rstrip('/')
        configuration.verify_ssl = server_config.verify_ssl

        if server_config.auth_type == AuthType.BEARER_TOKEN:
            if not server_config.token:
                raise ValueError("Token is required for bearer_token auth")
            configuration.api_key = {"BearerToken": server_config.token}
            configuration.api_key_prefix = {"BearerToken": "Bearer"}
        else:
            if not server_config.kubeconfig_data:
                raise ValueError(
                    "kubeconfig_data is required for kubeconfig auth"
                )
            kubeconfig = yaml.safe_load(server_config.kubeconfig_data)
            await load_kube_config_from_dict(
                kubeconfig, client_configuration=configuration
            )

        return configuration

    async def _create_session(
        self, server_config: KubernetesConfig
    ) -> ApiClient:
        """Create a new Kubernetes API client session."""
        configuration = await self._create_configuration(server_config)
        api_client = ApiClient(configuration=configuration)
        if server_config.auth_type == AuthType.BEARER_TOKEN and server_config.token:
            api_client.set_default_header(
                "Authorization", f"Bearer {server_config.token}"
            )
            logger.info(f"Set Authorization header for {server_config.cluster_url}")
        return api_client

    async def get_session(
        self, server_id: str, server_config: KubernetesConfig
    ) -> ApiClient:
        """Get or create a session for a server."""
        key = server_id
        async with self.lock:
            if key in self.sessions:
                api_client, _, _ = self.sessions.pop(key)
                self.sessions[key] = (
                    api_client,
                    asyncio.get_event_loop().time(),
                    server_config
                )
                logger.debug(f"Reusing session for {server_id}")
                return api_client

            if self.total_sessions >= self.global_max:
                await self.evict_one()

            logger.info(
                f"Creating new session for {server_id}, "
                f"auth_type={server_config.auth_type}, "
                f"has_token={bool(server_config.token)}"
            )
            api_client = await self._create_session(server_config)
            self.sessions[key] = (
                api_client,
                asyncio.get_event_loop().time(),
                server_config
            )
            self.total_sessions += 1
            return api_client

    async def evict_one(self):
        """Evict the least recently used session."""
        if not self.sessions:
            return

        key, (api_client, _, _) = next(iter(self.sessions.items()))
        await api_client.close()
        del self.sessions[key]
        self.total_sessions -= 1
        logger.info(f"Evicted session for server {key}")

    async def cleanup_loop(self):
        """Background task to cleanup idle sessions."""
        await self._cleanup_loop()

    async def _cleanup_loop(self):
        """Background task to cleanup idle sessions."""
        while True:
            await asyncio.sleep(self.idle_ttl / 2)
            now = asyncio.get_event_loop().time()
            async with self.lock:
                for key, (api_client, last_used, _) in list(
                    self.sessions.items()
                ):
                    if now - last_used > self.idle_ttl:
                        await api_client.close()
                        del self.sessions[key]
                        self.total_sessions -= 1
                        logger.info(f"Cleaned up idle session for {key}")

    async def close_session(self, server_id: str) -> bool:
        """Close and remove a session for a specific server."""
        async with self.lock:
            if server_id in self.sessions:
                api_client, _, _ = self.sessions.pop(server_id)
                await api_client.close()
                self.total_sessions -= 1
                logger.info(f"Closed session for server {server_id}")
                return True
            return False

    def _get_namespace(
        self, namespace: Optional[str], config: KubernetesConfig
    ) -> str:
        """Get namespace, falling back to default from config."""
        return namespace or config.default_namespace

    def _serialize_k8s_object(self, obj: Any) -> Dict[str, Any]:
        """Convert Kubernetes object to serializable dict."""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return obj

    async def list_namespaces(
        self, server_id: str, server_config: KubernetesConfig
    ) -> List[Dict[str, Any]]:
        """List all namespaces."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            result = await v1.list_namespace()
            return [self._serialize_k8s_object(ns) for ns in result.items]
        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
            raise

    async def get_namespace(
        self, server_id: str, server_config: KubernetesConfig, name: str
    ) -> Dict[str, Any]:
        """Get a specific namespace."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            result = await v1.read_namespace(name=name)
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get namespace {name}: {e}")
            raise

    async def list_pods(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List pods in a namespace or all namespaces."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await v1.list_namespaced_pod(
                    namespace=namespace, **kwargs
                )
            else:
                result = await v1.list_pod_for_all_namespaces(**kwargs)

            return [self._serialize_k8s_object(pod) for pod in result.items]
        except Exception as e:
            logger.error(f"Failed to list pods: {e}")
            raise

    async def get_pod(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific pod."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await v1.read_namespaced_pod(name=name, namespace=ns)
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get pod {name}: {e}")
            raise

    async def delete_pod(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a pod."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            await v1.delete_namespaced_pod(name=name, namespace=ns)
            return {"status": "deleted", "name": name, "namespace": ns}
        except Exception as e:
            logger.error(f"Failed to delete pod {name}: {e}")
            raise

    async def get_pod_logs(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None,
        container: Optional[str] = None, tail_lines: int = 100,
        previous: bool = False
    ) -> str:
        """Get logs from a pod."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            kwargs = {
                "name": name,
                "namespace": ns,
                "tail_lines": tail_lines,
                "previous": previous
            }
            if container:
                kwargs["container"] = container

            result = await v1.read_namespaced_pod_log(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Failed to get pod logs for {name}: {e}")
            raise

    async def list_deployments(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List deployments."""
        try:
            api_client = await self.get_session(server_id, server_config)
            apps_v1 = client.AppsV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await apps_v1.list_namespaced_deployment(
                    namespace=namespace, **kwargs
                )
            else:
                result = await apps_v1.list_deployment_for_all_namespaces(
                    **kwargs
                )

            return [self._serialize_k8s_object(dep) for dep in result.items]
        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            raise

    async def get_deployment(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific deployment."""
        try:
            api_client = await self.get_session(server_id, server_config)
            apps_v1 = client.AppsV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await apps_v1.read_namespaced_deployment(
                name=name, namespace=ns
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get deployment {name}: {e}")
            raise

    async def create_deployment(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, image: str, namespace: Optional[str] = None,
        replicas: int = 1, port: Optional[int] = None,
        labels: Optional[Dict[str, str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a deployment."""
        try:
            api_client = await self.get_session(server_id, server_config)
            apps_v1 = client.AppsV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            pod_labels = labels or {"app": name}

            container = client.V1Container(
                name=name,
                image=image,
                ports=[
                    client.V1ContainerPort(container_port=port)
                ] if port else None,
                env=[
                    client.V1EnvVar(name=k, value=v)
                    for k, v in (env or {}).items()
                ] or None
            )

            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=pod_labels),
                spec=client.V1PodSpec(containers=[container])
            )

            spec = client.V1DeploymentSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(match_labels=pod_labels),
                template=template
            )

            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=name, labels=pod_labels),
                spec=spec
            )

            result = await apps_v1.create_namespaced_deployment(
                namespace=ns, body=deployment
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to create deployment {name}: {e}")
            raise

    async def update_deployment(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None,
        image: Optional[str] = None, replicas: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update a deployment."""
        try:
            api_client = await self.get_session(server_id, server_config)
            apps_v1 = client.AppsV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            deployment = await apps_v1.read_namespaced_deployment(
                name=name, namespace=ns
            )

            if image:
                deployment.spec.template.spec.containers[0].image = image
            if replicas is not None:
                deployment.spec.replicas = replicas

            result = await apps_v1.replace_namespaced_deployment(
                name=name, namespace=ns, body=deployment
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to update deployment {name}: {e}")
            raise

    async def delete_deployment(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a deployment."""
        try:
            api_client = await self.get_session(server_id, server_config)
            apps_v1 = client.AppsV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            await apps_v1.delete_namespaced_deployment(name=name, namespace=ns)
            return {"status": "deleted", "name": name, "namespace": ns}
        except Exception as e:
            logger.error(f"Failed to delete deployment {name}: {e}")
            raise

    async def scale_deployment(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, replicas: int, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scale a deployment."""
        try:
            api_client = await self.get_session(server_id, server_config)
            apps_v1 = client.AppsV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            scale = await apps_v1.read_namespaced_deployment_scale(
                name=name, namespace=ns
            )
            scale.spec.replicas = replicas
            await apps_v1.replace_namespaced_deployment_scale(
                name=name, namespace=ns, body=scale
            )
            return {"name": name, "namespace": ns, "replicas": replicas}
        except Exception as e:
            logger.error(f"Failed to scale deployment {name}: {e}")
            raise

    async def list_services(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List services."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await v1.list_namespaced_service(
                    namespace=namespace, **kwargs
                )
            else:
                result = await v1.list_service_for_all_namespaces(**kwargs)

            return [self._serialize_k8s_object(svc) for svc in result.items]
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            raise

    async def get_service(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific service."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await v1.read_namespaced_service(name=name, namespace=ns)
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get service {name}: {e}")
            raise

    async def create_service(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, selector: Dict[str, str], port: int,
        namespace: Optional[str] = None, target_port: Optional[int] = None,
        service_type: str = "ClusterIP"
    ) -> Dict[str, Any]:
        """Create a service."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            service = client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1ServiceSpec(
                    selector=selector,
                    ports=[client.V1ServicePort(
                        port=port,
                        target_port=target_port or port
                    )],
                    type=service_type
                )
            )

            result = await v1.create_namespaced_service(
                namespace=ns, body=service
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to create service {name}: {e}")
            raise

    async def delete_service(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a service."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            await v1.delete_namespaced_service(name=name, namespace=ns)
            return {"status": "deleted", "name": name, "namespace": ns}
        except Exception as e:
            logger.error(f"Failed to delete service {name}: {e}")
            raise

    async def list_configmaps(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List ConfigMaps."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await v1.list_namespaced_config_map(
                    namespace=namespace, **kwargs
                )
            else:
                result = await v1.list_config_map_for_all_namespaces(**kwargs)

            return [self._serialize_k8s_object(cm) for cm in result.items]
        except Exception as e:
            logger.error(f"Failed to list configmaps: {e}")
            raise

    async def get_configmap(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific ConfigMap."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await v1.read_namespaced_config_map(
                name=name, namespace=ns
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get configmap {name}: {e}")
            raise

    async def create_configmap(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, data: Dict[str, str], namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a ConfigMap."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            configmap = client.V1ConfigMap(
                api_version="v1",
                kind="ConfigMap",
                metadata=client.V1ObjectMeta(name=name),
                data=data
            )

            result = await v1.create_namespaced_config_map(
                namespace=ns, body=configmap
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to create configmap {name}: {e}")
            raise

    async def delete_configmap(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a ConfigMap."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            await v1.delete_namespaced_config_map(name=name, namespace=ns)
            return {"status": "deleted", "name": name, "namespace": ns}
        except Exception as e:
            logger.error(f"Failed to delete configmap {name}: {e}")
            raise

    async def list_secrets(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List Secrets (metadata only for security)."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await v1.list_namespaced_secret(
                    namespace=namespace, **kwargs
                )
            else:
                result = await v1.list_secret_for_all_namespaces(**kwargs)

            secrets = []
            for secret in result.items:
                s = self._serialize_k8s_object(secret)
                s.pop('data', None)
                secrets.append(s)
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            raise

    async def get_secret(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None, decode: bool = False
    ) -> Dict[str, Any]:
        """Get a specific Secret."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await v1.read_namespaced_secret(name=name, namespace=ns)
            secret = self._serialize_k8s_object(result)

            if decode and secret.get('data'):
                secret['decoded_data'] = {
                    k: base64.b64decode(v).decode('utf-8', errors='replace')
                    for k, v in secret['data'].items()
                }

            return secret
        except Exception as e:
            logger.error(f"Failed to get secret {name}: {e}")
            raise

    async def create_secret(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, data: Dict[str, str], namespace: Optional[str] = None,
        secret_type: str = "Opaque"
    ) -> Dict[str, Any]:
        """Create a Secret."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)

            encoded_data = {
                k: base64.b64encode(v.encode()).decode()
                for k, v in data.items()
            }

            secret = client.V1Secret(
                api_version="v1",
                kind="Secret",
                metadata=client.V1ObjectMeta(name=name),
                type=secret_type,
                data=encoded_data
            )

            result = await v1.create_namespaced_secret(
                namespace=ns, body=secret
            )
            response = self._serialize_k8s_object(result)
            response.pop('data', None)
            return response
        except Exception as e:
            logger.error(f"Failed to create secret {name}: {e}")
            raise

    async def delete_secret(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a Secret."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            await v1.delete_namespaced_secret(name=name, namespace=ns)
            return {"status": "deleted", "name": name, "namespace": ns}
        except Exception as e:
            logger.error(f"Failed to delete secret {name}: {e}")
            raise

    async def list_pvcs(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List PersistentVolumeClaims."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await v1.list_namespaced_persistent_volume_claim(
                    namespace=namespace, **kwargs
                )
            else:
                func = v1.list_persistent_volume_claim_for_all_namespaces
                result = await func(**kwargs)

            return [self._serialize_k8s_object(pvc) for pvc in result.items]
        except Exception as e:
            logger.error(f"Failed to list PVCs: {e}")
            raise

    async def get_pvc(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific PersistentVolumeClaim."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await v1.read_namespaced_persistent_volume_claim(
                name=name, namespace=ns
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get PVC {name}: {e}")
            raise

    async def list_ingresses(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, label_selector: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List Ingresses."""
        try:
            api_client = await self.get_session(server_id, server_config)
            networking_v1 = client.NetworkingV1Api(api_client)

            kwargs = {"limit": limit}
            if label_selector:
                kwargs["label_selector"] = label_selector

            if namespace:
                result = await networking_v1.list_namespaced_ingress(
                    namespace=namespace, **kwargs
                )
            else:
                result = await networking_v1.list_ingress_for_all_namespaces(
                    **kwargs
                )

            return [self._serialize_k8s_object(ing) for ing in result.items]
        except Exception as e:
            logger.error(f"Failed to list ingresses: {e}")
            raise

    async def get_ingress(
        self, server_id: str, server_config: KubernetesConfig,
        name: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a specific Ingress."""
        try:
            api_client = await self.get_session(server_id, server_config)
            networking_v1 = client.NetworkingV1Api(api_client)
            ns = self._get_namespace(namespace, server_config)
            result = await networking_v1.read_namespaced_ingress(
                name=name, namespace=ns
            )
            return self._serialize_k8s_object(result)
        except Exception as e:
            logger.error(f"Failed to get ingress {name}: {e}")
            raise

    async def list_events(
        self, server_id: str, server_config: KubernetesConfig,
        namespace: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List events."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.CoreV1Api(api_client)

            if namespace:
                result = await v1.list_namespaced_event(
                    namespace=namespace, limit=limit
                )
            else:
                result = await v1.list_event_for_all_namespaces(limit=limit)

            return [
                self._serialize_k8s_object(event) for event in result.items
            ]
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            raise

    async def test_connection(
        self, server_id: str, server_config: KubernetesConfig
    ) -> Dict[str, Any]:
        """Test the connection to the Kubernetes cluster."""
        try:
            api_client = await self.get_session(server_id, server_config)
            v1 = client.VersionApi(api_client)
            version_info = await v1.get_code()

            core_v1 = client.CoreV1Api(api_client)
            await core_v1.list_namespace(limit=1)

            return {
                "status": "connected",
                "connected": True,
                "cluster_url": server_config.cluster_url,
                "auth_type": server_config.auth_type.value,
                "kubernetes_version": {
                    "major": version_info.major,
                    "minor": version_info.minor,
                    "git_version": version_info.git_version,
                    "platform": version_info.platform
                },
                "default_namespace": server_config.default_namespace
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "error",
                "connected": False,
                "cluster_url": server_config.cluster_url,
                "auth_type": server_config.auth_type.value,
                "error": str(e)
            }
