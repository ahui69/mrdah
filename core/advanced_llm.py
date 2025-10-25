#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Advanced Integration - Zaawansowana integracja z silnikiem językowym
Zawiera funkcje do efektywnego przetwarzania zapytań LLM, optymalizacji
wsadowej i mechanizmy adaptacyjne do obciążenia systemu.
"""

import time
import asyncio
import threading
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from collections import deque
import heapq
import json
import traceback
import hashlib

from core.llm import call_llm, call_llm_once, call_llm_stream
from core.config import (
    LLM_MODEL, LLM_API_KEY, LLM_BASE_URL, 
    LLM_RETRIES, LLM_TIMEOUT, LLM_BACKOFF_S
)
from core.helpers import log_info, log_warning, log_error

# Import Redis cache middleware
try:
    from core.redis_middleware import get_redis, cached
    REDIS_AVAILABLE = True
except Exception as e:
    log_warning(f"Redis not available: {e}")
    REDIS_AVAILABLE = False

# Import modułu wsadowego przetwarzania
from batch_processing import (
    process_batch, call_llm_batch, get_batch_metrics, batch_processor
)


# ═══════════════════════════════════════════════════════════════════
# KONFIGURACJA INTEGRACJI LLM
# ═══════════════════════════════════════════════════════════════════

# Parametry adaptacyjne
ADAPTIVE_BATCH_THRESHOLD = 10  # Liczba żądań w kolejce, przy której włączamy wsadowe przetwarzanie
ADAPTIVE_LATENCY_MS = 100      # Maksymalne dodatkowe opóźnienie dla wsadowego przetwarzania (ms)
BATCH_PROCESSING_ENABLED = True  # Globalne włączenie/wyłączenie wsadowego przetwarzania

# Monitorowanie i statystyki
MAX_HISTORY_SIZE = 1000        # Maksymalna liczba wpisów w historii
METRICS_WINDOW_SIZE = 100      # Liczba ostatnich zapytań do obliczania średnich metryk

# Metryki systemowe
class LLMMetrics:
    """Przechowuje metryki operacji LLM"""
    def __init__(self):
        self.total_requests = 0
        self.total_batched_requests = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.total_errors = 0
        
        # Bufory do obliczeń średnich wartości
        self.latency_buffer = deque(maxlen=METRICS_WINDOW_SIZE)
        self.token_counts_in = deque(maxlen=METRICS_WINDOW_SIZE)
        self.token_counts_out = deque(maxlen=METRICS_WINDOW_SIZE)
        self.queue_sizes = deque(maxlen=METRICS_WINDOW_SIZE)
        
        # Historia przetwarzania
        self.processing_history = deque(maxlen=MAX_HISTORY_SIZE)
        
    def record_request(self, latency_ms: float, tokens_in: int, tokens_out: int, queue_size: int, was_batched: bool):
        """Rejestruje metryki jednego zapytania"""
        self.total_requests += 1
        if was_batched:
            self.total_batched_requests += 1
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        
        # Dodaj do buforów dla średnich wartości
        self.latency_buffer.append(latency_ms)
        self.token_counts_in.append(tokens_in)
        self.token_counts_out.append(tokens_out)
        self.queue_sizes.append(queue_size)
        
        # Dodaj do historii
        timestamp = time.time()
        self.processing_history.append({
            "timestamp": timestamp,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "queue_size": queue_size,
            "was_batched": was_batched
        })
    
    def record_error(self, error_type: str):
        """Rejestruje błąd LLM"""
        self.total_errors += 1
        # Dodaj do historii
        timestamp = time.time()
        self.processing_history.append({
            "timestamp": timestamp,
            "error_type": error_type,
            "is_error": True
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Zwraca statystyki dotyczące wydajności LLM"""
        # Obliczenia średnich wartości
        avg_latency = sum(self.latency_buffer) / max(1, len(self.latency_buffer))
        avg_tokens_in = sum(self.token_counts_in) / max(1, len(self.token_counts_in))
        avg_tokens_out = sum(self.token_counts_out) / max(1, len(self.token_counts_out))
        avg_queue_size = sum(self.queue_sizes) / max(1, len(self.queue_sizes))
        
        # Obliczenia procentowe
        batch_percentage = (self.total_batched_requests / max(1, self.total_requests)) * 100.0
        error_rate = (self.total_errors / max(1, self.total_requests)) * 100.0
        
        return {
            "total_requests": self.total_requests,
            "total_batched_requests": self.total_batched_requests,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_errors": self.total_errors,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_tokens_in": round(avg_tokens_in, 2),
            "avg_tokens_out": round(avg_tokens_out, 2),
            "avg_queue_size": round(avg_queue_size, 2),
            "batch_percentage": round(batch_percentage, 2),
            "error_rate": round(error_rate, 2),
            "recent_history": list(self.processing_history)[-10:]  # Ostatnie 10 wpisów
        }


