import subprocess
import time
import os
import sys
import datetime
from pathlib import Path

class TrainingManagerConda:
    def __init__(self, dataset_name, log_file_path, model_name=None, conda_env_name="cuda_unsloth", cuda_visible_devices="2", script_path="ab-test-rlhf/dpo_lora.py"):
        self.dataset_name = dataset_name
        self.model_name = model_name
        self.conda_env_name = conda_env_name
        self.cuda_visible_devices = cuda_visible_devices
        self.script_path = script_path
        self.process = None
        self.start_time = None
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
        
        # Verify script exists
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Training script not found at {self.script_path}")
        
        # if log_file
        #     # Create log file path
        #     timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        #     logs_dir = os.path.join(os.getcwd(), "logs")
        #     os.makedirs(logs_dir, exist_ok=True)
        #     self.log_file_path = os.path.join(logs_dir, f"training_{timestamp}.log")
    
    def get_python_path(self):
        """Get path to python executable in conda environment"""
        python_path = f"{self.conda_base}/envs/{self.conda_env_name}/bin/python"
        if not os.path.exists(python_path):
            raise FileNotFoundError(f"Python not found at {python_path}")
        return python_path
    
    def start(self):
        """Start the training process"""
        python_path = self.get_python_path()
        
        cmd = [python_path, self.script_path]
        
        # Add required arguments
        cmd.extend(["--dataset-name", self.dataset_name])
        
        if self.model_name:
            cmd.extend(["--model-name", self.model_name])
        
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
        self.log_file_handle.write(f"=== Training Started at {datetime.datetime.now()} ===\n")
        self.log_file_handle.write(f"Dataset: {self.dataset_name}\n")
        self.log_file_handle.write(f"Model name: {self.model_name}\n")
        self.log_file_handle.write(f"CUDA devices: {self.cuda_visible_devices}\n")
        self.log_file_handle.write(f"Command: {' '.join(cmd)}\n")
        self.log_file_handle.write("=" * 50 + "\n\n")
        
        print(f"Starting DPO training from conda env '{self.conda_env_name}'")
        print(f"Dataset: {self.dataset_name}")
        print(f"Model name: {self.model_name}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Logging to: {self.log_file_path}")
        
        self.process = subprocess.Popen(
            cmd,
            env=env,
            stdout=self.log_file_handle,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout so all output goes to log
            text=True,
            cwd=os.getcwd()  # Ensure we're in the project root
        )
        
        self.start_time = time.time()
        print(f"✓ Training process started with PID: {self.process.pid}")
        
    def is_running(self):
        """Check if the training process is still running"""
        if not self.process:
            return False
        return self.process.poll() is None
    
    def wait_for_completion(self, timeout=None):
        """Wait for training to complete"""
        if not self.process:
            raise RuntimeError("No training process started")
        
        print("Waiting for training to complete...")
        try:
            stdout, stderr = self.process.communicate(timeout=timeout)
            
            if self.process.returncode == 0:
                elapsed_time = time.time() - self.start_time if self.start_time else 0
                print(f"✓ Training completed successfully in {elapsed_time:.1f} seconds")
                return True, stdout, stderr
            else:
                print(f"✗ Training failed with return code: {self.process.returncode}")
                return False, stdout, stderr
                
        except subprocess.TimeoutExpired:
            print(f"Training exceeded timeout of {timeout} seconds")
            return False, None, None
    
    def get_status(self):
        """Get current status of the training process"""
        if not self.process:
            return "not_started"
        
        poll_result = self.process.poll()
        if poll_result is None:
            elapsed_time = time.time() - self.start_time if self.start_time else 0
            return f"running (PID: {self.process.pid}, elapsed: {elapsed_time:.1f}s)"
        elif poll_result == 0:
            return "completed_successfully"
        else:
            return f"failed (return code: {poll_result})"
    
    def stop(self):
        """Stop the training process"""
        if self.process and self.is_running():
            print("Stopping training process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=30)
                print("✓ Training process stopped")
            except subprocess.TimeoutExpired:
                print("Force killing training process...")
                self.process.kill()
                self.process.wait()
                print("✓ Training process force killed")
        
        # Close log file handle if open
        if self.log_file_handle and not self.log_file_handle.closed:
            self.log_file_handle.write(f"\n=== Training Stopped at {datetime.datetime.now()} ===\n")
            self.log_file_handle.close()
    
    def get_logs(self):
        """Get training logs from log file"""
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
    
    def get_output_directory(self):
        """Get the expected output directory for the trained model"""
        if self.model_name:
            return f"outputs/{self.model_name}"
        else:
            # If no model name specified, it uses timestamp format
            # We can't predict the exact timestamp, but we can check the outputs directory
            return "outputs"
    
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
        # Example with specific model name
        with TrainingManagerConda(
            dataset_name="BOSSrobot343/dubhacks-buy_button",
            model_name="my_custom_model",
            cuda_visible_devices="2"  # Use GPU 0
        ) as trainer:
            trainer.start()
            
            # Option 1: Wait for completion with timeout
            success, stdout, stderr = trainer.wait_for_completion(timeout=3600)  # 1 hour timeout
            
            if success:
                print(f"Training output directory: {trainer.get_output_directory()}")
                print("Training logs available via trainer.get_logs()")
            else:
                print("Training failed!")
                if stderr:
                    print(f"Error output: {stderr}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if 'trainer' in locals():
            status = trainer.get_status()
            print(f"Training status: {status}")
            stdout, stderr = trainer.get_logs()
            if stderr and stderr != "Training still in progress...":
                print(f"Training logs:\n{stderr}", file=sys.stderr)
