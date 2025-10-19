from unsloth import FastLanguageModel, FastModel
import torch
# from trl import SFTTrainer, SFTConfig
from trl import DPOConfig, DPOTrainer
from datasets import load_dataset
import datetime
from peft import PeftModel
import os
import gc

max_seq_length = 1024 # Supports RoPE Scaling internally, so choose any!
dataset = load_dataset("trl-lib/ultrafeedback_binarized", split = "train[:1000]")
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_dir = f"outputs/{timestamp}"
# dataset = load_dataset("imdb", split="train[:1000]")
# eval_dataset = load_dataset("trl-lib/ultrafeedback_binarized", split = "test")
# eval_dataset = load_dataset("imdb", split="test[:1000]")


# 4bit pre quantized models we support for 4x faster downloading + no OOMs.
# fourbit_models = [
#     "unsloth/gpt-oss-20b-unsloth-bnb-4bit", #or choose any model

# ] # More models at https://huggingface.co/unsloth

# Clear any cached memory before starting
torch.cuda.empty_cache()
gc.collect()

model, tokenizer = FastModel.from_pretrained(
    model_name="Qwen/Qwen3-Coder-30B-A3B-Instruct",
    max_seq_length=max_seq_length,
    load_in_4bit=True,
    load_in_8bit=False,
    load_in_16bit=False,
    full_finetuning=False,
)

model: PeftModel = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
    max_seq_length=max_seq_length,
    use_rslora=False,
    loftq_config=None,
)

trainer = DPOTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    args=DPOConfig(
        max_seq_length=max_seq_length,
        
        # VRAM optimization: Increase batch size, reduce gradient accumulation
        per_device_train_batch_size=8,  # Increased from 8
        gradient_accumulation_steps=1,
        
        # Reduce memory from optimizer
        optim="adamw_8bit",  # Good choice, keep this
        
        # DataLoader optimization
        dataloader_num_workers=2,  # Reduced from 4 to save memory
        dataloader_pin_memory=False,  # Disable pinned memory
        
        # Gradient settings for better GPU utilization
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        
        # Reduce checkpoint frequency to avoid memory fragmentation
        save_strategy="steps",
        save_steps=5,  # Changed from 1 to 5
        save_only_model=True,
        save_total_limit=2,  # Only keep 2 most recent checkpoints
        
        # Mixed precision for better GPU utilization
        bf16=True,  # Use BF16 on H100 for better performance
        fp16=False,
        
        # Logging
        logging_steps=1,
        report_to="wandb",
        
        # Training params
        warmup_steps=0,
        max_steps=3,
        learning_rate=1e-5,
        seed=3407,
        
        # DPO-specific: Reduce reference model memory
        beta=0.1,  # DPO beta parameter
        generate_during_eval=False,  # Disable generation during eval
        
        # Memory cleanup
        ddp_find_unused_parameters=False,
    ),
)

# Enable torch.compile for better GPU utilization (PyTorch 2.0+)
# model = torch.compile(model)  # Uncomment if using PyTorch 2.0+

trainer.train()

# Path where the fused model will be saved
fused_model_dir = os.path.join(output_dir, "fused_model")
os.makedirs(fused_model_dir, exist_ok=True)

if isinstance(model, PeftModel):
    print("Merging LoRA weights into the base model...")
    
    # Use safe merging that handles MoE properly
    fused_model = model.merge_and_unload(
        progressbar=True,
        safe_merge=True  # This helps with MoE models
    )
    
    # Ensure all state dict keys are present
    state_dict = fused_model.state_dict()
    print(f"Total parameters in fused model: {len(state_dict)}")
else:
    fused_model = model

# Save with explicit configuration
print(f"Saving fused model to {fused_model_dir}...")
fused_model.save_pretrained(
    fused_model_dir,
    safe_serialization=True,
    max_shard_size="5GB"
)
tokenizer.save_pretrained(fused_model_dir)

# Go to https://docs.unsloth.ai for advanced tips like
# (1) Saving to GGUF / merging to 16bit for vLLM
# (2) Continued training from a saved LoRA adapter
# (3) Adding an evaluation loop / OOMs
# (4) Customized chat templates