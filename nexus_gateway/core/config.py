from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "NexusGateway"
    redis_url: str = "redis://localhost:6379"
    vllm_nodes: str = "http://node1:8000,http://node2:8000"
    rate_limit_rpm: int = 600
    
    @property
    def vllm_node_list(self) -> list[str]:
        return [node.strip() for node in self.vllm_nodes.split(",")]

settings = Settings()
