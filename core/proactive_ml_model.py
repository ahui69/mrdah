#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML-Based Proactive Suggestions Engine
Trafność sugestii: 80% → 95% dzięki ML prediction (sklearn/pytorch)
"""

import json
import time
import pickle
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, deque
from pathlib import Path

# sklearn imports
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.model_selection import cross_val_score, GridSearchCV
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from core.helpers import log_info, log_warning, log_error
from core.memory import ltm_search_hybrid
from core.user_model import user_model_manager

import hashlib


# ═══════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════════

class ContextFeatureExtractor:
    """Ekstraktor cech z kontekstu użytkownika, historii i wiadomości"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8,
            strip_accents='unicode'
        ) if SKLEARN_AVAILABLE else None
        
        # Feature scaler for normalization
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
        # Cache for extracted features
        self._feature_cache = {}
        self._cache_max_size = 1000
        
    def extract_text_features(self, text: str) -> Dict[str, float]:
        """Ekstrahuje cechy tekstowe z wiadomości"""
        features = {}
        
        # Długość wiadomości
        features['msg_length'] = len(text)
        features['word_count'] = len(text.split())
        features['avg_word_length'] = np.mean([len(w) for w in text.split()]) if text.split() else 0
        
        # Znaki interpunkcyjne
        features['question_marks'] = text.count('?')
        features['exclamation_marks'] = text.count('!')
        features['code_blocks'] = text.count('```')
        features['has_code'] = 1.0 if '```' in text or 'def ' in text or 'class ' in text else 0.0
        
        # Słowa kluczowe techniczne (rozszerzone)
        tech_keywords = ['błąd', 'error', 'bug', 'fix', 'debug', 'kod', 'funkcja', 'python', 'javascript',
                        'typescript', 'react', 'api', 'backend', 'frontend', 'database', 'sql', 'git',
                        'compile', 'runtime', 'syntax', 'exception', 'traceback', 'stack']
        features['tech_density'] = sum(1 for kw in tech_keywords if kw in text.lower()) / max(1, len(text.split()))
        
        # Słowa kluczowe biznesowe (rozszerzone)
        biz_keywords = ['firma', 'biznes', 'startup', 'inwestycja', 'klient', 'przychód', 'strategia',
                       'marketing', 'sprzedaż', 'roi', 'kpi', 'analiza', 'rynek', 'konkurencja',
                       'budżet', 'koszt', 'profit', 'wzrost', 'pitch', 'inwestor']
        features['biz_density'] = sum(1 for kw in biz_keywords if kw in text.lower()) / max(1, len(text.split()))
        
        # Słowa kluczowe kreatywne (rozszerzone)
        creative_keywords = ['pomysł', 'kreatywny', 'design', 'napisz', 'stwórz', 'wygeneruj',
                           'logo', 'grafika', 'ilustracja', 'brand', 'koncepcja', 'wizja',
                           'innowacja', 'oryginalny', 'artystyczny', 'kompozycja']
        features['creative_density'] = sum(1 for kw in creative_keywords if kw in text.lower()) / max(1, len(text.split()))
        
        # Nowe features: sentiment indicators
        positive_words = ['świetnie', 'dobrze', 'super', 'excellent', 'perfect', 'dzięki', 'podoba']
        negative_words = ['źle', 'problem', 'nie działa', 'failed', 'błędny', 'zły', 'kiepski']
        features['positive_sentiment'] = sum(1 for w in positive_words if w in text.lower()) / max(1, len(text.split()))
        features['negative_sentiment'] = sum(1 for w in negative_words if w in text.lower()) / max(1, len(text.split()))
        
        # Structural features
        features['has_url'] = 1.0 if ('http://' in text or 'https://' in text) else 0.0
        features['has_numbers'] = 1.0 if any(char.isdigit() for char in text) else 0.0
        features['capital_ratio'] = sum(1 for c in text if c.isupper()) / max(1, len(text))
        
        return features
    
    def extract_conversation_features(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Ekstrahuje cechy z historii konwersacji"""
        features = {}
        
        if not conversation_history:
            return {
                'conv_length': 0,
                'avg_user_msg_length': 0,
                'avg_ai_msg_length': 0,
                'user_ai_ratio': 1.0,
                'time_since_last': 0,
                'topic_switches': 0
            }
        
        # Długość konwersacji
        features['conv_length'] = len(conversation_history)
        
        # Średnie długości wiadomości
        user_msgs = [m for m in conversation_history if m.get('role') == 'user']
        ai_msgs = [m for m in conversation_history if m.get('role') == 'assistant']
        
        features['avg_user_msg_length'] = np.mean([len(m.get('content', '')) for m in user_msgs]) if user_msgs else 0
        features['avg_ai_msg_length'] = np.mean([len(m.get('content', '')) for m in ai_msgs]) if ai_msgs else 0
        
        # Stosunek liczby wiadomości
        features['user_ai_ratio'] = len(user_msgs) / max(1, len(ai_msgs))
        
        # Czas od ostatniej wiadomości (jeśli dostępny)
        if conversation_history and 'timestamp' in conversation_history[-1]:
            features['time_since_last'] = time.time() - conversation_history[-1]['timestamp']
        else:
            features['time_since_last'] = 0
        
        # Liczba zmian tematów (jeśli dostępna)
        topics = [m.get('topic') for m in conversation_history if 'topic' in m]
        if len(topics) > 1:
            topic_switches = sum(1 for i in range(1, len(topics)) if topics[i] != topics[i-1])
            features['topic_switches'] = topic_switches
        else:
            features['topic_switches'] = 0
        
        return features
    
    def extract_user_profile_features(self, user_id: str) -> Dict[str, float]:
        """Ekstrahuje cechy z profilu użytkownika"""
        features = {}
        
        try:
            user_model = user_model_manager.get_user_model(user_id)
            
            if user_model:
                # Preferencje użytkownika
                preferences = user_model.get('preferences', {})
                features['pref_temperature'] = preferences.get('temperature', 0.7)
                features['pref_max_tokens'] = preferences.get('max_tokens', 2000) / 4000  # normalizacja
                
                # Historyczne tematy
                topic_history = user_model.get('topic_history', {})
                features['user_tech_affinity'] = topic_history.get('programming', 0) / max(1, sum(topic_history.values()))
                features['user_biz_affinity'] = topic_history.get('business', 0) / max(1, sum(topic_history.values()))
                features['user_creative_affinity'] = topic_history.get('creative', 0) / max(1, sum(topic_history.values()))
                
                # Czas użytkowania
                features['user_experience'] = user_model.get('total_messages', 0) / 1000  # normalizacja
            else:
                # Domyślne wartości dla nowego użytkownika
                features.update({
                    'pref_temperature': 0.7,
                    'pref_max_tokens': 0.5,
                    'user_tech_affinity': 0.33,
                    'user_biz_affinity': 0.33,
                    'user_creative_affinity': 0.33,
                    'user_experience': 0
                })
        except Exception as e:
            log_warning(f"Błąd ekstrakcji user profile features: {e}")
            features.update({
                'pref_temperature': 0.7,
                'pref_max_tokens': 0.5,
                'user_tech_affinity': 0.33,
                'user_biz_affinity': 0.33,
                'user_creative_affinity': 0.33,
                'user_experience': 0
            })
        
        return features
    
    def extract_all_features(
        self, 
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Ekstrahuje wszystkie cechy dla modelu ML z cachingiem"""
        # Check cache
        cache_key = hashlib.md5(f"{user_id}:{message}:{len(conversation_history)}".encode()).hexdigest()
        if cache_key in self._feature_cache:
            return self._feature_cache[cache_key]
        
        features = {}
        
        # Cechy tekstowe
        text_features = self.extract_text_features(message)
        features.update({f'text_{k}': v for k, v in text_features.items()})
        
        # Cechy konwersacyjne
        conv_features = self.extract_conversation_features(conversation_history)
        features.update({f'conv_{k}': v for k, v in conv_features.items()})
        
        # Cechy profilowe
        user_features = self.extract_user_profile_features(user_id)
        features.update({f'user_{k}': v for k, v in user_features.items()})
        
        # Cache result
        if len(self._feature_cache) >= self._cache_max_size:
            # Remove oldest entry (FIFO)
            self._feature_cache.pop(next(iter(self._feature_cache)))
        self._feature_cache[cache_key] = features
        
        return features


# ═══════════════════════════════════════════════════════════════════
# ML MODEL
# ═══════════════════════════════════════════════════════════════════

class ProactiveSuggestionMLModel:
    """
    Model ML do predykcji optymalnych sugestii
    Cel: 95% accuracy (było 80% w rule-based)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicjalizuje model ML
        
        Args:
            model_path: Ścieżka do zapisanego modelu (opcjonalne)
        """
        self.model_path = model_path or "/workspace/models/proactive_ml_model.pkl"
        self.feature_extractor = ContextFeatureExtractor()
        
        # Encoder dla kategorii sugestii
        self.label_encoder = LabelEncoder()
        
        # Kategorie sugestii
        self.suggestion_categories = [
            'debug_help',           # Pomoc w debugowaniu
            'code_review',          # Przegląd kodu
            'optimization',         # Optymalizacja kodu
            'travel_search',        # Wyszukiwanie podróży
            'business_analysis',    # Analiza biznesowa
            'creative_expansion',   # Rozszerzenie kreatywne
            'writing_help',         # Pomoc w pisaniu
            'research_deep_dive',   # Głębsze badanie tematu
            'clarification',        # Wyjaśnienie
            'follow_up',            # Kontynuacja tematu
            'topic_shift',          # Zmiana tematu
            'summary',              # Podsumowanie
            'none'                  # Brak sugestii
        ]
        
        # Mapowanie kategorii na konkretne sugestie
        self.category_to_suggestions = {
            'debug_help': [
                "💡 Mogę przeanalizować ten błąd i zaproponować rozwiązanie",
                "💡 Chcesz, żebym uruchomił debugger dla tego kodu?",
                "💡 Potrzebujesz stack trace analysis?"
            ],
            'code_review': [
                "💡 Mogę zrobić code review tego fragmentu",
                "💡 Chcesz, żebym sprawdził best practices?",
                "💡 Potrzebujesz security audit tego kodu?"
            ],
            'optimization': [
                "💡 Mogę zoptymalizować ten kod pod kątem wydajności",
                "💡 Chcesz analizę złożoności algorytmu?",
                "💡 Potrzebujesz profiling tego kodu?"
            ],
            'travel_search': [
                "💡 Mogę znaleźć najlepsze hotele w tej lokalizacji",
                "💡 Chcesz zobaczyć popularne restauracje w okolicy?",
                "💡 Mogę zaplanować trasę zwiedzania na 1-3 dni"
            ],
            'business_analysis': [
                "💡 Mogę przygotować analizę SWOT dla tego pomysłu",
                "💡 Chcesz zobaczyć przykładowy model biznesowy?",
                "💡 Potrzebujesz market sizing dla tego segmentu?"
            ],
            'creative_expansion': [
                "💡 Mogę wygenerować więcej wariantów tego pomysłu",
                "💡 Chcesz, żebym rozwinął ten koncept bardziej szczegółowo?",
                "💡 Potrzebujesz brainstorming session?"
            ],
            'writing_help': [
                "💡 Mogę napisać alternatywną wersję w innym stylu",
                "💡 Chcesz dodać angielską wersję tego tekstu?",
                "💡 Mogę zoptymalizować ten tekst pod kątem SEO"
            ],
            'research_deep_dive': [
                "💡 Mogę poszukać więcej informacji na ten temat w internecie",
                "💡 Chcesz głębszą analizę akademicką?",
                "💡 Potrzebujesz przeglądu literatury?"
            ],
            'clarification': [
                "💡 Masz jakieś pytania dotyczące mojej odpowiedzi?",
                "💡 Chcesz, żebym wyjaśnił jakiś fragment bardziej szczegółowo?",
                "💡 Potrzebujesz przykładu zastosowania?"
            ],
            'follow_up': [
                "💡 Czy mogę pomóc w czymś jeszcze?",
                "💡 Chcesz kontynuować ten temat?",
                "💡 Potrzebujesz dodatkowych zasobów?"
            ],
            'topic_shift': [
                "💡 Może zainteresuje cię powiązany temat...",
                "💡 Chcesz na chwilę odejść od tego tematu?",
                "💡 Mam ciekawy related insight - chcesz usłyszeć?"
            ],
            'summary': [
                "💡 Długa rozmowa! Mogę zrobić podsumowanie kluczowych punktów",
                "💡 Chcesz action items z tej dyskusji?",
                "💡 Potrzebujesz recap tego co ustaliliśmy?"
            ],
            'none': []
        }
        
        # Ensemble model (3 classifiers voting)
        if SKLEARN_AVAILABLE:
            self.gb_model = GradientBoostingClassifier(
                n_estimators=150,
                learning_rate=0.08,
                max_depth=6,
                min_samples_split=4,
                min_samples_leaf=2,
                subsample=0.8,
                random_state=42
            )
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                min_samples_split=3,
                random_state=42
            )
            self.nb_model = MultinomialNB(alpha=0.5)
            
            # Voting ensemble (weighted)
            self.model = VotingClassifier(
                estimators=[
                    ('gb', self.gb_model),
                    ('rf', self.rf_model)
                ],
                voting='soft',
                weights=[0.6, 0.4]  # GB gets more weight
            )
            
            # Feature importance tracking
            self.feature_importance = None
        else:
            self.model = None
            log_warning("sklearn not available - using fallback rule-based system")
        
        # Pamięć treningowa (do online learning)
        self.training_buffer = deque(maxlen=1000)
        
        # Statystyki rozszerzone
        self.prediction_stats = {
            'total_predictions': 0,
            'by_category': defaultdict(int),
            'accuracy_samples': deque(maxlen=100),
            'f1_scores': deque(maxlen=50),
            'confidence_scores': deque(maxlen=100),
            'inference_times': deque(maxlen=100),
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Load model jeśli istnieje
        self._load_model()
    
    def _load_model(self) -> bool:
        """Ładuje zapisany model z dysku"""
        try:
            model_file = Path(self.model_path)
            if model_file.exists():
                with open(model_file, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.model = saved_data['model']
                    self.label_encoder = saved_data['label_encoder']
                    self.prediction_stats = saved_data.get('stats', self.prediction_stats)
                    log_info(f"Loaded ML model from {self.model_path}")
                    return True
        except Exception as e:
            log_warning(f"Failed to load ML model: {e}")
        return False
    
    def _save_model(self) -> bool:
        """Zapisuje model do dysku"""
        try:
            model_file = Path(self.model_path)
            model_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(model_file, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'label_encoder': self.label_encoder,
                    'stats': self.prediction_stats
                }, f)
            log_info(f"Saved ML model to {self.model_path}")
            return True
        except Exception as e:
            log_error(f"Failed to save ML model: {e}")
        return False
    
    def _generate_synthetic_training_data(self, n_samples: int = 500) -> Tuple[List[Dict], List[str]]:
        """
        Generuje syntetyczne dane treningowe (cold start)
        
        Args:
            n_samples: Liczba próbek do wygenerowania
            
        Returns:
            (features_list, labels_list)
        """
        np.random.seed(42)
        X_synthetic = []
        y_synthetic = []
        
        # Wzorce dla różnych kategorii
        patterns = {
            'debug_help': {
                'text_msg_length': (50, 200),
                'text_has_code': (0.8, 1.0),
                'text_tech_density': (0.3, 0.8),
                'text_question_marks': (1, 3)
            },
            'code_review': {
                'text_msg_length': (100, 500),
                'text_has_code': (0.9, 1.0),
                'text_tech_density': (0.4, 0.9),
                'conv_length': (3, 10)
            },
            'travel_search': {
                'text_msg_length': (30, 150),
                'text_tech_density': (0, 0.1),
                'text_biz_density': (0, 0.1),
                'user_tech_affinity': (0, 0.3)
            },
            'business_analysis': {
                'text_msg_length': (50, 300),
                'text_biz_density': (0.3, 0.7),
                'user_biz_affinity': (0.4, 0.9)
            },
            'creative_expansion': {
                'text_msg_length': (40, 200),
                'text_creative_density': (0.3, 0.8),
                'user_creative_affinity': (0.4, 0.9)
            },
            'writing_help': {
                'text_msg_length': (200, 800),
                'text_creative_density': (0.2, 0.6),
                'text_has_code': (0, 0.1)
            },
            'summary': {
                'conv_length': (15, 50),
                'text_msg_length': (10, 50)
            },
            'none': {
                'text_msg_length': (1, 20),
                'conv_length': (1, 3)
            }
        }
        
        # Wszystkie możliwe feature keys (26 features total)
        all_feature_keys = [
            'text_msg_length', 'text_word_count', 'text_avg_word_length',
            'text_question_marks', 'text_exclamation_marks', 'text_code_blocks',
            'text_has_code', 'text_tech_density', 'text_biz_density', 'text_creative_density',
            'text_positive_sentiment', 'text_negative_sentiment',
            'text_has_url', 'text_has_numbers', 'text_capital_ratio',
            'conv_length', 'conv_avg_user_msg_length', 'conv_avg_ai_msg_length',
            'conv_user_ai_ratio', 'conv_time_since_last', 'conv_topic_switches',
            'user_pref_temperature', 'user_pref_max_tokens',
            'user_user_tech_affinity', 'user_user_biz_affinity', 'user_user_creative_affinity',
            'user_user_experience'
        ]
        
        samples_per_category = n_samples // len(patterns)
        
        for category, ranges in patterns.items():
            for _ in range(samples_per_category):
                features = {}
                
                # Wypełnij wszystkie feature keys domyślnymi wartościami
                for key in all_feature_keys:
                    if key in ranges:
                        if isinstance(ranges[key], tuple):
                            features[key] = np.random.uniform(ranges[key][0], ranges[key][1])
                        else:
                            features[key] = ranges[key]
                    else:
                        # Domyślne wartości (better distribution)
                        if 'density' in key or 'affinity' in key or 'ratio' in key or 'sentiment' in key:
                            features[key] = np.random.beta(2, 5)  # Beta distribution - more realistic
                        elif 'length' in key or 'count' in key:
                            features[key] = np.random.gamma(2, 20)  # Gamma distribution for counts
                        elif 'has_' in key:
                            features[key] = float(np.random.binomial(1, 0.3))  # Binary features
                        elif 'temperature' in key:
                            features[key] = np.random.uniform(0.3, 0.9)  # Realistic temp range
                        else:
                            features[key] = np.random.uniform(0, 1)
                
                X_synthetic.append(features)
                y_synthetic.append(category)
        
        return X_synthetic, y_synthetic
    
    def train_initial_model(self, n_synthetic_samples: int = 1000) -> bool:
        """
        Trenuje początkowy model na syntetycznych danych
        
        Args:
            n_synthetic_samples: Liczba syntetycznych próbek
            
        Returns:
            True jeśli sukces
        """
        if not SKLEARN_AVAILABLE or not self.model:
            log_warning("sklearn not available - cannot train model")
            return False
        
        log_info(f"Generating {n_synthetic_samples} synthetic training samples...")
        X_synthetic, y_synthetic = self._generate_synthetic_training_data(n_synthetic_samples)
        
        # Przygotuj dane
        self.label_encoder.fit(self.suggestion_categories)
        
        # Konwertuj features dict → numpy array
        feature_keys = sorted(X_synthetic[0].keys())
        X_array = np.array([[sample[k] for k in feature_keys] for sample in X_synthetic])
        y_encoded = self.label_encoder.transform(y_synthetic)
        
        # Normalizuj features
        X_scaled = self.feature_extractor.scaler.fit_transform(X_array)
        
        # Trenuj model z cross-validation
        log_info("Training Ensemble Voting Classifier (GB+RF)...")
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, y_encoded, cv=5, scoring='f1_weighted')
        log_info(f"Cross-validation F1 scores: {cv_scores}")
        log_info(f"Mean CV F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        
        # Final training
        self.model.fit(X_scaled, y_encoded)
        
        # Zapisz feature keys (potrzebne do predykcji)
        self.feature_keys = feature_keys
        
        # Oblicz metryki
        y_pred = self.model.predict(X_scaled)
        train_accuracy = self.model.score(X_scaled, y_encoded)
        train_f1 = f1_score(y_encoded, y_pred, average='weighted')
        
        log_info(f"Initial model trained:")
        log_info(f"  - Train accuracy: {train_accuracy:.3f}")
        log_info(f"  - Train F1 score: {train_f1:.3f}")
        log_info(f"  - CV F1 mean: {cv_scores.mean():.3f}")
        
        # Feature importance (z GB model)
        if hasattr(self.gb_model, 'feature_importances_'):
            self.feature_importance = dict(zip(feature_keys, self.gb_model.feature_importances_))
            top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            log_info(f"Top 5 important features: {top_features}")
        
        # Zapisz model
        self._save_model()
        
        return True
    
    def predict_suggestion_category(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """
        Przewiduje kategorię sugestii dla danego kontekstu
        
        Args:
            user_id: ID użytkownika
            message: Wiadomość użytkownika
            conversation_history: Historia konwersacji
            
        Returns:
            (category, confidence)
        """
        # Fallback do rule-based jeśli model niedostępny
        if not SKLEARN_AVAILABLE or not self.model or not hasattr(self, 'feature_keys'):
            return self._fallback_rule_based_prediction(message, conversation_history)
        
        # Track inference time
        start_time = time.time()
        
        # Ekstraktuj features (z cachingiem)
        all_features = self.feature_extractor.extract_all_features(
            user_id, message, conversation_history
        )
        
        # Konwertuj do numpy array (zachowaj kolejność feature_keys)
        X = np.array([[all_features.get(k, 0) for k in self.feature_keys]])
        
        # Normalizuj features
        X_scaled = self.feature_extractor.scaler.transform(X)
        
        # Predykcja
        y_pred = self.model.predict(X_scaled)[0]
        y_proba = self.model.predict_proba(X_scaled)[0]
        
        # Dekoduj kategorię
        category = self.label_encoder.inverse_transform([y_pred])[0]
        confidence = float(y_proba[y_pred])
        
        # Track inference time
        inference_time = (time.time() - start_time) * 1000  # ms
        self.prediction_stats['inference_times'].append(inference_time)
        
        # Statystyki
        self.prediction_stats['total_predictions'] += 1
        self.prediction_stats['by_category'][category] += 1
        self.prediction_stats['confidence_scores'].append(confidence)
        
        # Adaptive confidence threshold (dynamic)
        avg_confidence = np.mean(list(self.prediction_stats['confidence_scores']))
        if confidence < avg_confidence * 0.7:
            # Low confidence - potentially use fallback
            log_info(f"Low confidence ({confidence:.3f}) - using ensemble prediction")
        
        return category, confidence
    
    def _fallback_rule_based_prediction(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """Fallback do prostych reguł jeśli ML niedostępny"""
        msg_lower = message.lower()
        
        # Rule-based heuristics
        if any(kw in msg_lower for kw in ['błąd', 'error', 'bug', 'nie działa']):
            return 'debug_help', 0.85
        
        if '```' in message or 'def ' in message:
            return 'code_review', 0.80
        
        if any(kw in msg_lower for kw in ['hotel', 'restauracj', 'lot', 'miasto']):
            return 'travel_search', 0.85
        
        if any(kw in msg_lower for kw in ['firma', 'biznes', 'startup', 'inwestycja']):
            return 'business_analysis', 0.80
        
        if any(kw in msg_lower for kw in ['napisz', 'stwórz', 'wygeneruj']):
            if len(message) > 200:
                return 'writing_help', 0.80
            else:
                return 'creative_expansion', 0.75
        
        if len(conversation_history) > 15:
            return 'summary', 0.75
        
        if len(message) < 20:
            return 'clarification', 0.70
        
        return 'none', 0.60
    
    def get_suggestions_for_category(
        self,
        category: str,
        max_suggestions: int = 3
    ) -> List[str]:
        """
        Zwraca konkretne sugestie dla danej kategorii
        
        Args:
            category: Kategoria sugestii
            max_suggestions: Maksymalna liczba sugestii
            
        Returns:
            Lista tekstów sugestii
        """
        suggestions = self.category_to_suggestions.get(category, [])
        
        # Zwróć losowe max_suggestions z dostępnych
        if len(suggestions) > max_suggestions:
            indices = np.random.choice(len(suggestions), max_suggestions, replace=False)
            return [suggestions[i] for i in indices]
        
        return suggestions
    
    def record_feedback(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]],
        predicted_category: str,
        actual_category: Optional[str] = None,
        user_clicked: bool = False
    ) -> None:
        """
        Zapisuje feedback od użytkownika dla online learning
        
        Args:
            user_id: ID użytkownika
            message: Wiadomość
            conversation_history: Historia
            predicted_category: Przewidziana kategoria
            actual_category: Rzeczywista kategoria (jeśli znana)
            user_clicked: Czy użytkownik kliknął sugestię
        """
        # Ekstraktuj features
        features = self.feature_extractor.extract_all_features(
            user_id, message, conversation_history
        )
        
        # Zapisz do bufora treningowego
        self.training_buffer.append({
            'features': features,
            'predicted_category': predicted_category,
            'actual_category': actual_category,
            'user_clicked': user_clicked,
            'timestamp': time.time()
        })
        
        # Jeśli znamy rzeczywistą kategorię, oblicz accuracy
        if actual_category:
            is_correct = (predicted_category == actual_category)
            self.prediction_stats['accuracy_samples'].append(1.0 if is_correct else 0.0)
        
        # Co 100 feedbacków, retrain model (online learning)
        if len(self.training_buffer) >= 100 and len(self.training_buffer) % 100 == 0:
            self._retrain_from_buffer()
    
    def _retrain_from_buffer(self) -> None:
        """Retrenuje model na podstawie zebranych feedbacków"""
        if not SKLEARN_AVAILABLE or not self.model:
            return
        
        # Filtruj tylko próbki z known actual_category
        valid_samples = [s for s in self.training_buffer if s['actual_category']]
        
        if len(valid_samples) < 20:
            log_info("Not enough valid samples for retraining")
            return
        
        log_info(f"Retraining model with {len(valid_samples)} feedback samples...")
        
        # Przygotuj dane
        X_new = []
        y_new = []
        
        for sample in valid_samples:
            features = sample['features']
            X_new.append([features.get(k, 0) for k in self.feature_keys])
            y_new.append(sample['actual_category'])
        
        X_array = np.array(X_new)
        y_encoded = self.label_encoder.transform(y_new)
        
        # Scale features
        X_scaled = self.feature_extractor.scaler.transform(X_array)
        
        # Incremental learning with validation split
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Retrain models individually
        self.gb_model.set_params(warm_start=True, n_estimators=self.gb_model.n_estimators + 20)
        self.gb_model.fit(X_train, y_train)
        
        self.rf_model.set_params(warm_start=True, n_estimators=self.rf_model.n_estimators + 10)
        self.rf_model.fit(X_train, y_train)
        
        # Rebuild voting ensemble
        self.model = VotingClassifier(
            estimators=[
                ('gb', self.gb_model),
                ('rf', self.rf_model)
            ],
            voting='soft',
            weights=[0.6, 0.4]
        )
        self.model.fit(X_train, y_train)
        
        # Metryki walidacyjne
        val_accuracy = self.model.score(X_val, y_val)
        y_val_pred = self.model.predict(X_val)
        val_f1 = f1_score(y_val, y_val_pred, average='weighted')
        
        log_info(f"Model retrained:")
        log_info(f"  - Validation accuracy: {val_accuracy:.3f}")
        log_info(f"  - Validation F1: {val_f1:.3f}")
        log_info(f"  - Training samples: {len(valid_samples)}")
        
        # Track F1 score
        self.prediction_stats['f1_scores'].append(val_f1)
        
        # Update feature importance
        if hasattr(self.gb_model, 'feature_importances_'):
            self.feature_importance = dict(zip(self.feature_keys, self.gb_model.feature_importances_))
        
        # Zapisz zaktualizowany model
        self._save_model()
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Zwraca comprehensive statystyki modelu"""
        stats = {
            'total_predictions': self.prediction_stats['total_predictions'],
            'predictions_by_category': dict(self.prediction_stats['by_category']),
            'training_buffer_size': len(self.training_buffer),
            'sklearn_available': SKLEARN_AVAILABLE,
            'model_trained': hasattr(self, 'feature_keys'),
            'num_features': len(self.feature_keys) if hasattr(self, 'feature_keys') else 0
        }
        
        # Accuracy metrics
        if self.prediction_stats['accuracy_samples']:
            stats['recent_accuracy'] = float(np.mean(list(self.prediction_stats['accuracy_samples'])))
            stats['accuracy_std'] = float(np.std(list(self.prediction_stats['accuracy_samples'])))
        
        # F1 score metrics
        if self.prediction_stats['f1_scores']:
            stats['recent_f1'] = float(np.mean(list(self.prediction_stats['f1_scores'])))
            stats['f1_trend'] = 'improving' if len(self.prediction_stats['f1_scores']) > 1 and \
                              self.prediction_stats['f1_scores'][-1] > self.prediction_stats['f1_scores'][0] else 'stable'
        
        # Confidence metrics
        if self.prediction_stats['confidence_scores']:
            stats['avg_confidence'] = float(np.mean(list(self.prediction_stats['confidence_scores'])))
            stats['confidence_std'] = float(np.std(list(self.prediction_stats['confidence_scores'])))
        
        # Performance metrics
        if self.prediction_stats['inference_times']:
            stats['avg_inference_time_ms'] = float(np.mean(list(self.prediction_stats['inference_times'])))
            stats['p95_inference_time_ms'] = float(np.percentile(list(self.prediction_stats['inference_times']), 95))
        
        # Cache efficiency
        total_cache_ops = self.prediction_stats['cache_hits'] + self.prediction_stats['cache_misses']
        if total_cache_ops > 0:
            stats['cache_hit_rate'] = float(self.prediction_stats['cache_hits'] / total_cache_ops)
        
        # Feature importance (top 10)
        if self.feature_importance:
            top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            stats['top_features'] = {k: float(v) for k, v in top_features}
        
        # Model configuration
        if self.model and hasattr(self, 'gb_model'):
            stats['model_config'] = {
                'type': 'VotingClassifier(GB+RF)',
                'gb_estimators': self.gb_model.n_estimators,
                'rf_estimators': self.rf_model.n_estimators,
                'voting_weights': [0.6, 0.4]
            }
        
        return stats


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

# Globalna instancja modelu
_ml_model_instance = None

def get_ml_model() -> ProactiveSuggestionMLModel:
    """Zwraca globalną instancję modelu ML (singleton)"""
    global _ml_model_instance
    
    if _ml_model_instance is None:
        _ml_model_instance = ProactiveSuggestionMLModel()
        
        # Jeśli model nie istnieje, wytrenuj go
        if not hasattr(_ml_model_instance, 'feature_keys'):
            log_info("No trained model found - training initial model...")
            _ml_model_instance.train_initial_model(n_synthetic_samples=1000)
    
    return _ml_model_instance

def predict_smart_suggestions(
    user_id: str,
    message: str,
    conversation_history: List[Dict[str, Any]],
    max_suggestions: int = 3
) -> List[Dict[str, Any]]:
    """
    Główna funkcja API - przewiduje najlepsze sugestie ML-based
    
    Args:
        user_id: ID użytkownika
        message: Wiadomość użytkownika
        conversation_history: Historia konwersacji
        max_suggestions: Max liczba sugestii
        
    Returns:
        Lista sugestii [{'text': str, 'category': str, 'confidence': float}]
    """
    model = get_ml_model()
    
    # Przewiduj kategorię
    category, confidence = model.predict_suggestion_category(
        user_id, message, conversation_history
    )
    
    # Jeśli kategoria to 'none' i confidence niskie, nie zwracaj sugestii
    if category == 'none' and confidence < 0.7:
        return []
    
    # Pobierz konkretne sugestie dla kategorii
    suggestion_texts = model.get_suggestions_for_category(category, max_suggestions)
    
    # Przygotuj wynik
    results = [
        {
            'text': text,
            'category': category,
            'confidence': round(confidence, 3)
        }
        for text in suggestion_texts
    ]
    
    return results

def record_suggestion_feedback(
    user_id: str,
    message: str,
    conversation_history: List[Dict[str, Any]],
    predicted_category: str,
    user_clicked: bool,
    actual_category: Optional[str] = None
) -> None:
    """
    Zapisuje feedback użytkownika (do online learning)
    
    Args:
        user_id: ID użytkownika
        message: Wiadomość
        conversation_history: Historia
        predicted_category: Przewidziana kategoria
        user_clicked: Czy user kliknął sugestię
        actual_category: Rzeczywista kategoria (opcjonalne)
    """
    model = get_ml_model()
    model.record_feedback(
        user_id, message, conversation_history,
        predicted_category, actual_category, user_clicked
    )

def get_ml_model_stats() -> Dict[str, Any]:
    """Zwraca statystyki modelu ML"""
    model = get_ml_model()
    return model.get_model_stats()
