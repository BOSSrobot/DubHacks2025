import os
import argparse
from unsloth import FastLanguageModel, FastModel
from peft import PeftModel, PeftConfig, get_peft_model

def main():
    # parser = argparse.ArgumentParser(description="Fuse LoRA adapter into base model")
    # parser.add_argument("--base_model", type=str, required=True, help="Path to base Hugging Face model or pretrained model name")
    # parser.add_argument("--lora_model", type=str, required=True, help="Path to LoRA adapter checkpoint")
    # parser.add_argument("--output_dir", type=str, required=True, help="Directory to save fused model")
    # args = parser.parse_args()
    output_dir = "ab-test-rlhf/outputs/checkpoint-10"
    lora_model = output_dir
    output_dir += "/fused_model"
    base_model = ".cache/huggingface/hub/models--Qwen--Qwen3-Coder-30B-A3B-Instruct/snapshots/573fa3901e5799703b1e60825b0ec024a4c0f1d3"
    max_seq_length = 8192
    os.makedirs(output_dir, exist_ok=True)

    base_model, tokenizer = FastModel.from_pretrained(
        model_name = "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        max_seq_length = max_seq_length, # Choose any for long context!
        load_in_4bit = True,  # 4-bit quantization. False = 16-bit LoRA.
        load_in_8bit = False, # 8-bit quantization
        load_in_16bit = False, # [NEW!] 16-bit LoRA
        full_finetuning = False, # Use for full fine-tuning.
        # token = "hf_...", # use one if using gated models
    )

    # # Load base model
    # print("Loading base model...")
    # base_model = AutoModelForCausalLM.from_pretrained(base_model)

    # Load LoRA adapter
    print("Loading LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, lora_model)

    model.save_pretrained_merged(
        output_dir,
        tokenizer,
        save_method="merged_16bit",  # This handles dequantization properly
    ) 

if __name__ == "__main__":
    main()