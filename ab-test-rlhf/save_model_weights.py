from huggingface_hub import snapshot_download

model_id = "Qwen/Qwen3-Coder-30B-A3B-Instruct"  # Replace with the ID of the model you want to download
snapshot_download(repo_id=model_id, local_dir="/home/user/projects/llama.cpp/hf_models")