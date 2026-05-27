from vastai import VastAI

from cloudcat.providers.base import Provider


class VastAIProvider(Provider):
    def __init__(self, api_key: str):
        self.vast = VastAI(api_key=api_key)

    def search_offers(
        self,
        gpu_names: list[str] | None,
        num_gpus: int | None,
        limit: int,
    ) -> list[dict]:
        query_parts = ["gpu_arch=nvidia", "gpu_frac=1.0","reliability>=0.9","verified=true","rentable=true", "direct_port_count>=1", "disk_space>=20"]
        # query_parts = []
        
        if gpu_names:
            if len(gpu_names) == 1:
                query_parts.append(f"gpu_name={gpu_names[0]}")
            else:
                query_parts.append(f"gpu_name in [{','.join(gpu_names)}]")
        if num_gpus:
            query_parts.append(f"num_gpus>={num_gpus}")
        query = " ".join(query_parts)
        order = "dph_total"
        
        offers = self.vast.search_offers(type="on-demand", query=query, order=order, limit=limit, no_default=True) or []
        # print(offers)
        return offers

    def create_instance(
        self,
        offer_id: int,
        template_id: str,
        label: str,
    ) -> str:
        raise NotImplementedError("create_instance is not implemented yet")

    def wait_for_ready(self, instance_id: str, timeout: int) -> bool:
        raise NotImplementedError("wait_for_ready is not implemented yet")

    def list_instances(self, label_prefix: str | None = None) -> list[dict]:
        instances = self.vast.show_instances() or []
        if label_prefix is not None:
            instances = [
                i for i in instances
                if (i.get("label") or "").startswith(label_prefix)
            ]
        return instances

    def get_ssh_info(self, instance_id: str) -> tuple[str, int]:
        raise NotImplementedError("get_ssh_info is not implemented yet")

    def pull_files(
        self,
        instance_id: str,
        remote_paths: list[str],
        local_dir: str,
    ) -> None:
        raise NotImplementedError("pull_files is not implemented yet")

    def destroy_instance(self, instance_id: str) -> None:
        raise NotImplementedError("destroy_instance is not implemented yet")
