# 🌌 NexusGateway: High-Throughput Semantic Load Balancer for vLLM

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NexusGateway** is an enterprise-grade, blazing-fast API gateway built in FastAPI to act as a front-end router for distributed [vLLM](https://github.com/vllm-project/vllm) or Ray Serve clusters. 

It solves one of the hardest problems in distributed LLM serving: **KV Cache Fragmentation**.

## 🧠 The Problem
When you run multiple vLLM worker nodes behind a standard Round-Robin load balancer (like NGINX or HAProxy), requests with identical system prompts (e.g. 5,000 tokens of RAG context) are randomly sprayed across your cluster. This forces *every* GPU to redundantly re-compute and store the exact same KV cache, destroying VRAM efficiency and causing Out-Of-Memory (OOM) errors.

## 🚀 The Solution: KV-Aware Routing
NexusGateway intercepts OpenAI-compatible `/v1/chat/completions` requests, semantically hashes the system prefix, and deterministically routes the request to the specific worker node that already holds the context in its KV cache. 

### Key Features
- **Deterministic Prefix Routing**: Uses `xxhash` for ultra-low latency routing, achieving near 100% KV Cache Hit Rates for shared contexts.
- **Asynchronous Pipelining**: Built on `uvloop` and `httpx`, capable of handling thousands of concurrent streaming connections with <2ms overhead.
- **Redis Rate Limiting**: Distributed, sliding-window rate limiting natively integrated to prevent tenant abuse.
- **OpenAI Compatible**: Fully transparent proxy. Drop-in replacement for any OpenAI client.

## 🏗️ Architecture

```mermaid
graph TD
    Client1[Client A (Prompt X)] --> Gateway[NexusGateway]
    Client2[Client B (Prompt Y)] --> Gateway
    Client3[Client C (Prompt X)] --> Gateway
    
    Gateway -->|Hash(Prompt X) routes to| Node1[vLLM Node 1]
    Gateway -->|Hash(Prompt Y) routes to| Node2[vLLM Node 2]
    
    Node1 -->|KV Cache Hit!| VRAM1[(GPU VRAM)]
    Node2 -->|KV Cache Miss/Compute| VRAM2[(GPU VRAM)]
```

## 🛠️ Getting Started

### 1. Installation
```bash
git clone https://github.com/yourusername/NexusGateway.git
cd NexusGateway
pip install -r requirements.txt
```

### 2. Configuration
Export your backend nodes:
```bash
export VLLM_NODES="http://10.0.0.1:8000,http://10.0.0.2:8000"
export REDIS_URL="redis://localhost:6379"
```

### 3. Run
```bash
docker-compose up -d
```
Your cluster is now protected by NexusGateway at `http://localhost:8000`.

## 🤝 Contributing
Contributions are welcome! If you're building heavily cached autonomous agents or multi-tenant LLM platforms, I'd love to chat.
