import subprocess
import time
import requests
import os
import sys
import datetime
import signal
import psutil

class VLLMServerConda:
    def __init__(self, model_name, model_path, log_file_path, conda_env_name="vllm", host="0.0.0.0", port=8002, cuda_visible_devices="1"):
        self.model_name = model_name
        self.model_path = model_path
        self.conda_env_name = conda_env_name
        self.host = host
        self.port = port
        self.cuda_visible_devices = cuda_visible_devices
        self.process = None
        self.log_file_path = log_file_path
        self.log_file_handle = None
        
        # Detect conda installation
        self.conda_base = "/home/user/miniconda3"
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
        
        # Create log file path
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        self.log_file_path = os.path.join(logs_dir, f"vllm_{timestamp}.log")
    
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
        
        # Open log file for writing
        self.log_file_handle = open(self.log_file_path, 'w', buffering=1)  # Line buffered
        
        # Write initial info to log file
        self.log_file_handle.write(f"=== vLLM Server Started at {datetime.datetime.now()} ===\n")
        self.log_file_handle.write(f"Model: {self.model_name}\n")
        self.log_file_handle.write(f"Model path: {self.model_path}\n")
        self.log_file_handle.write(f"Host: {self.host}\n")
        self.log_file_handle.write(f"Port: {self.port}\n")
        self.log_file_handle.write(f"CUDA devices: {self.cuda_visible_devices}\n")
        self.log_file_handle.write(f"Command: {' '.join(cmd)}\n")
        self.log_file_handle.write("=" * 50 + "\n\n")
        
        print(f"Starting vLLM server from conda env '{self.conda_env_name}'")
        print(f"Command: {' '.join(cmd)}")
        print(f"Logging to: {self.log_file_path}")
        
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=self.log_file_handle,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout so all output goes to log
            text=True,
            start_new_session=True  # Create new process group for proper cleanup
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
        """Stop the server and all related processes"""
        if not self.process:
            print("No process to stop")
            return
        
        print("Stopping vLLM server...")
        
        try:
            # Get the process group ID
            pgid = os.getpgid(self.process.pid)
            
            # First, try graceful termination of the entire process group
            print(f"Terminating process group {pgid}...")
            os.killpg(pgid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=15)
                print("✓ Server gracefully stopped")
            except subprocess.TimeoutExpired:
                print("Graceful shutdown timed out, force killing...")
                
                # Force kill the entire process group
                try:
                    os.killpg(pgid, signal.SIGKILL)
                    self.process.wait(timeout=10)
                    print("✓ Server force killed")
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    print("⚠ Process group already terminated or unresponsive")
        
        except (ProcessLookupError, OSError) as e:
            # Process might already be dead
            print(f"Process cleanup: {e}")
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        
        # Additional cleanup: kill any remaining vLLM processes on this port
        self._cleanup_port_processes()
        
        # GPU memory cleanup
        self._cleanup_gpu_memory()
        
        # Verify port is available
        self._verify_port_available()
        
        # Close log file handle if open
        if self.log_file_handle and not self.log_file_handle.closed:
            self.log_file_handle.write(f"\n=== vLLM Server Stopped at {datetime.datetime.now()} ===\n")
            self.log_file_handle.close()
    
    def _cleanup_port_processes(self):
        """Kill any processes still using our port"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                    try:
                        proc = psutil.Process(conn.pid)
                        if 'vllm' in proc.name().lower() or 'python' in proc.name().lower():
                            print(f"Killing process {conn.pid} using port {self.port}")
                            proc.terminate()
                            try:
                                proc.wait(timeout=5)
                            except psutil.TimeoutExpired:
                                proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except Exception as e:
            print(f"Port cleanup warning: {e}")
    
    def _cleanup_gpu_memory(self):
        """Clear GPU memory allocated by this process"""
        if self.cuda_visible_devices:
            try:
                # Use nvidia-smi to reset GPU memory if available
                result = subprocess.run(
                    ['nvidia-smi', '--gpu-reset', '-i', str(self.cuda_visible_devices)],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    print(f"✓ GPU {self.cuda_visible_devices} memory cleared")
                else:
                    print(f"GPU reset warning: {result.stderr}")
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                print(f"GPU cleanup warning: {e}")
    
    def _verify_port_available(self):
        """Verify that the port is now available"""
        try:
            # Try to connect to the port to see if anything is still listening
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                print(f"⚠ Warning: Port {self.port} still appears to be in use")
            else:
                print(f"✓ Port {self.port} is now available")
        except Exception as e:
            print(f"Port verification warning: {e}")
    
    def get_logs(self):
        """Get server logs from log file"""
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r') as f:
                    content = f.read()
                return content, None
            except Exception as e:
                return None, f"Error reading log file: {str(e)}"
        return None, "No log file available"
    
    def get_log_file_path(self):
        """Get the path to the log file"""
        return self.log_file_path
    
    def get_recent_logs(self, lines=50):
        """Get the last N lines from the log file"""
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    return ''.join(recent_lines), None
            except Exception as e:
                return None, f"Error reading log file: {str(e)}"
        return None, "No log file available"
    
    def is_running(self):
        """Check if the server process is still running"""
        if not self.process:
            return False
        return self.process.poll() is None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        # Ensure log file is properly closed
        if self.log_file_handle and not self.log_file_handle.closed:
            self.log_file_handle.close()


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
