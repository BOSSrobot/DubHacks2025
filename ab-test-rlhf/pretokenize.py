from datasets import load_dataset
from transformers import AutoTokenizer

model = "Qwen/Qwen2.5-7B-Instruct"
tok = AutoTokenizer.from_pretrained(model, use_fast=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

ds = load_dataset("trl-lib/ultrafeedback_binarized", split="train")
max_len = 2048

ex = ds[0]
print({k : type(ex[k]) for k in ex})
for k in ex:
    if isinstance(ex[k], list):
        print(k, ex[k])
    elif isinstance(ex[k], float):
        print(k, ex[k])

exit()

def list_to_text(msgs):
    # list of dicts like [{"role": "...", "content": "..."}]
    if isinstance(msgs, list) and msgs and isinstance(msgs[0], dict) and "content" in msgs[0]:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    # list of strings
    if isinstance(msgs, list) and (len(msgs) == 0 or isinstance(msgs[0], str)):
        return "\n".join(msgs)
    # fallback
    return str(msgs)

def tokenize_batch(batch):
    chosen_txts   = [list_to_text(x) for x in batch["chosen"]]
    rejected_txts = [list_to_text(x) for x in batch["rejected"]]

    tch = tok(chosen_txts,  truncation=True, max_length=max_len)
    trj = tok(rejected_txts, truncation=True, max_length=max_len)

    return {
        "chosen_input_ids": tch["input_ids"],
        "chosen_attention_mask": tch["attention_mask"],
        "rejected_input_ids": trj["input_ids"],
        "rejected_attention_mask": trj["attention_mask"],
    }

tok_ds = ds.map(
    tokenize_batch,
    batched=True,
    remove_columns=ds.column_names,   # keep only tokenized tensors
    # num_proc=1  # keep 1 if you have few CPU cores; raise if you can
)

tok_ds.save_to_disk("ufb_tok_qwen2p5_2048")