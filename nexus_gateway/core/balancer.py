import xxhash # type: ignore
from typing import List, Dict
from bisect import bisect
from nexus_gateway.core.config import settings

class KVCacheAwareBalancer:
    """
    Implements a custom prefix-aware routing algorithm using a Consistent Hashing Ring.
    By hashing the system prompt / few-shot examples, we deterministically route 
    requests sharing the same prefix to the exact same vLLM worker node.
    A consistent hash ring ensures minimal disruption to existing caches when
    scaling cluster size up or down.
    """
    def __init__(self, nodes: List[str], vnodes: int = 100) -> None:
        """
        Initializes the consistent hashing ring for routing requests.
        
        Args:
            nodes: List of backend vLLM node URLs.
            vnodes: Number of virtual nodes per physical node.
        """
        self.nodes: List[str] = nodes
        self.vnodes: int = vnodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        
        if nodes:
            self._build_ring()

    def _build_ring(self) -> None:
        """
        Builds the consistent hash ring by placing virtual nodes.
        """
        for node in self.nodes:
            for i in range(self.vnodes):
                vnode_key = f"{node}:{i}"
                hash_val = xxhash.xxh64(vnode_key.encode('utf-8')).intdigest()
                self.ring[hash_val] = node
                self.sorted_keys.append(hash_val)
        self.sorted_keys.sort()

    def _get_prefix_hash(self, text: str) -> int:
        """
        Hashes the full text. Prefix isolation is now handled in the router.
        """
        return xxhash.xxh64(text.encode('utf-8')).intdigest()

    def get_node(self, prompt: str) -> str:
        """
        Returns the optimal vLLM node URL for the given prompt using the ring.
        """
        if not self.nodes:
            raise ValueError("No vLLM nodes available.")
        
        hash_val = self._get_prefix_hash(prompt)
        idx = bisect(self.sorted_keys, hash_val)
        if idx == len(self.sorted_keys):
            idx = 0
        return self.ring[self.sorted_keys[idx]]

# Global instance
balancer = KVCacheAwareBalancer(settings.vllm_node_list)
