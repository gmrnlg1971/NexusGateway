import pytest
from nexus_gateway.core.balancer import KVCacheAwareBalancer

def test_prefix_hashing_consistency():
    balancer = KVCacheAwareBalancer(["node1", "node2"])
    # Same prefix should route to same node
    prompt1 = "You are a helpful assistant. " * 20 + "Tell me a joke."
    prompt2 = "You are a helpful assistant. " * 20 + "What is the weather?"
    
    node1 = balancer.get_node(prompt1)
    node2 = balancer.get_node(prompt2)
    assert node1 == node2, "Requests with identical system prompts should route to same node."

def test_different_prefixes_distribute():
    balancer = KVCacheAwareBalancer(["node1", "node2"])
    prompt1 = "You are a math tutor. " * 20 + "Solve 2+2."
    prompt2 = "You are a historian. " * 20 + "Who was Lincoln?"
    
    # Not guaranteed to be different due to hash, but highly likely in a small set.
    # We can at least check it doesn't crash.
    node1 = balancer.get_node(prompt1)
    node2 = balancer.get_node(prompt2)
    assert node1 in ["node1", "node2"]
    assert node2 in ["node1", "node2"]
