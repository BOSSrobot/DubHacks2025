from unsloth import FastLanguageModel, FastModel
import torch
# from trl import SFTTrainer, SFTConfig
from trl import DPOConfig, DPOTrainer
from datasets import load_dataset

max_seq_length = 1024 # Supports RoPE Scaling internally, so choose any!
dataset = load_dataset("trl-lib/ultrafeedback_binarized", split = "train[:1000]")
# dataset = load_dataset("imdb", split="train[:1000]")
# eval_dataset = load_dataset("trl-lib/ultrafeedback_binarized", split = "test")
# eval_dataset = load_dataset("imdb", split="test[:1000]")


# 4bit pre quantized models we support for 4x faster downloading + no OOMs.
# fourbit_models = [
#     "unsloth/gpt-oss-20b-unsloth-bnb-4bit", #or choose any model

# ] # More models at https://huggingface.co/unsloth

model, tokenizer = FastModel.from_pretrained(
    model_name = "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    max_seq_length = max_seq_length, # Choose any for long context!
    load_in_4bit = True,  # 4-bit quantization. False = 16-bit LoRA.
    load_in_8bit = False, # 8-bit quantization
    load_in_16bit = False, # [NEW!] 16-bit LoRA
    full_finetuning = False, # Use for full fine-tuning.
    # token = "hf_...", # use one if using gated models
)

# Do model patching and add fast LoRA weights
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Supports any, but = 0 is optimized
    bias = "none",    # Supports any, but = "none" is optimized
    # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
    use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
    random_state = 3407,
    max_seq_length = max_seq_length,
    use_rslora = False,  # We support rank stabilized LoRA
    loftq_config = None, # And LoftQ
)

trainer = DPOTrainer(
    model = model,
    train_dataset = dataset,
    # eval_dataset = eval_dataset,
    tokenizer = tokenizer,
    args = DPOConfig(
        max_seq_length = max_seq_length,
        per_device_train_batch_size = 8,
        gradient_accumulation_steps = 1,
        warmup_steps = 3,
        max_steps = 10,
        logging_steps = 1,
        output_dir = "outputs",
        save_strategy = "steps",
        save_steps = 1,
        save_only_model = True,
        optim = "adamw_8bit",
        report_to = "wandb",
        seed = 3407,
        learning_rate = 1e-5,
        dataloader_num_workers = 4,
    ),
)
trainer.train()

# Go to https://docs.unsloth.ai for advanced tips like
# (1) Saving to GGUF / merging to 16bit for vLLM
# (2) Continued training from a saved LoRA adapter
# (3) Adding an evaluation loop / OOMs
# (4) Customized chat templates