# Globalny obiekt metryki
llm_metrics = LLMMetrics()

# Kolejka żądań
request_queue = asyncio.Queue()
request_count = 0
queue_lock = threading.Lock()

# Stany adaptatora
is_batch_mode_active = False  # Czy tryb wsadowy jest obecnie aktywny
last_mode_switch_time = 0     # Czas ostatniej zmiany trybu (unix timestamp)


# ═══════════════════════════════════════════════════════════════════
# ZAAWANSOWANE FUNKCJE LLM
# ═══════════════════════════════════════════════════════════════════

async def adaptive_llm_call(messages: List[Dict[str, Any]], **params) -> str:
    """
    Adaptacyjne wywołanie LLM - automatycznie wybiera między zwykłym wywołaniem a wsadowym
    
    Args:
        messages: Lista wiadomości dla LLM
        **params: Dodatkowe parametry dla LLM
        
    Returns:
        Odpowiedź LLM jako tekst
    """
    global is_batch_mode_active, last_mode_switch_time, request_count
    
    # Oszacuj liczbę tokenów wejściowych
    tokens_in = estimate_tokens(messages)
    
    # Określ czy powinniśmy użyć wsadowego przetwarzania
    start_time = time.time()
    
    # Pobierz aktualny rozmiar kolejki
    with queue_lock:
        current_queue_size = request_count
        request_count += 1
    
    use_batch = False
    if BATCH_PROCESSING_ENABLED:
        # Sprawdź warunki dla włączenia wsadowego przetwarzania
        if current_queue_size >= ADAPTIVE_BATCH_THRESHOLD:
            use_batch = True
        elif is_batch_mode_active and (time.time() - last_mode_switch_time) < 10:
            # Utrzymaj tryb wsadowy, jeśli był niedawno włączony
            use_batch = True
    
    # Jeśli zmieniamy tryb, zapamiętaj czas
    if use_batch != is_batch_mode_active:
        is_batch_mode_active = use_batch
        last_mode_switch_time = time.time()
    
    result = None
    was_batched = False
    error = None
    
    try:
        if use_batch:
            # Użyj wsadowego przetwarzania
            result = await call_llm_batch(messages, **params)
            was_batched = True
        else:
            # Użyj standardowego wywołania
            result = call_llm(messages, **params)
    
    except Exception as e:
        error = str(e)
        log_error(f"Adaptive LLM call failed: {error}", "LLM_ADVANCED")
        # Próba fallbacku do standardowego wywołania, jeśli był użyty batch
        if use_batch:
            try:
                log_warning("Falling back to standard LLM call", "LLM_ADVANCED")
                result = call_llm(messages, **params)
                error = None
            except Exception as e2:
                error = f"Batch error: {error}. Fallback error: {str(e2)}"
        
        if error:
            llm_metrics.record_error(error)
            return f"[ERROR] {error[:200]}..."
    
    # Oblicz metryki
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    tokens_out = estimate_tokens([{"role": "assistant", "content": result}]) if result else 0
    
    # Zaktualizuj metryki
    llm_metrics.record_request(
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        queue_size=current_queue_size,
        was_batched=was_batched
    )
    
    # Zmniejsz licznik żądań
    with queue_lock:
        request_count = max(0, request_count - 1)
    
    return result


async def batch_multiple_prompts(prompts: List[str], system_prompt: str = None, **params) -> List[str]:
    """
    Przetwarza wsadowo wiele promptów użytkownika z tym samym promptem systemowym
    
    Args:
        prompts: Lista promptów użytkownika
        system_prompt: Wspólny prompt systemowy (opcjonalny)
        **params: Dodatkowe parametry dla LLM
        
    Returns:
        Lista odpowiedzi LLM
    """
    # Przygotuj listę wiadomości dla każdego promptu
    messages_list = []
    for prompt in prompts:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        messages_list.append(messages)
    
    # Przetwórz wsadowo
    start_time = time.time()
    
    try:
        # Upewnij się, że procesor wsadowy jest uruchomiony
        await ensure_batch_processor_running()
        
        # Wywołaj wsadowe przetwarzanie
        results = await process_batch(messages_list, [params] * len(prompts))
        
        # Oblicz metryki
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_prompt = total_time_ms / len(prompts)
        
        # Zaloguj statystyki
        log_info(f"Batch processed {len(prompts)} prompts in {total_time_ms:.2f}ms " +
                f"(avg: {avg_time_per_prompt:.2f}ms per prompt)", "LLM_BATCH")
        
        # Zwróć wyniki
        return results
        
    except Exception as e:
        log_error(f"Batch processing failed: {e}", "LLM_BATCH")
        
        # Fallback do sekwencyjnego przetwarzania
        log_warning("Falling back to sequential processing", "LLM_BATCH")
        results = []
        
        for messages in messages_list:
            try:
                result = call_llm(messages, **params)
                results.append(result)
            except Exception as inner_e:
                results.append(f"[ERROR] {str(inner_e)[:200]}...")
        
        return results


