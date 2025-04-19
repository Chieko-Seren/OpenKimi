# Starlight Dream, It's Qwen-2 Fine-tuning!!!!!

import torch
from modelscope import snapshot_download, AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset
import json
import os

# Download and cache model
model_dir = snapshot_download('qwen/Qwen2-7B-Instruct', cache_dir='/root/autodl-tmp', revision='master')

# Optimized tokenizer loading with explicit padding token handling
tokenizer = AutoTokenizer.from_pretrained(
   '/root/autodl-tmp/qwen/Qwen2-7B-Instruct/',
   use_fast=False,
   trust_remote_code=True,
   padding_side='right'
)
tokenizer.pad_token = tokenizer.eos_token if tokenizer.pad_token is None else tokenizer.pad_token

def load_jsonl_data(file_path):
   """Load data from a jsonl file and update self-cognition to Kimi."""
   data = []
   with open(file_path, 'r', encoding='utf-8') as f:
       for line in f:
           item = json.loads(line.strip())
           data.append(item)
   return data

def process_func(example, max_length=384):
   """
   Process examples for training with optimized tokenization and truncation.
   Returns input_ids, attention_mask, and labels with proper padding.
   """
   # Combine instruction and input for system prompt with Kimi persona
   instruction_text = (
       "<|im_start|>system\n你现在是Kimi，一个聪明、幽默的AI助手，由Moonshot AI开发。<|im_end|>\n"
       f"<|im_start|>user\n{example['instruction'] + example['input']}<|im_end|>\n"
       "<|im_start|>assistant\n"
   )
   response_text = example['output']
   
   # Tokenize instruction and response
   instruction = tokenizer(instruction_text, add_special_tokens=False)
   response = tokenizer(response_text, add_special_tokens=False)
   
   # Combine input_ids, attention_mask, and labels
   input_ids = instruction["input_ids"] + response["input_ids"]
   attention_mask = instruction["attention_mask"] + response["attention_mask"]
   labels = [-100] * len(instruction["input_ids"]) + response["input_ids"]
   
   # Truncate to max_length and add padding
   if len(input_ids) > max_length:
       input_ids = input_ids[:max_length]
       attention_mask = attention_mask[:max_length]
       labels = labels[:max_length]
   else:
       padding_length = max_length - len(input_ids)
       input_ids += [tokenizer.pad_token_id] * padding_length
       attention_mask += [0] * padding_length
       labels += [-100] * padding_length
   
   return {
       "input_ids": input_ids,
       "attention_mask": attention_mask,
       "labels": labels
   }

# Load model with 4-bit quantization for memory efficiency
from transformers import BitsAndBytesConfig
quant_config = BitsAndBytesConfig(
   load_in_4bit=True,
   bnb_4bit_quant_type="nf4",
   bnb_4bit_compute_dtype=torch.bfloat16,
   bnb_4bit_use_double_quant=True
)

model = AutoModelForCausalLM.from_pretrained(
   '/root/autodl-tmp/qwen/Qwen2-7B-Instruct/',
   quantization_config=quant_config,
   device_map="auto",
   trust_remote_code=True
)

# Apply LoRA configuration
lora_config = LoraConfig(
   task_type="CAUSAL_LM",
   target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
   r=16,
   lora_alpha=32,
   lora_dropout=0.05,
   bias="none",
   use_rslora=True
)
model = get_peft_model(model, lora_config)

# Training arguments with optimizations
training_args = TrainingArguments(
   output_dir="./output/Kimi_Distill_Qwen2_instruct_lora",
   per_device_train_batch_size=4,
   gradient_accumulation_steps=4,
   logging_steps=10,
   num_train_epochs=3,
   learning_rate=5e-5,
   save_steps=100,
   save_total_limit=2,
   gradient_checkpointing=True,
   fp16=False,
   bf16=True,
   optim="adamw_8bit",
   dataloader_num_workers=4,
   report_to="none",
   deepspeed=None
)

# Load and process dataset from jsonl
data = load_jsonl_data('data.jsonl')
dataset = Dataset.from_list(data)
tokenized_id = dataset.map(
   lambda x: process_func(x, max_length=384),
   batched=False,
   remove_columns=dataset.column_names
)

# Initialize trainer
trainer = Trainer(
   model=model,
   args=training_args,
   train_dataset=tokenized_id,
   data_collator=DataCollatorForSeq2Seq(
       tokenizer=tokenizer,
       padding=True,
       label_pad_token_id=-100
   ),
)

# Train the model
trainer.train()

# Save the final model
model.save_pretrained("./output/Kimi_Distill_Qwen2_instruct_lora/final")
tokenizer.save_pretrained("./output/Kimi_Distill_Qwen2_instruct_lora/final")

