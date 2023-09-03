import json
import os
import bitsandbytes as bnb
import torch
import torch.nn as nn
import transformers
from pprint import pprint
from datasets import load_dataset
import pandas as pd

from peft import LoraConfig, PeftConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, AutoModelForSeq2SeqLM

os.environ["CUDA_VISIBLE_DEVICES"] = '0'

model_location = '../../model/flan-alpaca-base'
repo_id = "declare-lab/flan-alpaca-large" # change to use different LLMs

# configuration to quantize the model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

#load model
# model = AutoModelForCausalLM.from_pretrained(
#     repo_id,
#     device_map="auto",
#     trust_remote_code=True,
#     quantization_config=bnb_config
# )

# # get the tokenizer for the model 
# tokenizer = AutoTokenizer.from_pretrained(repo_id)
# tokenizer.pad_token = tokenizer.eos_token

alpaca_tokenizer = AutoTokenizer.from_pretrained(model_location)
alpaca_model = AutoModelForSeq2SeqLM.from_pretrained(
    model_location,
    device_map="auto",
    trust_remote_code=True,
    quantization_config=bnb_config
)

#model = AutoModelForCausalLM.from_pretrained(repo_id, device_map="auto", quantization_config=bnb_config, cache_dir="./falcon7B")
#tokenizer = AutoTokenizer.from_pretrained(repo_id, cache_dir = "./falcon7B")
alpaca_model.gradient_checkpointing_enable()
alpaca_model = prepare_model_for_kbit_training(alpaca_model)
# Qlora configuration, can tweak r, lora_alpha, and lora_dropout as hyperparameters
config = LoraConfig(
    r=16,
    lora_alpha=32,
    # target_modules=["query_key_value"],
    lora_dropout = 0.05,
    bias="none",
    task_type = "Seq2Seq"
)

alpaca_model = get_peft_model(alpaca_model, config)
#load data

def generate_prompt(data_point,description = "html_parsed",summary = "Summary"):
    prompt = f"""
    Please summarize the following text in a clear, well-organized, and easy-to-understand manner:
    Content: {data_point[description]}
    Summary: {data_point[summary]}
    """
    
    return prompt
    
def generate_and_tokenize_prompt(data_point):
    # prompt = generate_prompt(data_point, description = "Summary_small",summary = "summary_alpaca")
    prompt = generate_prompt(data_point, description = "html_parsed",summary = "Summary")
    tokenized_prompt = alpaca_tokenizer(prompt, padding=True, truncation=True)
    # print(type(tokenized_prompt))
    return dict({
        "input_ids" : tokenized_prompt["input_ids"],
        "attention_mask" : tokenized_prompt["attention_mask"]

        })
    return tokenized_prompt

data = load_dataset("csv", data_files = "train_data.csv")
# data = data["train"].shuffle().map(generate_and_tokenize_prompt)
tokenized_datasets = data["train"].shuffle().map(generate_and_tokenize_prompt, batched = False)
tokenized_datasets = tokenized_datasets.remove_columns(data["train"].column_names)
# Can tune almost all these parameters but primarily batch_size, steps, epochs, and max_steps BUT if max_steps, it overrides train_epochs
training_args = transformers.TrainingArguments(
    per_device_train_batch_size=5,
    gradient_accumulation_steps=5,
    num_train_epochs=40,
    learning_rate=2e-4,
    fp16=True,
    remove_unused_columns=False,
    # save_total_limit=3,
    # logging_steps=0,
    output_dir="outputs2",
    optim="paged_adamw_8bit",
    lr_scheduler_type="cosine",
    #warmup_ratio=0.05
    warmup_steps = 100,
    #max_steps = 300
)

trainer = transformers.Trainer(
    model = alpaca_model,
    train_dataset = tokenized_datasets,
    args = training_args,
    data_collator = transformers.DataCollatorForLanguageModeling(alpaca_tokenizer, mlm=False)
)

alpaca_model.config.use_cache = False
trainer.train()
MODEL_SAVE_LOCATION = "../../model/flan-alpaca-task-specific"
alpaca_model.save_pretrained(MODEL_SAVE_LOCATION)
alpaca_tokenizer.save_pretrained(MODEL_SAVE_LOCATION)# change name of folder you want to save new weights to 
config = PeftConfig.from_pretrained(MODEL_SAVE_LOCATION)

alpaca_tokenizer = AutoTokenizer.from_pretrained(config.base_model_name_or_path)
alpaca_tokenizer.pad_token = alpaca_tokenizer.eos_token
alpaca_model = AutoModelForSeq2SeqLM.from_pretrained(
    config.base_model_name_or_path,
    return_dict = True,
    quantization_config = bnb_config,
    device_map = "auto",
    trust_remote_code = True)

alpaca_model = PeftModel.from_pretrained(alpaca_model, MODEL_SAVE_LOCATION)

generation_config = alpaca_model.generation_config
generation_config.max_new_tokens = 2048 #number of tokens in output
generation_config.temperature = 0.01 #level of creativity
generation_config.top_p = 0.7 #threshold to select probable next tokens
generation_config.num_return_sequences = 1
generation_config.pad_token_id = alpaca_tokenizer.eos_token_id
generation_config.eos_token_id = alpaca_tokenizer.eos_token_id


import random
size = complete_result.shape[0]
description = complete_result.iloc[random.randint(0, size-1) ]["html_parsed"]
prompt_search = f"""Please summarize the following text in a clear, well-organized, and easy-to-understand manner:
    Content: {description}"""
print(prompt_search)
encoding = alpaca_tokenizer(prompt_search, return_tensors="pt").to("cuda:0")
with torch.inference_mode():
    outputs = alpaca_model.generate(
    input_ids = encoding.input_ids,
    attention_mask = encoding.attention_mask,
    generation_config = generation_config
    )
print(f"Summary: {alpaca_tokenizer.decode(outputs[0], skip_special_tokens=True)}")