async def ensure_batch_processor_running():
    """Upewnia się, że procesor wsadowy jest uruchomiony"""
    if not batch_processor.running:
        await batch_processor.start()


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """
    Szacuje liczbę tokenów w wiadomościach
    
    Args:
        messages: Lista wiadomości dla LLM
        
    Returns:
        Szacowana liczba tokenów
    """
    # Proste przybliżenie: 1 token ≈ 4 znaki
    total_chars = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
    
    return total_chars // 4


# ═══════════════════════════════════════════════════════════════════
# ZAAWANSOWANE FUNKCJE PROMPT ENGINEERING
# ═══════════════════════════════════════════════════════════════════

async def optimize_prompt(prompt: str) -> str:
    """
    Optymalizuje prompt dla lepszych wyników
    
    Args:
        prompt: Oryginalny prompt
        
    Returns:
        Zoptymalizowany prompt
    """
    # Jeśli prompt jest krótki, nie optymalizuj
    if len(prompt) < 200:
        return prompt
    
    # Próba optymalizacji długich promptów
    try:
        optimization_prompt = [
            {"role": "system", "content": "Jesteś ekspertem od optymalizacji promptów. " +
             "Twoim zadaniem jest skrócenie i poprawienie promptu, zachowując jego kluczowe elementy. " +
             "Usuń zbędne słowa, upewnij się, że prompt jest jasny i zwięzły. " +
             "Zachowaj wszystkie konkretne instrukcje i pytania."},
            {"role": "user", "content": f"Zoptymalizuj ten prompt, zachowując kluczowe pytania i instrukcje:\n\n{prompt}"}
        ]
        
        optimized = await adaptive_llm_call(optimization_prompt, temperature=0.3, max_tokens=2048)
        
        # Jeśli optymalizacja zwiększyła długość, użyj oryginału
        if len(optimized) >= len(prompt):
            return prompt
        
        # Jeśli optymalizacja skróciła zbyt mocno, użyj oryginału
        if len(optimized) < len(prompt) * 0.5:
            return prompt
        
        return optimized
    
    except Exception:
        # W przypadku błędu, użyj oryginalnego promptu
        return prompt


