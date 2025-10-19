import subprocess
import time
import requests
import os
import sys

class VLLMServerConda:
    def __init__(self, model_name, model_path, conda_env_name, host="0.0.0.0", port=8001, cuda_visible_devices=None):
        self.model_name = model_name
        self.model_path = model_path
        self.conda_env_name = conda_env_name
        self.host = host
        self.port = port
        self.cuda_visible_devices = cuda_visible_devices
        self.process = None
        
        # Detect conda installation
        self.conda_base = os.environ.get('CONDA_PREFIX')
        if not self.conda_base:
            # Try common locations
            for path in [os.path.expanduser('~/anaconda3'), 
                        os.path.expanduser('~/miniconda3'),
                        '/opt/conda']:
                if os.path.exists(path):
                    self.conda_base = path
                    break
        
        if not self.conda_base:
            raise RuntimeError("Could not find conda installation")
    
    def get_vllm_path(self):
        """Get path to vllm executable in conda environment"""
        vllm_path = f"{self.conda_base}/envs/{self.conda_env_name}/bin/vllm"
        if not os.path.exists(vllm_path):
            raise FileNotFoundError(f"vLLM not found at {vllm_path}")
        return vllm_path
    
    def start(self, **kwargs):
        """Start the vLLM server"""
        vllm_path = self.get_vllm_path()
        
        cmd = [
            vllm_path, "serve", self.model_path,
            "--host", self.host,
            "--port", str(self.port),
            "--served-model-name", self.model_name
        ]
        
        # Add optional arguments
        for key, value in kwargs.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])
        
        # Set up environment with conda paths
        env = os.environ.copy()
        conda_bin = f"{self.conda_base}/envs/{self.conda_env_name}/bin"
        env['PATH'] = f"{conda_bin}:{env.get('PATH', '')}"
        env['CONDA_DEFAULT_ENV'] = self.conda_env_name
        env['CONDA_PREFIX'] = f"{self.conda_base}/envs/{self.conda_env_name}"
        
        # Set CUDA_VISIBLE_DEVICES if specified
        if self.cuda_visible_devices is not None:
            env['CUDA_VISIBLE_DEVICES'] = str(self.cuda_visible_devices)
            print(f"Setting CUDA_VISIBLE_DEVICES={self.cuda_visible_devices}")
        
        print(f"Starting vLLM server from conda env '{self.conda_env_name}'")
        print(f"Command: {' '.join(cmd)}")
        
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        self.wait_for_ready()
        
    def wait_for_ready(self, timeout=300):
        """Wait for server to be ready"""
        start_time = time.time()
        url = f"http://{self.host}:{self.port}/health"
        
        print("Waiting for server to be ready...")
        while time.time() - start_time < timeout:
            # Check if process died
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(f"Server process died. stderr: {stderr}")
            
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    print("✓ Server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        
        raise TimeoutError("Server failed to start within timeout period")
    
    def stop(self):
        """Stop the server"""
        if self.process:
            print("Stopping vLLM server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=30)
                print("✓ Server stopped")
            except subprocess.TimeoutExpired:
                print("Force killing server...")
                self.process.kill()
                self.process.wait()
    
    def get_logs(self):
        """Get server logs"""
        if self.process:
            return self.process.stdout.read(), self.process.stderr.read()
        return None, None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Usage example
if __name__ == "__main__":
    try:
        with VLLMServerConda(
            model_name="qwen3-lora",
            model_path="/home/user/projects/DubHacks2025/outputs/2025-10-19_07-25-50/fused_model",
            conda_env_name="vllm",  # Your conda environment name
            port=8001,
            cuda_visible_devices="1"  # Example: use GPU 0 only
        ) as server:
            server.start(
                tensor_parallel_size=1,
                gpu_memory_utilization=0.9
            )
            # Test the server
            response = requests.post(
                f"http://localhost:8000/v1/completions",
                headers={
                    "Authorization": "Bearer 4321"
                },
                json={
                    "model": "qwen3-lora",
                    "prompt": "Hello, world!",
                    "max_tokens": 50
                }
            )
            print("\nResponse:", response.json())
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if 'server' in locals():
            stdout, stderr = server.get_logs()
            if stderr:
                print(f"Server logs:\n{stderr}", file=sys.stderr)
