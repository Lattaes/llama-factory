# Copyright 2025 HuggingFace Inc. and the LlamaFactory team.
#
# This code is based on the HuggingFace's PEFT library.
# https://github.com/huggingface/peft/blob/v0.10.0/examples/loftq_finetuning/quantize_save_load.py
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import shutil

import fire
from peft import PeftModel
from transformers import AutoModel, AutoProcessor, AutoTokenizer


def merge_lora(
    base_model_path: str,
    lora_checkpoint_path: str,
    extra_file: str = "spk_dict.pt",
    submodule_name: str = "thinker",
    save_path: str = "./merged_model_checkpoint",
):
    """Load the original model, tokenizer, and processor configuration, merge the LoRA weights.

    for a specified submodule, and save the final merged model along with its configurations.

    Args:
        base_model_path (str): Path to the original model directory.
        lora_checkpoint_path (str): Path to the directory containing LoRA weights.
        extra_file (str): Name of the extra file to be copied (default: "spk_dict.pt").
        submodule_name (str): Name of the submodule to merge (default: "thinker").
        save_path (str): Directory where the merged model and configurations will be saved.
    """
    # 1. Load the original model, tokenizer, and processor
    model = AutoModel.from_pretrained(base_model_path)
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)

    try:
        processor = AutoProcessor.from_pretrained(base_model_path)
    except Exception:
        print("Processor configuration not found, skipping processor load.")
        processor = None

    print("Successfully loaded the original model, tokenizer, and processor (if available).")

    # 2. Extract the submodule to be merged (e.g., model.thinker)
    if not hasattr(model, submodule_name):
        raise AttributeError(f"The model does not have a submodule named '{submodule_name}'.")
    base_submodule = getattr(model, submodule_name)
    print(f"Successfully extracted submodule: {submodule_name}.")

    # 3. Load the LoRA weights onto the extracted submodule
    lora_model = PeftModel.from_pretrained(base_submodule, lora_checkpoint_path)
    print("LoRA weights loaded successfully.")

    # 4. Merge the LoRA weights into the submodule and unload the LoRA modules
    merged_submodule = lora_model.merge_and_unload()
    print("LoRA weights merged successfully.")

    # 5. Replace the original submodule with the merged submodule in the model
    setattr(model, submodule_name, merged_submodule)

    # 6. Save the final merged model along with the tokenizer and processor configuration
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    if processor is not None:
        processor.save_pretrained(save_path)

    print(f"Merged model and configuration saved to {save_path}.")

    source_file = os.path.join(base_model_path, extra_file)
    target_file = os.path.join(save_path, extra_file)
    if os.path.exists(source_file):
        shutil.copy(source_file, target_file)
        print(f"File '{extra_file}' copied from {base_model_path} to {save_path}.")
    else:
        print(f"File '{extra_file}' not found in {base_model_path}, skipping copy.")


if __name__ == "__main__":
    fire.Fire(merge_lora)