def extract_key_information(text: str, max_length: int = 800) -> str:
    """
    Ekstrahuje kluczowe informacje z długiego tekstu
    
    Args:
        text: Tekst wejściowy
        max_length: Maksymalna długość wynikowego tekstu
        
    Returns:
        Skrócony tekst zawierający kluczowe informacje
    """
    # Jeśli tekst jest już krótszy niż limit, zwróć go bez zmian
    if len(text) <= max_length:
        return text
    
    # Proste skrócenie przez podzielenie tekstu na sekcje i wybranie początków każdej sekcji
    paragraphs = text.split("\n\n")
    
    if len(paragraphs) <= 1:
        # Jeśli nie ma wyraźnych paragrafów, podziel na zdania
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 3:
            # Jeśli mało zdań, po prostu przytnij
            return text[:max_length] + "..."
            
        # Wybierz pierwsze i ostatnie zdania oraz kilka ze środka
        result = sentences[0] + " "
        
        # Dodaj kilka zdań ze środka
        middle_count = min(3, len(sentences) // 2)
        middle_start = (len(sentences) - middle_count) // 2
        for i in range(middle_start, middle_start + middle_count):
            result += sentences[i] + " "
        
        # Dodaj ostatnie zdanie
        result += sentences[-1]
        
        # Przytnij, jeśli nadal za długi
        if len(result) > max_length:
            result = result[:max_length] + "..."
        
        return result
    
    # Wybierz pierwsze i ostatnie zdania każdego paragrafu
    result = paragraphs[0] + "\n\n"
    
    # Dodaj pierwsze zdania z pozostałych paragrafów
    import re
    for para in paragraphs[1:-1]:
        if not para.strip():
            continue
        
        # Wyciągnij pierwsze zdanie
        match = re.match(r'^([^.!?]+[.!?])', para.strip())
        if match:
            result += match.group(1) + "\n\n"
    
    # Dodaj ostatni paragraf
    if len(paragraphs) > 1:
        result += paragraphs[-1]
    
    # Przytnij, jeśli nadal za długi
    if len(result) > max_length:
        result = result[:max_length] + "..."
    
    return result


# ═══════════════════════════════════════════════════════════════════
# FUNKCJE WYSOKO POZIOMOWE DLA SILNIKA KOGNITYWNEGO
# ═══════════════════════════════════════════════════════════════════

async def enhanced_cognitive_llm_call(
    messages: List[Dict[str, Any]], 
    optimize: bool = True, 
    priority: int = 0,
    **params
) -> Dict[str, Any]:
    """
    Ulepszone wywołanie LLM dla silnika kognitywnego z pełnymi metadanymi
    
    Args:
        messages: Lista wiadomości dla LLM
        optimize: Czy optymalizować prompt
        priority: Priorytet żądania (wyższy = ważniejsze)
        **params: Dodatkowe parametry dla LLM
        
    Returns:
        Dict zawierający odpowiedź i metadane
    """
    start_time = time.time()
    
    try:
        # Optymalizacja promptu (opcjonalna)
        if optimize and len(messages) > 0 and "content" in messages[-1]:
            last_message = messages[-1]["content"]
            if isinstance(last_message, str) and len(last_message) > 200:
                optimized_message = await optimize_prompt(last_message)
                messages[-1]["content"] = optimized_message
        
        # Szacowanie liczby tokenów wejściowych
        tokens_in = estimate_tokens(messages)
        
        # Wywołanie LLM z adaptacyjnym trybem
        result = await adaptive_llm_call(messages, **params)
        
        # Szacowanie liczby tokenów wyjściowych
        tokens_out = estimate_tokens([{"role": "assistant", "content": result}]) if result else 0
        
        # Obliczenie czasu wykonania
        elapsed_time = time.time() - start_time
        
        # Przygotuj metadane o wywołaniu
        metadata = {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "processing_time_ms": round(elapsed_time * 1000, 2),
            "optimized": optimize,
            "was_batched": is_batch_mode_active,
            "queue_size": request_count,
            "timestamp": time.time()
        }
        
        # Jeśli był użyty wsadowy procesor, dołącz jego metryki
        if is_batch_mode_active:
            batch_metrics = get_batch_metrics()
            if batch_metrics:
                metadata["batch_metrics"] = {
                    "avg_batch_size": batch_metrics.get("avg_batch_size", 0),
                    "avg_processing_time_ms": batch_metrics.get("avg_processing_time_ms", 0),
                    "total_batches": batch_metrics.get("total_batches", 0)
                }
        
        return {
            "answer": result,
            "metadata": metadata
        }
        
    except Exception as e:
        error_msg = str(e)
        log_error(f"Enhanced cognitive LLM call failed: {error_msg}", "LLM_ADVANCED")
        
        # Przygotuj odpowiedź błędu z metadanymi
        elapsed_time = time.time() - start_time
        return {
            "answer": f"[ERROR] Wystąpił problem podczas przetwarzania: {error_msg[:200]}...",
            "metadata": {
                "error": error_msg,
                "processing_time_ms": round(elapsed_time * 1000, 2),
                "timestamp": time.time()
            }
        }


def get_llm_advanced_metrics() -> Dict[str, Any]:
    """
    Pobiera szczegółowe metryki LLM
    
    Returns:
        Słownik z metrykami
    """
    stats = llm_metrics.get_statistics()
    
    # Dodaj stan adaptatora
    stats["adaptive_state"] = {
        "is_batch_mode_active": is_batch_mode_active,
        "last_mode_switch": last_mode_switch_time,
        "current_queue_size": request_count,
        "batch_threshold": ADAPTIVE_BATCH_THRESHOLD
    }
    
    # Dodaj informacje o konfiguracji
    stats["config"] = {
        "batch_processing_enabled": BATCH_PROCESSING_ENABLED,
        "adaptive_latency_ms": ADAPTIVE_LATENCY_MS,
        "metrics_window_size": METRICS_WINDOW_SIZE
    }
    
    # Jeśli wsadowy procesor jest aktywny, dołącz jego metryki
    if batch_processor.running:
        batch_metrics = get_batch_metrics()
        stats["batch_processor"] = batch_metrics
    
    return stats


# ═══════════════════════════════════════════════════════════════════
# INICJALIZACJA I ZARZĄDZANIE
# ═══════════════════════════════════════════════════════════════════

async def initialize_advanced_llm():
    """Inicjalizuje zaawansowane funkcje LLM"""
    # Uruchom procesor wsadowy
    await ensure_batch_processor_running()
    log_info("Advanced LLM integration initialized", "LLM_ADVANCED")

async def shutdown_advanced_llm():
    """Zatrzymuje zaawansowane funkcje LLM"""
    # Zatrzymaj procesor wsadowy
    if batch_processor.running:
        await batch_processor.stop()
    log_info("Advanced LLM integration shut down", "LLM_ADVANCED")

# Automatyczna inicjalizacja podczas importu
async def _auto_init():
    try:
        await initialize_advanced_llm()
    except Exception as e:
        log_error(f"Failed to initialize advanced LLM: {e}", "LLM_ADVANCED")

# Uruchom inicjalizację w tle
if BATCH_PROCESSING_ENABLED:
    asyncio.create_task(_auto_init())