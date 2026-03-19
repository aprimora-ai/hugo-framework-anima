"""
ANIMA — src/ego/hf_backend.py
================================
Backend HuggingFace para o LLM-Ego.

Carrega modelos via transformers com:
  - output_attentions=True  → matrizes de atenção reais para KappaSignal
  - quantização 4-bit (bitsandbytes) → cabe em 8GB VRAM
  - attn_implementation="eager" → obrigatório para extrair atenção

Vantagens sobre Ollama:
  - Matrizes de atenção reais (não proxy via logprobs)
  - Controle total de quantização
  - KappaSignal topologicamente correto

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class HFConfig:
    model_id:        str   = "microsoft/Phi-3-mini-4k-instruct"
    load_in_4bit:    bool  = True
    load_in_8bit:    bool  = False
    device_map:      str   = "auto"
    max_new_tokens:  int   = 512
    temperature:     float = 0.7
    do_sample:       bool  = True
    attention_layer: int   = -1   # -1 = última camada


@dataclass
class HFResponse:
    text:             str
    attention_matrix: Optional[np.ndarray]  # [seq, seq] média das heads
    logits_last:      Optional[np.ndarray]  # logits do último token gerado
    n_input_tokens:   int = 0
    n_output_tokens:  int = 0


class HuggingFaceBackend:
    """
    Backend HuggingFace para o ANIMA.
    Gera texto e retorna matrizes de atenção para KappaSignal real.
    """

    def __init__(self, cfg: HFConfig):
        self.cfg = cfg
        self._model     = None
        self._tokenizer = None
        self._load()

    def _load(self):
        import torch, os
        from transformers import (
            AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        )

        # Reduz fragmentação de memória CUDA
        os.environ.setdefault(
            "PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True"
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._device = device
        print(f"  [HF] Carregando {self.cfg.model_id} em {device}...")

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.cfg.model_id, trust_remote_code=True)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        bnb_config = None
        if self.cfg.load_in_4bit and device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            print("  [HF] Quantizacao: 4-bit NF4")
        elif self.cfg.load_in_8bit and device == "cuda":
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            print("  [HF] Quantizacao: 8-bit")

        self._model = AutoModelForCausalLM.from_pretrained(
            self.cfg.model_id,
            quantization_config=bnb_config,
            device_map=self.cfg.device_map,
            attn_implementation="eager",
            output_attentions=True,
            trust_remote_code=True,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        self._model.eval()
        print(f"  [HF] Pronto: {self.cfg.model_id}")

    def generate(self, messages: List[dict]) -> HFResponse:
        """Gera resposta + matriz de atenção a partir de lista de mensagens."""
        import torch

        # Chat template
        try:
            prompt = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            prompt = self._build_prompt_manual(messages)

        inputs = self._tokenizer(
            prompt, return_tensors="pt",
            truncation=True, max_length=4096,
        ).to(self._device)
        n_input = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.cfg.max_new_tokens,
                temperature=self.cfg.temperature,
                do_sample=self.cfg.do_sample,
                pad_token_id=self._tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_attentions=True,
                output_scores=True,
            )

        # Decodificar texto — mover para CPU imediatamente
        new_ids  = outputs.sequences[0, n_input:].cpu()
        text     = self._tokenizer.decode(new_ids, skip_special_tokens=True).strip()
        n_output = len(new_ids)

        # Extrair atenção para CPU antes de liberar GPU
        attn = self._extract_attention(outputs)

        # Logits do último token
        logits_last = None
        if outputs.scores:
            logits_last = outputs.scores[-1][0].float().cpu().numpy()

        # Liberar tensores da GPU explicitamente
        del outputs
        del inputs
        if self._device == "cuda":
            torch.cuda.empty_cache()

        return HFResponse(
            text=text,
            attention_matrix=attn,
            logits_last=logits_last,
            n_input_tokens=n_input,
            n_output_tokens=n_output,
        )

    def _extract_attention(self, outputs) -> Optional[np.ndarray]:
        """
        Extrai atenção da camada escolhida e move para CPU/numpy imediatamente.
        Libera o tensor GPU após extração para evitar acúmulo de memória.
        """
        try:
            if not outputs.attentions or not outputs.attentions[0]:
                return None
            step0       = outputs.attentions[0]
            attn_tensor = step0[self.cfg.attention_layer]
            # Mover para CPU e converter — libera referência GPU
            attn_mean   = attn_tensor[0].mean(dim=0).float().cpu().numpy()
            del attn_tensor
            a_min, a_max = attn_mean.min(), attn_mean.max()
            if a_max - a_min > 1e-10:
                return (attn_mean - a_min) / (a_max - a_min)
            return attn_mean
        except Exception:
            return None

    def _build_prompt_manual(self, messages: List[dict]) -> str:
        """Fallback para modelos sem chat template."""
        parts = []
        for m in messages:
            role, content = m.get("role", "user"), m.get("content", "")
            if role == "system":
                parts.append(f"Sistema: {content}")
            elif role == "user":
                parts.append(f"Humano: {content}")
            elif role == "assistant":
                parts.append(f"Assistente: {content}")
        parts.append("Assistente:")
        return "\n\n".join(parts)

    @property
    def model_id(self) -> str:
        return self.cfg.model_id
