import xxhash
from typing import List
from nexus_gateway.core.config import settings

class KVCacheAwareBalancer:
    """
    Implements a custom prefix-aware routing algorithm.
    By hashing the beginning of the prompt (the system prompt / few-shot examples),
    we deterministically route requests sharing the same prefix to the exact same 
    vLLM worker node. This guarantees a near 100% KV-cache hit rate for shared contexts
    in production environments, eliminating duplicate prompt processing.
    """
    def __init__(self, nodes: List[str]):
        self.nodes = nodes
        self.num_nodes = len(nodes)

    def _get_prefix_hash(self, text: str, prefix_length: int = 500) -> int:
        """
        Hashes the first `prefix_length` characters of the text.
        xxhash is extremely fast and collision-resistant for this purpose.
        """
        prefix = text[:prefix_length]
        return xxhash.xxh64(prefix.encode('utf-8')).intdigest()

    def get_node(self, prompt: str) -> str:
        """
        Returns the optimal vLLM node URL for the given prompt.
        """
        if not self.nodes:
            raise ValueError("No vLLM nodes available.")
        
        # Consistent hashing for prefix
        hash_val = self._get_prefix_hash(prompt)
        node_idx = hash_val % self.num_nodes
        return self.nodes[node_idx]

# Global instance
balancer = KVCacheAwareBalancer(settings.vllm_node_list)
