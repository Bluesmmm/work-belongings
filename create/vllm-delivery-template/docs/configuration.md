# Configuration Reference

Complete reference for `serving/config.yaml` and all vLLM engine parameters.

## Basic Configuration

### model (required)

The HuggingFace model identifier to serve.

```yaml
model: "Qwen/Qwen2.5-3B-Instruct"
```

**Examples:**
- `Qwen/Qwen2.5-3B-Instruct` - 3B model
- `Qwen/Qwen2.5-7B-Instruct` - 7B model
- `meta-llama/Llama-3.2-3B-Instruct` - Meta's 3B model
- `/path/to/local/model` - Local model path

### port

Server port for the API. Default: `8000`

```yaml
port: 8000
```

### api_key

API key for authentication. Default: `token-abc123`

```yaml
api_key: "your-secure-api-key"
```

**Security tip:** Change this in production and use environment variables.

## Engine Configuration

### dtype

Data type for model weights. Default: `auto`

```yaml
dtype: "auto"  # or "half", "bfloat16", "float32"
```

**Options:**
- `auto` - Automatically choose based on GPU
- `half` / `float16` - 16-bit floating point
- `bfloat16` - Brain floating point (recommended for newer GPUs)
- `float32` - 32-bit floating point (slower, more precise)

### gpu_memory_utilization

Fraction of GPU memory to use. Range: `0.0` - `1.0`. Default: `0.9`

```yaml
gpu_memory_utilization: 0.9
```

**Tips:**
- Set to `0.7` if running out of memory
- Set to `0.95` for maximum utilization
- Leave headroom for other processes

### max_model_len

Maximum sequence length (tokens). Default: `8192`

```yaml
max_model_len: 8192
```

**Model-specific limits:**
- Qwen2.5-3B: up to 32768
- Reduce if running out of memory

## Advanced Configuration

### tensor_parallel_size

Number of GPUs for tensor parallelism. Default: `1`

```yaml
tensor_parallel_size: 1  # Use 2 for 2 GPUs, 4 for 4 GPUs
```

### block_size

Size of KV cache blocks. Default: `16`

```yaml
block_size: 16
```

**Leave as default** unless you know what you're doing.

### swap_space

GPU swap space in GB for CPU offloading. Default: `0`

```yaml
swap_space: 4  # Use 4GB of CPU RAM for KV cache
```

**Use when:** GPU memory is limited and you can tolerate slower inference.

### max_num_batched_tokens

Maximum number of tokens batched. Default: `8192`

```yaml
max_num_batched_tokens: 8192
```

**Increase for:** Higher throughput with many concurrent requests.

### max_num_seqs

Maximum number of sequences in a batch. Default: `256`

```yaml
max_num_seqs: 256
```

**Decrease if:** Running out of memory during high concurrency.

### enforce_eager

Disable CUDA graph compilation and use eager mode. Default: `false`

```yaml
enforce_eager: false  # Set to true to disable CUDA graphs
```

**Use when:** Debugging or if CUDA graph compilation fails. Note: This will reduce performance.

## CLI Overrides

Override any config value with command-line arguments:

```bash
python serving/launch.py --port 9000
python serving/launch.py --gpu-memory-utilization 0.8 --max-model-len 4096
```

## Environment Variables

Set configuration via environment variables:

```bash
export VLLM_MODEL_ID="Qwen/Qwen2.5-7B-Instruct"
export VLLM_PORT=9000
export VLLM_API_KEY="your-key"
```

Then modify `serving/launch.py` to read from environment.

## Example Configurations

### Development (3B Model)

```yaml
model: "Qwen/Qwen2.5-3B-Instruct"
port: 8000
gpu_memory_utilization: 0.8
max_model_len: 4096
```

### Production (7B Model)

```yaml
model: "Qwen/Qwen2.5-7B-Instruct"
port: 8000
gpu_memory_utilization: 0.95
max_model_len: 8192
tensor_parallel_size: 1
api_key: "your-production-api-key"
```

### Multi-GPU (Large Model)

```yaml
model: "meta-llama/Llama-3.1-70B-Instruct"
port: 8000
gpu_memory_utilization: 0.95
max_model_len: 8192
tensor_parallel_size: 4  # Requires 4 GPUs
```

## Reference Links

- [vLLM Engine Arguments](https://docs.vllm.ai/en/latest/configuration/engine_args/)
- [vLLM Serving Guide](https://docs.vllm.ai/en/latest/serving/)
- [OpenAI API Compatibility](https://docs.vllm.ai/en/latest/serving/openai_compatible_server/)
