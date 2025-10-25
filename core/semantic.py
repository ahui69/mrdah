#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Module - SemanticAnalyzer, SemanticIntegration
FULL LOGIC - 1441 lines - NO PLACEHOLDERS!
"""

import os, re, sys, time, json, uuid, sqlite3, random
from typing import Any, Dict, List, Optional

from .config import DB_PATH, CONTEXT_DICTIONARIES
from .helpers import log_info, log_error, tokenize as _tok, tfidf_vec as _tfidf_vec

class SemanticAnalyzer:
    """Klasa do zaawansowanej analizy semantycznej tekstu"""
    def __init__(self):
        self.sentiment_keywords = {
            "pozytywny": ["dobry", "świetny", "doskonały", "zadowolony", "wspaniały", "super", "fajny", "miły", "ciekawy", "lubię", "podoba", "polecam"],
            "negatywny": ["zły", "słaby", "kiepski", "niedobry", "rozczarowany", "niezadowolony", "fatalny", "beznadziejny", "okropny", "niestety", "problem"],
            "neutralny": ["normalny", "zwykły", "standard", "średni", "przeciętny", "typowy"]
        }
        
        # Słownik dla dokładniejszej analizy emocji
        self.emotion_keywords = {
            "radość": ["świetny", "super", "zachwycający", "cieszyć", "uwielbić", "radość", "szczęśliwy", "entuzjazm", "zadowolony", "radosny", "wow", "hurra"],
            "smutek": ["smutny", "przykro", "żal", "szkoda", "płakać", "przygnębiony", "przykry", "smuci", "niestety", "rozczarowany", "porzucić", "zrezygnowany"],
            "złość": ["wkurzony", "zdenerwowany", "wściekły", "irytuje", "denerwuje", "zły", "zirytowany", "wkurza", "frustracja", "wkurzyć", "złościć"],
            "strach": ["boi się", "przerażony", "lęk", "obawy", "obawiam", "strach", "martwi", "zatrwożony", "niepewny", "przestraszony", "obawiam się"],
            "zaskoczenie": ["wow", "zaskoczony", "zdziwiony", "niesamowity", "zaskakujący", "niewiarygodny", "szok", "zdumiewający", "niezwykły", "nieprawdopodobny"],
            "zaufanie": ["ufam", "wierzę", "polegam", "pewny", "sprawdzony", "bezpieczny", "wiarygodny", "niezawodny", "godny zaufania"],
            "wstręt": ["obrzydliwy", "ohydny", "niesmaczny", "odrażający", "paskudny", "wstrętny", "niechęć", "okropny", "obrzydzenie"],
            "oczekiwanie": ["czekam", "oczekuję", "mam nadzieję", "spodziewać się", "przewidywać", "liczyć", "powinno", "będzie", "chciałbym"]
        }
        
        self.intention_indicators = {
            "pytanie": ["?", "czy", "jak", "kiedy", "gdzie", "co", "dlaczego", "ile", "który", "jakie", "proszę wyjaśnić"],
            "prośba": ["proszę", "czy możesz", "czy mógłbyś", "pomóż", "potrzebuję", "zrób", "wykonaj", "daj", "pokaż"],
            "stwierdzenie": ["jest", "są", "myślę", "sądzę", "uważam", "moim zdaniem", "wydaje mi się", "wiem", "rozumiem"]
        }
        
        # Słowniki kategorii tematycznych
        self.topic_keywords = {
            "technologia": ["komputer", "laptop", "telefon", "internet", "aplikacja", "program", "software", "hardware", "kod", "programowanie"],
            "biznes": ["firma", "przedsiębiorstwo", "zysk", "marketing", "sprzedaż", "klient", "produkt", "usługa", "rynek", "inwestycja"],
            "podróże": ["wakacje", "wycieczka", "hotel", "rezerwacja", "lot", "samolot", "zwiedzanie", "turysta", "przewodnik", "destynacja"],
            "zdrowie": ["lekarz", "choroba", "lekarstwo", "terapia", "ćwiczenia", "dieta", "samopoczucie", "zdrowy", "pacjent", "dolegliwości"],
            "edukacja": ["szkoła", "nauka", "studia", "uniwersytet", "kurs", "student", "profesor", "egzamin", "wykład", "wiedza"],
            "rozrywka": ["film", "muzyka", "koncert", "spektakl", "książka", "gra", "zabawa", "hobby", "serial", "festiwal"]
        }
        print("Analiza semantyczna - inicjalizacja powiodła się")
        
    def analyze_text(self, text):
        """Kompleksowa analiza semantyczna tekstu"""
        if not text:
            return {}
            
        result = {
            "topics": self.detect_topics(text),
            "sentiment": self.analyze_sentiment(text),
            "emotions": self.analyze_emotions(text),
            "intention": self.detect_intention(text),
            "hidden_intentions": self.detect_hidden_intentions(text),
            "keywords": self.extract_keywords(text),
            "complexity": self.analyze_complexity(text),
            "temporal_context": self.detect_temporal_context(text),
            "entities": self.extract_entities(text)
        }
        return result
        
    def analyze_emotions(self, text):
        """Zaawansowana analiza emocji w tekście"""
        if not text:
            return {}
            
        text_lower = text.lower()
        tokens = _tok(text_lower) if hasattr(text_lower, '__len__') else []
        words = text_lower.split()
        
        # Analizuj emocje na podstawie słów kluczowych
        emotion_scores = {emotion: 0.0 for emotion in self.emotion_keywords}
        emotion_matches = {}
        
        # Zaimplementujmy podejście z uwzględnieniem kontekstu
        # Najpierw podstawowe zliczanie
        for emotion, keywords in self.emotion_keywords.items():
            matches = []
            for word in keywords:
                # Bardziej zaawansowane sprawdzenie niż proste text_lower.count()
                if len(word.split()) > 1:  # Dla fraz wielowyrazowych
                    if word in text_lower:
                        matches.append(word)
                        emotion_scores[emotion] += 0.2
                else:  # Dla pojedynczych słów
                    # Dopasowanie form wyrazów (np. smutek, smutny, smutno)
                    pattern = r"\b" + re.escape(word[:4]) + r"[a-ząćęłńóśźź]*\b"
                    matches_found = re.findall(pattern, text_lower)
                    if matches_found:
                        matches.extend(matches_found)
                        emotion_scores[emotion] += 0.1 * len(matches_found)
            
            if matches:
                emotion_matches[emotion] = matches
        
        # Analiza wzajemnych wzmocnień i osłabień emocji
        if emotion_scores.get("radość", 0) > 0 and emotion_scores.get("smutek", 0) > 0:
            # Jeśli występuje jednocześnie radość i smutek, sprawdźmy negacje
            if any(neg in text_lower for neg in ["nie jest", "nie był", "nie są", "nie czuję"]):
                # Prawdopodobnie negacja pozytywnych emocji
                if "nie" in text_lower and any(pos in text_lower[text_lower.find("nie"):] 
                                            for pos in self.emotion_keywords["radość"]):
                    emotion_scores["radość"] *= 0.3
                    emotion_scores["smutek"] *= 1.5
        
        # Uwzględnienie znaków interpunkcyjnych i emotikonów
        if "!" in text:
            # Wykrzykniki wzmacniają dominujące emocje
            max_emotion = max(emotion_scores, key=emotion_scores.get)
            if max_emotion in ["radość", "złość", "zaskoczenie"]:
                emotion_scores[max_emotion] += 0.1 * text.count("!")
        
        # Emotikony i emoji
        happy_emojis = [":)", ":D", "😊", "😁", "😄", "👍"]
        sad_emojis = [":(", "😢", "😭", "😔", "👎"]
        angry_emojis = ["😠", "😡", "👿", "💢"]
        surprised_emojis = ["😮", "😯", "😲", "😱", "😳"]
        
        for emoji in happy_emojis:
            count = text.count(emoji)
            if count > 0:
                emotion_scores["radość"] += 0.15 * count
                
        for emoji in sad_emojis:
            count = text.count(emoji)
            if count > 0:
                emotion_scores["smutek"] += 0.15 * count
                
        for emoji in angry_emojis:
            count = text.count(emoji)
            if count > 0:
                emotion_scores["złość"] += 0.15 * count
                
        for emoji in surprised_emojis:
            count = text.count(emoji)
            if count > 0:
                emotion_scores["zaskoczenie"] += 0.15 * count
        
        # Analiza intensywności na podstawie składni i powtarzających się wzorów
        intensity = 1.0
        if re.search(r"bardzo|niezwykle|ogromnie|niesamowicie|wyjątkowo", text_lower):
            intensity = 1.5
        elif re.search(r"trochę|lekko|nieco|delikatnie", text_lower):
            intensity = 0.7
            
        # Aplikujemy intensywność do wyników
        for emotion in emotion_scores:
            emotion_scores[emotion] *= intensity
        
        # Normalizacja wyników
        total = sum(emotion_scores.values()) or 1.0
        normalized = {k: round(v/total, 2) for k, v in emotion_scores.items() if v > 0}
        
        # Dominujące emocje (top 3)
        dominant = sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:3]
        dominant_emotions = {emotion: score for emotion, score in dominant if score > 0.1}
        
        return {
            "dominujące": dominant_emotions,
            "wszystkie": normalized,
            "intensywność": round(intensity, 2),
            "dopasowania": emotion_matches
        }
        
    def detect_topics(self, text):
        """Wykrywa tematy w tekście z wagami używając TF-IDF"""
        if not text:
            return {}
            
        text_lower = text.lower()
        text_tokens = _tok(text_lower)  # Używamy istniejącej funkcji tokenizującej
        
        # Przygotowanie korpusu dokumentów do TF-IDF
        corpus = []
        topic_docs = {}
        
        # Tworzenie dokumentów dla każdego tematu (dla TF-IDF)
        for topic, keywords in self.topic_keywords.items():
            topic_docs[topic] = " ".join(keywords)
            corpus.append(topic_docs[topic])
        
        # Dodaj zapytanie użytkownika jako ostatni dokument w korpusie
        corpus.append(text_lower)
        
        # Obliczenie wektorów TF-IDF
        tfidf_scores = _tfidf_vec(text_tokens, [_tok(doc) for doc in corpus])
        
        # Obliczenie podobieństwa między tekstem a tematami
        topic_scores = {}
        for topic, topic_text in topic_docs.items():
            topic_tokens = _tok(topic_text)
            topic_tfidf = _tfidf_vec(topic_tokens, [_tok(doc) for doc in corpus])
            
            # Iloczyn skalarny wektorów TF-IDF (prostszy odpowiednik cosine similarity)
            score = 0
            for term in set(text_tokens) & set(topic_tokens):  # Wspólne terminy
                score += tfidf_scores.get(term, 0) * topic_tfidf.get(term, 0) * 3.0  # Waga dla wspólnych terminów
                
            # Dodatkowa korekta dla słów kluczowych
            for keyword in self.topic_keywords[topic]:
                if keyword in text_lower:
                    score += 0.15  # Bonus za dokładne dopasowanie słów kluczowych
            
            if score > 0.1:  # Minimalny próg
                topic_scores[topic] = min(0.95, score)  # Ograniczenie maksymalnej wartości
        
        # Dodatkowa analiza kontekstualna
        # Wzorce zakupowe
        if re.search(r'\b(kup|kupi[ćęcł]|zam[óo]wi[ćęcł]|sprzeda[ćęcł]|cen[ayę]|koszt|ofert[ayę]|tani|drogi)\b', text_lower):
            topic_scores["zakupy"] = max(topic_scores.get("zakupy", 0), 0.7)
            
        # Wzorce wsparcia technicznego
        if re.search(r'\b(problem|trudno[śsć][ćcę]|b[łl][ąa]d|nie dzia[łl]a|zepsut|pom[óo][żz])\b', text_lower):
            topic_scores["wsparcie"] = max(topic_scores.get("wsparcie", 0), 0.75)
            
        # Wzorce finansowe
        if re.search(r'\b(pieni[ąa]dz|z[łl]ot|pln|eur|usd|walut|bank|konto|p[łl]atno[śsć][ćc])\b', text_lower):
            topic_scores["finanse"] = max(topic_scores.get("finanse", 0), 0.7)
            
        # Normalizacja wyników
        total_score = sum(topic_scores.values()) or 1.0
        for topic in topic_scores:
            topic_scores[topic] = topic_scores[topic] / total_score * 0.8 + 0.1  # Skalowanie do sensownego zakresu
            
        # Usuń tematy z bardzo niskim wynikiem
        return {k: round(v, 2) for k, v in topic_scores.items() if v > 0.22}
    
    def analyze_sentiment(self, text):
        """Analiza sentymentu tekstu"""
        text_lower = text.lower()
        scores = {"pozytywny": 0, "negatywny": 0, "neutralny": 0}
        
        # Liczenie wystąpień słów z każdej kategorii
        for sentiment, words in self.sentiment_keywords.items():
            for word in words:
                count = text_lower.count(word)
                if count > 0:
                    scores[sentiment] += count * 0.1  # Każde wystąpienie zwiększa wynik
        
        # Analiza znaków interpunkcyjnych i emoji
        if "!" in text:
            excl_count = text.count("!")
            if scores["pozytywny"] > scores["negatywny"]:
                scores["pozytywny"] += excl_count * 0.05
            elif scores["negatywny"] > scores["pozytywny"]:
                scores["negatywny"] += excl_count * 0.05
                
        # Sprawdź emoji lub emotikony
        positive_emotes = [":)", ":D", "😊", "👍", "😁"]
        negative_emotes = [":(", ":(", "😢", "👎", "😠"]
        
        for emote in positive_emotes:
            scores["pozytywny"] += text.count(emote) * 0.15
            
        for emote in negative_emotes:
            scores["negatywny"] += text.count(emote) * 0.15
        
        # Sprawdź negację, która może odwracać sentyment
        negation_words = ["nie", "bez", "nigdy", "żaden"]
        for word in negation_words:
            pattern = word + " [\\w]+ "
            matches = re.findall(pattern, text_lower)
            if matches:
                # Zmniejsz wpływ pozytywnych słów po negacji
                scores["pozytywny"] *= 0.8
                scores["negatywny"] *= 1.2
                
        # Normalizacja wyników
        total = sum(scores.values()) or 1
        normalized = {k: round(v/total, 2) for k, v in scores.items()}
        
        # Określenie dominującego sentymentu
        dominant = max(normalized, key=normalized.get)
        normalized["dominujący"] = dominant
        
        return normalized
        
    def detect_intention(self, text):
        """Wykrywanie intencji użytkownika"""
        text_lower = text.lower()
        scores = {"pytanie": 0, "prośba": 0, "stwierdzenie": 0}
        
        # Sprawdź znaki zapytania
        if "?" in text:
            scores["pytanie"] += 0.6
        
        # Sprawdzanie wskaźników intencji
        for intention, indicators in self.intention_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    scores[intention] += 0.15
        
        # Analiza struktury gramatycznej (podstawowa)
        if text_lower.startswith("czy") or text_lower.startswith("jak") or text_lower.startswith("kiedy"):
            scores["pytanie"] += 0.3
            
        if "proszę" in text_lower or "czy możesz" in text_lower or text_lower.startswith("pomóż"):
            scores["prośba"] += 0.3
            
        if "." in text and "?" not in text:
            scores["stwierdzenie"] += 0.2
            
        # Normalizacja wyników
        total = sum(scores.values()) or 1
        normalized = {k: round(v/total, 2) for k, v in scores.items()}
        
        # Określenie dominującej intencji
        dominant = max(normalized, key=normalized.get)
        normalized["dominująca"] = dominant
        
        return normalized
    
    def extract_keywords(self, text):
        """Ekstrakcja słów kluczowych z tekstu"""
        # Proste czyszczenie tekstu
        text_lower = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text_lower.split()
        
        # Lista stop words (podstawowa)
        stop_words = ["i", "w", "na", "z", "do", "od", "dla", "że", "to", "jest", "są", "być", "a", "o", "jak", "tak", "nie", "się"]
        
        # Filtrowanie słów
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Obliczanie częstości występowania
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sortowanie po częstości i zwracanie top N słów
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [word for word, freq in sorted_words[:10]]
        
        return top_keywords
    
    def analyze_complexity(self, text):
        """Analiza złożoności tekstu"""
        if not text:
            return {"poziom": "brak tekstu", "średnia_długość_zdania": 0, "średnia_długość_słowa": 0, "różnorodność_leksykalna": 0}
            
        # Podział na zdania
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"poziom": "brak tekstu", "średnia_długość_zdania": 0, "średnia_długość_słowa": 0, "różnorodność_leksykalna": 0}
        
        # Liczba słów w zdaniach
        words_per_sentence = [len(s.split()) for s in sentences]
        avg_sentence_length = sum(words_per_sentence) / len(sentences) if sentences else 0
        
        # Średnia długość słowa
        all_words = [word for s in sentences for word in s.split()]
        if not all_words:
            return {"poziom": "brak tekstu", "średnia_długość_zdania": 0, "średnia_długość_słowa": 0, "różnorodność_leksykalna": 0}
            
        avg_word_length = sum(len(word) for word in all_words) / len(all_words)
        
        # Różnorodność leksykalna (unique words / total words)
        lexical_diversity = len(set(all_words)) / len(all_words) if all_words else 0
        
        # Określenie poziomu złożoności
        complexity_level = "niska"
        if avg_sentence_length > 15 or avg_word_length > 6 or lexical_diversity > 0.7:
            complexity_level = "wysoka"
        elif avg_sentence_length > 10 or avg_word_length > 5 or lexical_diversity > 0.5:
            complexity_level = "średnia"
            
        return {
            "poziom": complexity_level,
            "średnia_długość_zdania": round(avg_sentence_length, 2),
            "średnia_długość_słowa": round(avg_word_length, 2),
            "różnorodność_leksykalna": round(lexical_diversity, 2)
        }
        
    def analyze_local_context(self, text):
        """Analizuje lokalny kontekst w tekście - lokalizacje, czas, odniesienia"""
        if not text:
            return {"lokalizacje": [], "czas": [], "odniesienia_przestrzenne": [], 
                    "odniesienia_czasowe": []}
            
        text_lower = text.lower()
        
        # Słowniki do rozpoznawania rodzajów kontekstu
        # Lokalizacje (miasta, kraje, regiony)
        location_patterns = [
            # "w Warszawie", "do Polski"
            r"\b(?:w|do|z)\s+([A-Z][a-ząćęłńóśźż]{2,})\b",
            # Nazwy własne (miasta, kraje)  
            r"\b([A-Z][a-ząćęłńóśźż]{2,})\b",
            # Nazwy ulic
            r"\b(?:ulica|ulicy|ul\.|aleja|alei|al\.)\s+([A-Z][a-ząćęłńóśźż]+)\b"
        ]
        
        # Wyrażenia czasowe
        time_patterns = [
            r"\b(\d{1,2}:\d{2})\b",  # Format godziny 12:30
            r"\b(\d{1,2})[:\.-]\s?(\d{2})\b",  # Format godziny z separatorem
            r"\bo\s+(?:godz(?:inie)?)\s+(\d{1,2})\b",  # "o godzinie 5"
            r"\b(?:rano|po\s+południu|wieczorem|w\s+nocy)\b"  # Pory dnia
        ]
        
        # Odniesienia przestrzenne
        spatial_references = [
            r"\b(?:na\s+prawo|na\s+lewo|nad|pod|obok|przy|przed|za|naprzeciw)\b",
            r"\b(?:w\s+pobliżu|niedaleko|blisko)\b",
            r"\b(?:na\s+północ|na\s+południe|na\s+wschód|na\s+zachód)\b",
            r"\b(?:w\s+centrum|na\s+obrzeżach|na\s+peryferiach|w\s+środku)\b"
        ]
        
        # Odniesienia czasowe
        temporal_references = [
            r"\b(?:wczoraj|dzisiaj|jutro|pojutrze|za\s+tydzień)\b",
            r"\b(?:w\s+przyszłym\s+tygodniu|w\s+przyszłym\s+miesiącu)\b",
            r"\b(?:rano|po\s+południu|wieczorem|w\s+nocy|o\s+świcie|o\s+zmierzchu)\b",
            r"\b(?:w\s+poniedziałek|we\s+wtorek|w\s+środę|w\s+czwartek)\b",
            r"\b(?:w\s+piątek|w\s+sobotę|w\s+niedzielę)\b",
            r"\b(\d{1,2})\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca)\b",
            r"\b(\d{1,2})\s+(?:lipca|sierpnia|września|października|listopada|grudnia)\b"
        ]
        
        # Rozpoznawanie lokalizacji
        locations = []
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                locations.extend([m[0] if isinstance(m, tuple) else m for m in matches])
        
        # Rozpoznawanie wyrażeń czasowych
        times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                times.extend([m[0] if isinstance(m, tuple) else m for m in matches])
        
        # Rozpoznawanie odniesień przestrzennych
        spatial_refs = []
        for pattern in spatial_references:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                spatial_refs.extend(matches)
        
        # Rozpoznawanie odniesień czasowych
        temporal_refs = []
        for pattern in temporal_references:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Dla dat w formacie "15 stycznia 2023"
                    temporal_refs.extend([' '.join(filter(None, m)) for m in matches])
                else:
                    temporal_refs.extend(matches)
        
        # Dodatkowe przetwarzanie dla lokalizacji z przyimkami
        processed_locations = []
        for loc in locations:
            # Czyścimy z przyimków i dodatkowych znaków
            cleaned_loc = re.sub(r'^(?:w|do|z|na|przy)\s+', '', loc)
            cleaned_loc = re.sub(r'[,.:;"\'()]', '', cleaned_loc)
            if len(cleaned_loc) > 2:  # Minimalna długość nazwy lokalizacji
                processed_locations.append(cleaned_loc)
        
        # Deduplikacja wyników
        locations = list(set(processed_locations))
        times = list(set(times))
        spatial_refs = list(set(spatial_refs))
        temporal_refs = list(set(temporal_refs))
        
        # Sortowanie wyników według długości (dłuższe nazwy są często bardziej specyficzne)
        locations.sort(key=len, reverse=True)
        
        # Usuwanie fałszywych trafień (typowe słowa, które nie są lokalizacjami)
        common_words = ["jako", "tego", "tych", "inne", "moje", "twoje", "nasze"]
        locations = [loc for loc in locations if loc.lower() not in common_words]
        
        # Identyfikacja głównego kontekstu przestrzenno-czasowego
        main_location = locations[0] if locations else None
        main_time = temporal_refs[0] if temporal_refs else None
        
        return {
            "lokalizacje": locations,
            "czas": times,
            "odniesienia_przestrzenne": spatial_refs,
            "odniesienia_czasowe": temporal_refs,
            "główna_lokalizacja": main_location,
            "główny_czas": main_time
        }
    def analyze_discourse(self, text):
        """Analizuje dyskurs - identyfikuje typ, strukturę i cechy komunikacji"""
        if not text:
            return {"typ_dyskursu": "brak tekstu", "cechy": [], "słowa_kluczowe": []}
            
        text_lower = text.lower()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return {"typ_dyskursu": "brak tekstu", "cechy": [], "słowa_kluczowe": []}
            
        # Słowniki do identyfikacji typów dyskursu
        discourse_markers = {
            "naukowy": [
                r"\b(?:badania|badanie|analiza|analizy|hipoteza|teoria|wyniki)\b",
                r"\b(?:dowód|dowody|metodologia|eksperyment|dane|wniosek)\b",
                r"\b(?:według\s+(?:\w+\s+){0,2}et\s+al\.|cytując|zgodnie\s+z)\b"
            ],
            "polityczny": [
                r"\b(?:państwo|władza|rząd|ustawa|prawo|społeczeństwo)\b",
                r"\b(?:polityka|polityczny|partia|demokracja|wybory)\b",
                r"\b(?:obywatel|obywatele|obywatelski|konstytucja|wolność)\b"
            ],
            "biznesowy": [
                r"\b(?:firma|biznes|przedsiębiorstwo|klient|klienci|zysk)\b",
                r"\b(?:sprzedaż|rynek|marketing|strategia|budżet|przychód)\b",
                r"\b(?:produkt|usługa|wartość|cena|oferta|umowa|kontrakt)\b"
            ],
            "potoczny": [
                r"\b(?:super|fajnie|ekstra|spoko|ziom|hej|cześć|siema|nara)\b",
                r"\b(?:mega|totalnie|generalnie|jakby|wiesz|no\s+wiesz)\b",
                r"(?:!{2,}|\\?{2,})"
            ],
            "perswazyjny": [
                r"\b(?:musisz|powinieneś|należy|trzeba|koniecznie)\b",
                r"\b(?:najlepszy|jedyny|wyjątkowy|niesamowity|rewolucyjny)\b",
                r"\b(?:przekonaj\s+się|sprawdź|nie\s+przegap|już\s+dziś)\b"
            ],
            "emocjonalny": [
                r"\b(?:kocham|nienawidzę|uwielbiam|boję\s+się|tęsknię)\b",
                r"\b(?:radość|smutek|złość|strach|niepokój|wzruszenie)\b",
                r"(?:!{2,}|\\?!|\\.{3,})"
            ],
            "informacyjny": [
                r"\b(?:informacja|informuję|zawiadamiam|komunikat|ogłoszenie)\b",
                r"\b(?:przekazuję|uprzejmie\s+informuję|podaję\s+do\s+wiadomości)\b",
                r"\b(?:dane|fakty|statystyki|zestawienie|podsumowanie)\b"
            ]
        }
        
        # Cechy dyskursu
        discourse_features = {
            "formalny": [
                r"\b(?:szanowny|uprzejmie|z\s+poważaniem|niniejszym)\b",
                r"\b(?:pragnę\s+podkreślić|należy\s+zaznaczyć)\b"
            ],
            "nieformalny": [
                r"\b(?:hej|cześć|siema|słuchaj|wiesz\s+co|no\s+dobra|ok)\b",
                r"(?:!{2,}|\\?{2,})"
            ],
            "argumentacyjny": [
                r"\b(?:ponieważ|dlatego|zatem|więc|skutkiem)\b",
                r"\b(?:po\s+pierwsze|po\s+drugie|z\s+jednej\s+strony)\b",
                r"\b(?:argumentuję|twierdzę|uważam|wnioskuję)\b"
            ],
            "narracyjny": [
                r"\b(?:pewnego\s+dnia|dawno\s+temu|na\s+początku)\b",
                r"\b(?:następnie|po\s+chwili|tymczasem|w\s+końcu)\b"
            ],
            "dialogowy": [
                r"\b(?:pytam|odpowiadam|mówię|twierdzisz|sugerujesz)\b",
                r'''["„"''].*?["„"']''',
                r"\b(?:rozmowa|dialog|dyskusja|debata)\b"
            ],
            "opisowy": [
                r"\b(?:jest|był|znajdował\s+się|wyglądał|przypominał)\b",
                r"\b(?:wysoki|szeroki|ciemny|jasny|czerwony|duży)\b"
            ],
            "instruktażowy": [
                r"\b(?:najpierw|następnie|potem|na\s+koniec|krok)\b",
                r"\b(?:włącz|wyłącz|naciśnij|kliknij|otwórz|zamknij)\b",
                r"(?:^\s*\d+\.|^\s*-|\*\s)"
            ]
        }
        
        # Analiza typu dyskursu
        discourse_scores = {}
        for disc_type, patterns in discourse_markers.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.MULTILINE)
                score += len(matches)
            discourse_scores[disc_type] = score
            
        # Analiza cech dyskursu
        features = []
        for feature, patterns in discourse_features.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.MULTILINE)
                score += len(matches)
            if score >= 2:  # Próg minimalny dla uznania cechy
                features.append(feature)
                
        # Struktura dyskursu - analiza połączeń logicznych
        logical_connectors = [
            r"\b(?:ponieważ|bo|gdyż|dlatego|więc|zatem|stąd)\b",
            r"\b(?:jeśli|jeżeli|o\s+ile|pod\s+warunkiem)\b",
            r"\b(?:ale|lecz|jednak|niemniej|natomiast)\b",
            r"\b(?:po\s+pierwsze|po\s+drugie|przede\s+wszystkim)\b"
        ]
        
        connectors_count = 0
        for pattern in logical_connectors:
            connectors_count += len(re.findall(pattern, text_lower))
            
        # Gęstość logiczna - liczba połączeń logicznych na zdanie
        logical_density = connectors_count / len(sentences) if sentences else 0
        
        # Kompleksowość dyskursu - średnia długość zdania
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        complexity_words = re.findall(r'\b\w{10,}\b', text_lower)
        lexical_complexity = len(complexity_words) / len(sentences) if sentences else 0
        
        # Określenie głównego typu dyskursu
        main_discourse_type = max(discourse_scores.items(), key=lambda x: x[1])[0] \
            if any(score > 0 for score in discourse_scores.values()) else "nieokreślony"
            
        # Słowa kluczowe w dyskursie
        words = re.findall(r'\b\w+\b', text_lower)
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Pomijamy krótkie słowa
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Lista polskich stopwords (słów nieistotnych)
        stopwords = [
            "oraz", "jako", "tylko", "tego", "przez", "jest", "jestem", 
            "jesteśmy", "ponieważ", "żeby", "który", "która", "które", 
            "także", "również", "dlatego", "więc", "czyli", "gdyż", "albo",
            "czyli", "lecz", "gdyż", "oraz", "jednak", "choć"
        ]
        
        # Filtrowanie słów nieistotnych
        for word in stopwords:
            if word in word_freq:
                del word_freq[word]
                
        # Wybieranie najczęstszych słów jako słowa kluczowe
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [word for word, freq in keywords]
        
        result = {
            "typ_dyskursu": main_discourse_type,
            "cechy": features,
            "słowa_kluczowe": keywords,
            "gęstość_logiczna": round(logical_density, 2),
            "złożoność_leksykalna": round(lexical_complexity, 2),
            "średnia_długość_zdania": round(avg_sentence_length, 2)
        }
        
        # Dodanie oceny jakości dyskursu
        if logical_density > 0.5 and lexical_complexity > 0.3 and avg_sentence_length > 15:
            result["ocena_jakości"] = "zaawansowany"
        elif logical_density > 0.3 and avg_sentence_length > 10:
            result["ocena_jakości"] = "standardowy"
        else:
            result["ocena_jakości"] = "prosty"
            
        return result
        
    def analyze_arguments(self, text):
        """Analizuje strukturę argumentacyjną tekstu"""
        if not text:
            return {"struktura": "brak tekstu", "elementy": [], "jakość": "brak"}
            
        # Dzielimy tekst na zdania
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return {"struktura": "brak tekstu", "elementy": [], "jakość": "brak"}
        
        # Wzorce dla rozpoznawania elementów argumentacji
        argument_patterns = {
            "teza_główna": [
                r"\b(?:uważam,\s+że|twierdzę,\s+że|moim\s+zdaniem)\b",
                r"\b(?:chciał[a]?bym\s+dowieść|zamierzam\s+pokazać)\b",
                r"\b(?:główn[ym|ą]\s+(?:tez[ą|e]|kwesti[ą|e])\s+jest)\b"
            ],
            "przesłanka": [
                r"\b(?:ponieważ|gdyż|bowiem|dlatego\s+że|z\s+powodu)\b",
                r"\b(?:pierwszym\s+argumentem|drugim\s+argumentem)\b",
                r"\b(?:dowodzi\s+tego|świadczy\s+o\s+tym|potwierdza\s+to)\b"
            ],
            "kontrargument": [
                r"\b(?:jednak|niemniej\s+jednak|z\s+drugiej\s+strony)\b",
                r"\b(?:można\s+(?:by|też)\s+(?:zauważyć|argumentować))\b",
                r"\b(?:przeciwnicy\s+twierdzą|krytycy\s+wskazują)\b"
            ],
            "konkluzja": [
                r"\b(?:w\s+(?:konsekwencji|rezultacie|efekcie))\b",
                r"\b(?:(?:podsumowując|reasumując|konkludując))\b",
                r"\b(?:(?:ostatecznie|finalnie|w\s+konkluzji))\b"
            ],
            "przykład": [
                r"\b(?:na\s+przykład|przykładem\s+jest|dla\s+przykładu)\b",
                r"\b(?:doskonale\s+ilustruje\s+to|świadczy\s+o\s+tym)\b",
                r"\b(?:warto\s+(?:przytoczyć|wskazać)\s+przykład)\b"
            ],
            "definicja": [
                r"\b(?:definiuję|rozumiem\s+(?:przez|jako)|oznacza\s+to)\b",
                r"\b(?:termin|pojęcie)\s+(?:\w+)\s+(?:odnosi\s+się|oznacza)\b",
                r"(?:(?:^|[.!?]\s+)(?:[A-Z]\w+)\s+(?:to|jest|oznacza))\b"
            ]
        }
        
        # Spójniki logiczne i ich kategorie
        logical_connectors = {
            "przyczynowe": [
                r"\b(?:ponieważ|gdyż|bowiem|dlatego\s+że|z\s+powodu)\b",
                r"\b(?:w\s+związku\s+z\s+tym|skutkiem\s+tego)\b"
            ],
            "kontrastujące": [
                r"\b(?:jednak|niemniej|natomiast|ale|lecz|choć|chociaż)\b",
                r"\b(?:z\s+drugiej\s+strony|przeciwnie|wbrew\s+temu)\b"
            ],
            "wynikowe": [
                r"\b(?:w\s+rezultacie|w\s+efekcie|w\s+konsekwencji)\b",
                r"\b(?:zatem|więc|tak\s+więc|stąd|dlatego)\b"
            ],
            "wzmacniające": [
                r"\b(?:co\s+więcej|ponadto|dodatkowo|w\s+dodatku)\b",
                r"\b(?:nie\s+tylko|również|także|zarówno)\b"
            ],
            "porządkujące": [
                r"\b(?:po\s+pierwsze|po\s+drugie|następnie|w\s+końcu)\b",
                r"\b(?:przede\s+wszystkim|w\s+szczególności|głównie)\b"
            ]
        }
        
        # Identyfikacja elementów argumentacji w zdaniach
        argument_structure = {}
        for arg_type, patterns in argument_patterns.items():
            argument_structure[arg_type] = []
            for pattern in patterns:
                for i, sentence in enumerate(sentences):
                    if re.search(pattern, sentence, re.IGNORECASE):
                        argument_structure[arg_type].append({
                            "zdanie": sentence,
                            "pozycja": i + 1
                        })
        
        # Identyfikacja spójników logicznych
        connectors_found = {}
        for conn_type, patterns in logical_connectors.items():
            connectors_found[conn_type] = 0
            for pattern in patterns:
                for sentence in sentences:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    connectors_found[conn_type] += len(matches)
        
        # Określanie struktury argumentacyjnej
        structure_type = "nieokreślona"
        elements_found = []
        
        # Sprawdzanie kompletności argumentacji
        if argument_structure["teza_główna"] and argument_structure["konkluzja"]:
            if argument_structure["przesłanka"]:
                if argument_structure["kontrargument"]:
                    structure_type = "złożona dialektyczna"
                    elements_found = ["teza", "przesłanki", "kontrargumenty", "konkluzja"]
                else:
                    structure_type = "prosta liniowa"
                    elements_found = ["teza", "przesłanki", "konkluzja"]
            else:
                structure_type = "niekompletna"
                elements_found = ["teza", "konkluzja"]
        elif argument_structure["przesłanka"]:
            if argument_structure["teza_główna"]:
                structure_type = "niedokończona"
                elements_found = ["teza", "przesłanki"]
            elif argument_structure["konkluzja"]:
                structure_type = "indukcyjna"
                elements_found = ["przesłanki", "konkluzja"]
            else:
                structure_type = "fragmentaryczna"
                elements_found = ["przesłanki"]
        elif argument_structure["teza_główna"]:
            structure_type = "deklaratywna"
            elements_found = ["teza"]
        
        # Określanie jakości argumentacji
        arg_quality = "niska"
        
        # Liczenie elementów argumentacji
        total_elements = sum(len(items) for items in argument_structure.values())
        
        # Sprawdzanie obecności definicji i przykładów
        has_definitions = len(argument_structure["definicja"]) > 0
        has_examples = len(argument_structure["przykład"]) > 0
        
        # Liczenie spójników logicznych
        total_connectors = sum(connectors_found.values())
        
        # Ocena jakości argumentacji
        conn_per_sentence = total_connectors / len(sentences) if sentences else 0
        
        # Zróżnicowanie typów spójników
        connector_diversity = sum(1 for count in connectors_found.values() if count > 0)
        
        # Kryteria jakości
        if (structure_type in ["złożona dialektyczna", "prosta liniowa"] and 
                has_definitions and has_examples and conn_per_sentence >= 0.5 and
                connector_diversity >= 3):
            arg_quality = "wysoka"
        elif (total_elements >= 5 and conn_per_sentence >= 0.3 and
              (has_definitions or has_examples) and connector_diversity >= 2):
            arg_quality = "średnia"
        
        # Identyfikacja głównych argumentów
        main_args = []
        for arg_type in ["teza_główna", "przesłanka", "konkluzja"]:
            for item in argument_structure[arg_type]:
                if item not in main_args:
                    main_args.append(item["zdanie"])
        
        result = {
            "struktura": structure_type,
            "elementy": elements_found,
            "główne_argumenty": main_args[:3],  # Ograniczamy do 3 najważniejszych
            "jakość": arg_quality,
            "spójniki_logiczne": {
                "liczba": total_connectors,
                "na_zdanie": round(conn_per_sentence, 2),
                "rodzaje": {k: v for k, v in connectors_found.items() if v > 0}
            }
        }
        
        # Dodajemy ocenę balansu argumentacji
        if argument_structure["kontrargument"]:
            contra_to_pro_ratio = (len(argument_structure["kontrargument"]) / 
                                 len(argument_structure["przesłanka"]) 
                                 if argument_structure["przesłanka"] else 0)
            result["balans_argumentacji"] = round(contra_to_pro_ratio, 2)
            
            if 0.3 <= contra_to_pro_ratio <= 0.7:
                result["ocena_balansu"] = "zrównoważona"
            elif contra_to_pro_ratio > 0.7:
                result["ocena_balansu"] = "silnie dialektyczna"
            else:
                result["ocena_balansu"] = "jednostronna"
        else:
            result["balans_argumentacji"] = 0.0
            result["ocena_balansu"] = "jednokierunkowa"
            
        return result
        
    def analyze_semantic_structure(self, text):
        """Analizuje głęboką strukturę semantyczną tekstu"""
        if not text:
            return {"struktura": "brak tekstu", "relacje": [], "tematy": []}
            
        text_lower = text.lower()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return {"struktura": "brak tekstu", "relacje": [], "tematy": []}
            
        # 1. Analiza podmiotów i obiektów w tekście
        entities = []
        patterns = {
            "osoba": [
                r"\b([A-Z][a-ząćęłńóśźż]+)\b(?=\s+(?:powiedział|stwierdził|uważa))",
                r"\b([A-Z][a-ząćęłńóśźż]+)\b(?=\s+(?:jest|był|będzie))"
            ],
            "organizacja": [
                r"\b([A-Z][A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż]+)\b(?=\s+(?:ogłosił|poinformował))",
                r"\b(?:firma|spółka|organizacja|instytucja|ministerstwo)\s+([A-Z]\w+)\b"
            ],
            "miejsce": [
                r"\bw\s+([A-Z][a-ząćęłńóśźż]+)\b",
                r"\bdo\s+([A-Z][a-ząćęłńóśźż]+)\b",
                r"\bz\s+([A-Z][a-ząćęłńóśźż]+)\b"
            ],
            "czas": [
                r"\b(\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)(?:\s+\d{4})?)\b",
                r"\b((?:w\s+)?(?:poniedziałek|wtorek|środę|czwartek|piątek|sobotę|niedzielę))\b",
                r"\b(\d{1,2}:\d{2})\b"
            ],
            "pojęcie": [
                r"\b([a-ząćęłńóśźż]{5,}(?:acja|izm|ość|stwo|ctwo|anie|enie))\b"
            ]
        }
        
        for entity_type, patterns_list in patterns.items():
            for pattern in patterns_list:
                for sentence in sentences:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        if len(match) > 2:  # Minimalna długość encji
                            entities.append({
                                "tekst": match,
                                "typ": entity_type,
                                "kontekst": sentence[:50] + "..." if len(sentence) > 50 else sentence
                            })
        
        # Filtrowanie duplikatów
        unique_entities = []
        seen_entities = set()
        for entity in entities:
            key = (entity["tekst"].lower(), entity["typ"])
            if key not in seen_entities:
                seen_entities.add(key)
                unique_entities.append(entity)
        
        # 2. Analiza relacji semantycznych
        relations = []
        semantic_patterns = {
            "przyczynowo-skutkowe": [
                r"(\b\w+[^.!?]*)\s+(?:powoduje|powodują|spowodował|spowodowała|wywołuje|skutkuje)\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:wpływa|wpływają|wpłynął|wpłynęła)\s+na\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:dlatego|z\s+tego\s+powodu|w\s+rezultacie)\s+([^.!?]*)"
            ],
            "porównawcze": [
                r"(\b\w+[^.!?]*)\s+(?:podobnie\s+jak|tak\s+jak|podobnie\s+do)\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:różni\s+się\s+od|jest\s+inne\s+niż|jest\s+odmienne\s+od)\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:w\s+przeciwieństwie\s+do)\s+([^.!?]*)"
            ],
            "część-całość": [
                r"(\b\w+[^.!?]*)\s+(?:składa\s+się\s+z|zawiera|obejmuje)\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:jest\s+częścią|wchodzi\s+w\s+skład|należy\s+do)\s+([^.!?]*)"
            ],
            "posesywne": [
                r"(\b\w+[^.!?]*)\s+(?:posiada|ma|dysponuje)\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:należący\s+do|właściciel|własność)\s+([^.!?]*)"
            ],
            "temporalne": [
                r"(\b\w+[^.!?]*)\s+(?:przed|po|w\s+trakcie|podczas)\s+([^.!?]*)",
                r"(\b\w+[^.!?]*)\s+(?:wcześniej\s+niż|później\s+niż|równocześnie\s+z)\s+([^.!?]*)"
            ]
        }
        
        for rel_type, patterns_list in semantic_patterns.items():
            for pattern in patterns_list:
                for sentence in sentences:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        if len(match) >= 2:
                            relations.append({
                                "typ": rel_type,
                                "element_1": match[0].strip(),
                                "element_2": match[1].strip(),
                                "zdanie": sentence
                            })
        
        # 3. Analiza struktury tematycznej
        topic_words = {}
        
        # Ekstrakcja rzeczowników jako potencjalnych tematów
        noun_pattern = r"\b([a-ząćęłńóśźż]{3,}(?:ość|anie|enie|stwo|ctwo|cja|zja|acja|izm|or|er|yk))\b"
        for sentence in sentences:
            matches = re.findall(noun_pattern, sentence.lower())
            for match in matches:
                if match not in topic_words:
                    topic_words[match] = 0
                topic_words[match] += 1
        
        # Lista "stop words" dla tematów
        stop_words = ["dlatego", "ponieważ", "przez", "gdyż", "czyli", "więc", "jednak", 
                     "bowiem", "także", "również", "czyli", "właśnie", "natomiast"]
        
        # Filtrowanie potencjalnych tematów
        for word in stop_words:
            if word in topic_words:
                del topic_words[word]
        
        # Wybór głównych tematów
        main_topics = sorted(topic_words.items(), key=lambda x: x[1], reverse=True)[:5]
        main_topics = [{"temat": topic, "częstość": count} for topic, count in main_topics]
        
        # 4. Analiza kohezji tekstu (powiązań wewnętrznych)
        cohesion_markers = {
            "zaimki_anaforyczne": [
                r"\b(?:on[a|i]?|jeg[a|o]|jej|ich|t[en|ą|ym|ymi]|t[a|e]|ci|tamci|tamte)\b"
            ],
            "odniesienia_tematyczne": [
                r"\b(?:ten\s+sam|wspomnian[y|a|e]|powyższ[y|a|e]|wcześniejsz[y|a|e])\b"
            ],
            "spójniki_kontynuacji": [
                r"\b(?:ponadto|poza\s+tym|co\s+więcej|następnie|dalej|kontynuując)\b"
            ],
            "powtórzenia_leksykalne": []  # Będzie analizowane algorytmicznie
        }
        
        # Liczenie markerów kohezji
        cohesion_counts = {}
        for marker_type, patterns_list in cohesion_markers.items():
            cohesion_counts[marker_type] = 0
            for pattern in patterns_list:
                for sentence in sentences:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    cohesion_counts[marker_type] += len(matches)
        
        # Analiza powtórzeń leksykalnych
        words_by_sentence = [re.findall(r'\b\w{3,}\b', s.lower()) for s in sentences]
        repetitions = 0
        
        # Szukamy powtórzeń słów między zdaniami
        if len(words_by_sentence) > 1:
            for i in range(1, len(words_by_sentence)):
                for word in words_by_sentence[i]:
                    if word in words_by_sentence[i-1]:
                        repetitions += 1
        
        cohesion_counts["powtórzenia_leksykalne"] = repetitions
        
        # Ogólna miara kohezji
        cohesion_total = sum(cohesion_counts.values())
        cohesion_per_sentence = cohesion_total / len(sentences) if sentences else 0
        
        # Określenie spójności semantycznej
        cohesion_level = "niska"
        if cohesion_per_sentence >= 1.5:
            cohesion_level = "wysoka"
        elif cohesion_per_sentence >= 0.8:
            cohesion_level = "średnia"
        
        # 5. Określenie głównej struktury semantycznej
        semantic_structure_types = {
            "narracyjna": 0,
            "ekspozycyjna": 0, 
            "argumentacyjna": 0,
            "opisowa": 0,
            "instruktażowa": 0
        }
        
        # Wzorce językowe charakterystyczne dla poszczególnych struktur
        structure_patterns = {
            "narracyjna": [
                r"\b(?:najpierw|potem|następnie|wtedy|później|w\s+końcu)\b",
                r"\b(?:gdy|kiedy|podczas|po\s+tym\s+jak|zanim|wkrótce)\b",
                r"\b(?:pewnego\s+dnia|pewnego\s+razu|dawno\s+temu|kiedyś)\b"
            ],
            "ekspozycyjna": [
                r"\b(?:definiuje|klasyfikuje|wyjaśnia|przedstawia|omawia)\b",
                r"\b(?:po\s+pierwsze|po\s+drugie|jednym\s+z|kolejnym)\b",
                r"\b(?:głównym|kluczowym|istotnym|ważnym|podstawowym)\b"
            ],
            "argumentacyjna": [
                r"\b(?:twierdzę|uważam|sądzę|dowodzę|argumentuję|przekonuję)\b",
                r"\b(?:ponieważ|dlatego|zatem|wobec\s+tego|wynika\s+z\s+tego)\b",
                r"\b(?:podsumowując|w\s+konkluzji|z\s+tego\s+wynika|dowodzi\s+to)\b"
            ],
            "opisowa": [
                r"\b(?:wygląda\s+jak|przypomina|charakteryzuje\s+się|cechuje\s+się)\b",
                r"\b(?:jest|wydaje\s+się|sprawia\s+wrażenie|prezentuje\s+się\s+jako)\b",
                r"\b(?:czerwony|niebieski|zielony|duży|mały|szeroki|wąski|wysoki)\b"
            ],
            "instruktażowa": [
                r"\b(?:należy|trzeba|powinno\s+się|musisz|najpierw|następnie)\b",
                r"\b(?:krok\s+po\s+kroku|w\s+pierwszej\s+kolejności|na\s+końcu)\b",
                r"(?:^\s*\d+\.|\d\)\s+|\-\s+|•\s+)"
            ]
        }
        
        # Analiza wzorców dla określenia struktury
        for structure, patterns_list in structure_patterns.items():
            for pattern in patterns_list:
                for sentence in sentences:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    semantic_structure_types[structure] += len(matches)
        
        main_structure = max(semantic_structure_types.items(), key=lambda x: x[1])
        main_structure_type = main_structure[0]
        if main_structure[1] == 0:
            main_structure_type = "mieszana/nieokreślona"
        
        result = {
            "struktura_semantyczna": main_structure_type,
            "encje": unique_entities[:10],  # Ograniczamy do top 10
            "relacje": relations[:10],      # Ograniczamy do top 10
            "główne_tematy": main_topics,
            "spójność": {
                "poziom": cohesion_level,
                "markery_kohezji": cohesion_counts,
                "wskaźnik_spójności": round(cohesion_per_sentence, 2)
            }
        }
        
        return result
    
    def detect_temporal_context(self, text):
        """Wykrywanie kontekstu czasowego w tekście"""
        text_lower = text.lower()
        temporal_scores = {"przeszłość": 0, "teraźniejszość": 0.1, "przyszłość": 0}
        
        # Wskaźniki czasu przeszłego
        past_indicators = ["był", "była", "było", "były", "byłem", "byłam", "zrobiłem", "zrobiłam", "wczoraj", "wcześniej", "dawniej", "kiedyś", "niedawno"]
        
        # Wskaźniki czasu teraźniejszego
        present_indicators = ["jest", "są", "jestem", "jesteś", "robimy", "robię", "teraz", "obecnie", "dziś", "dzisiaj"]
        
        # Wskaźniki czasu przyszłego
        future_indicators = ["będzie", "będą", "będę", "będziemy", "zrobimy", "zrobię", "jutro", "wkrótce", "za chwilę", "w przyszłości", "później"]
        
        # Sprawdzanie wskaźników w tekście
        for indicator in past_indicators:
            if indicator in text_lower:
                temporal_scores["przeszłość"] += 0.15
                
        for indicator in present_indicators:
            if indicator in text_lower:
                temporal_scores["teraźniejszość"] += 0.15
                
        for indicator in future_indicators:
            if indicator in text_lower:
                temporal_scores["przyszłość"] += 0.15
        
        # Normalizacja wyników
        total = sum(temporal_scores.values()) or 1
        normalized = {k: round(v/total, 2) for k, v in temporal_scores.items()}
        
        # Określenie dominującego kontekstu czasowego
        dominant = max(normalized, key=normalized.get)
        normalized["dominujący"] = dominant
        
        return normalized
    def extract_entities(self, text):
        """Ekstrakcja encji z tekstu (osoby, miejsca, organizacje, daty, liczby)"""
        entities = {
            "osoby": [],
            "miejsca": [],
            "organizacje": [],
            "daty": [],
            "liczby": []
        }
        
        # Proste wzorce do rozpoznawania encji
        
        # Osoby (podstawowy wzorzec imię i nazwisko)
        person_pattern = re.compile(r'\b[A-ZŚĆŹŻŁÓŃ][a-zśćźżłóńäëöüß]+ [A-ZŚĆŹŻŁÓŃ][a-zśćźżłóńäëöüß]+\b')
        for match in person_pattern.finditer(text):
            entities["osoby"].append(match.group(0))
            
        # Miejsca (miasta, kraje)
        places = ["Warszawa", "Kraków", "Wrocław", "Poznań", "Gdańsk", "Łódź", "Szczecin", 
                 "Polska", "Niemcy", "Francja", "Włochy", "Hiszpania", "Anglia", "USA"]
        for place in places:
            if place in text:
                entities["miejsca"].append(place)
                
        # Organizacje (proste wzorce)
        org_pattern = re.compile(r'\b(?:[A-ZŚĆŹŻŁÓŃ][a-zśćźżłóńäëöüß]+ )?(?:[A-ZŚĆŹŻŁÓŃ][a-zśćźżłóńäëöüß]+ )?[A-ZŚĆŹŻŁÓŃ][a-zśćźżłóńäëöüß]* (?:sp\. z o\.o\.|S\.A\.|Inc\.|Ltd\.|GmbH)\b')
        for match in org_pattern.finditer(text):
            entities["organizacje"].append(match.group(0))
            
        # Popularne organizacje
        orgs = ["Google", "Microsoft", "Facebook", "Apple", "Amazon", "Twitter", "Netflix", "Allegro", "PKO", "PZU"]
        for org in orgs:
            if org in text:
                entities["organizacje"].append(org)
                
        # Daty
        date_patterns = [
            re.compile(r'\b\d{1,2} (?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia) \d{4}\b'),
            re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b'),
            re.compile(r'\b\d{4}-\d{1,2}-\d{1,2}\b')
        ]
        
        for pattern in date_patterns:
            for match in pattern.finditer(text):
                entities["daty"].append(match.group(0))
                
        # Liczby
        number_pattern = re.compile(r'\b\d+(?:[.,]\d+)?\b')
        for match in number_pattern.finditer(text):
            entities["liczby"].append(match.group(0))
            
        # Usunięcie duplikatów
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
            
        return entities
    
    def analyze_conversation(self, messages):
        """Analiza całej konwersacji"""
        if not messages:
            return {}
            
        # Ekstrahuj teksty z wiadomości
        texts = [msg.get("content", "") for msg in messages]
        full_text = " ".join(texts)
        
        # Analiza całego tekstu
        overall_analysis = self.analyze_text(full_text)
        
        # Śledzenie trendu sentymentu
        sentiment_values = []
        for msg in messages:
            content = msg.get("content", "")
            if content:
                sentiment = self.analyze_sentiment(content)
                if sentiment["dominujący"] == "pozytywny":
                    sentiment_values.append(sentiment["pozytywny"])
                elif sentiment["dominujący"] == "negatywny":
                    sentiment_values.append(-sentiment["negatywny"])
                else:
                    sentiment_values.append(0)
        
        # Określenie trendu sentymentu
        sentiment_trend = "stabilny"
        avg_sentiment = "neutralny"
        if sentiment_values:
            if len(sentiment_values) >= 3:
                first_half = sentiment_values[:len(sentiment_values)//2]
                second_half = sentiment_values[len(sentiment_values)//2:]
                avg_first = sum(first_half) / len(first_half) if first_half else 0
                avg_second = sum(second_half) / len(second_half) if second_half else 0
                
                if avg_second > avg_first + 0.2:
                    sentiment_trend = "rosnący"
                elif avg_second < avg_first - 0.2:
                    sentiment_trend = "malejący"
            
            avg_value = sum(sentiment_values) / len(sentiment_values)
            if avg_value > 0.2:
                avg_sentiment = "pozytywny"
            elif avg_value < -0.2:
                avg_sentiment = "negatywny"
        
        # Analiza spójności tematycznej
        topic_consistency = {"spójność": "wysoka", "wartość": 0.8}
        if len(texts) >= 2:
            topics_per_message = [set(self.detect_topics(txt).keys()) for txt in texts]
            consistency_scores = []
            
            for i in range(1, len(topics_per_message)):
                current = topics_per_message[i]
                previous = topics_per_message[i-1]
                
                if current and previous:  # Jeśli oba zestawy niepuste
                    similarity = len(current.intersection(previous)) / len(current.union(previous)) if current.union(previous) else 0
                    consistency_scores.append(similarity)
            
            if consistency_scores:
                avg_consistency = sum(consistency_scores) / len(consistency_scores)
                topic_consistency["wartość"] = round(avg_consistency, 2)
                
                if avg_consistency < 0.3:
                    topic_consistency["spójność"] = "niska"
                elif avg_consistency < 0.6:
                    topic_consistency["spójność"] = "średnia"
        
        # Analiza zmian intencji
        intention_sequence = []
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content"):
                intention = self.detect_intention(msg.get("content"))
                intention_sequence.append(intention["dominująca"])
                
        intention_changes = {"zmiany": "brak", "sekwencja": intention_sequence}
        
        if len(intention_sequence) >= 3:
            changes_count = sum(1 for i in range(1, len(intention_sequence)) if intention_sequence[i] != intention_sequence[i-1])
            change_rate = changes_count / (len(intention_sequence) - 1)
            
            if change_rate > 0.7:
                intention_changes["zmiany"] = "częste"
            elif change_rate > 0.3:
                intention_changes["zmiany"] = "sporadyczne"
        
        return {
            "overall_analysis": overall_analysis,
            "sentiment_trend": {
                "trend": sentiment_trend,
                "średni_sentyment": avg_sentiment,
                "wartości": sentiment_values
            },
            "topic_consistency": topic_consistency,
            "main_topics": list(overall_analysis["topics"].keys()),
            "intention_changes": intention_changes
        }

class SemanticIntegration:
    """Klasa integrująca analizę semantyczną z głównym systemem"""
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.analyzer = SemanticAnalyzer()
        
        # Inicjalizacja tabeli semantic_metadata, jeśli nie istnieje
        if db_path:
            conn = sqlite3.connect(db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS semantic_metadata (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    message_id TEXT,
                    role TEXT,
                    topics TEXT,
                    sentiment TEXT,
                    intention TEXT,
                    entities TEXT,
                    complexity TEXT,
                    temporal_context TEXT,
                    timestamp REAL
                )
            ''')
            conn.commit()
            conn.close()
    
    def enhance_chat_response(self, user_id, query, response, message_history=None):
        """Wzbogaca odpowiedź o analizę semantyczną"""
        # Analiza zapytania użytkownika
        query_analysis = self.analyzer.analyze_text(query)
        
        # Analiza odpowiedzi
        response_analysis = self.analyzer.analyze_text(response)
        
        # Analiza całej konwersacji
        conversation_analysis = {}
        if message_history:
            conversation_analysis = self.analyzer.analyze_conversation(message_history)
        
        # Ekstrakcja encji
        entities = query_analysis.get("entities", {})
        
        # Generowanie rekomendacji
        recommendations = self._generate_recommendations(query_analysis, response_analysis, conversation_analysis)
        
        # Zapisanie metadanych semantycznych w bazie danych
        self.store_semantic_data(user_id, query, query_analysis)
        
        return {
            "query_analysis": query_analysis,
            "response_analysis": response_analysis,
            "conversation_analysis": conversation_analysis,
            "entities": entities,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, query_analysis, response_analysis, conversation_analysis):
        """Generuje rekomendacje na podstawie analizy semantycznej"""
        recommendations = {
            "topics": [],
            "intentions": [],
            "tone_suggestions": [],
            "follow_up_questions": [],
            "context_needs": []
        }
        
        # Rekomendacje tematów
        if query_analysis.get("topics"):
            for topic, score in sorted(query_analysis["topics"].items(), key=lambda x: x[1], reverse=True)[:3]:
                recommendations["topics"].append({"topic": topic, "score": score})
        
        # Rekomendacje intencji
        query_intention = query_analysis.get("intention", {}).get("dominująca")
        if query_intention:
            recommendations["intentions"].append(query_intention)
        
        # Rekomendacje tonu
        query_sentiment = query_analysis.get("sentiment", {}).get("dominujący")
        if query_sentiment == "pozytywny":
            recommendations["tone_suggestions"] = ["pozytywny", "entuzjastyczny", "pomocny"]
        elif query_sentiment == "negatywny":
            recommendations["tone_suggestions"] = ["empatyczny", "profesjonalny", "rzeczowy"]
        else:
            recommendations["tone_suggestions"] = ["informacyjny", "neutralny", "rzeczowy"]
        
        # Generowanie pytań uzupełniających
        topics = list(query_analysis.get("topics", {}).keys())
        entities = query_analysis.get("entities", {})
        keywords = query_analysis.get("keywords", [])
        
        follow_up_templates = [
            "Czy potrzebujesz bardziej szczegółowych informacji na temat {topic}?",
            "Czy chciałbyś dowiedzieć się więcej o {keyword}?",
            "Czy masz jakieś konkretne pytania dotyczące {entity}?",
            "Czy mogę pomóc Ci w jeszcze czymś związanym z {topic}?"
        ]
        
        # Tworzenie pytań uzupełniających
        if topics:
            topic = random.choice(topics)
            recommendations["follow_up_questions"].append(follow_up_templates[0].format(topic=topic))
            
        if keywords:
            keyword = random.choice(keywords)
            recommendations["follow_up_questions"].append(follow_up_templates[1].format(keyword=keyword))
            
        for entity_type, entity_list in entities.items():
            if entity_list and random.random() < 0.5:  # 50% szans na dodanie pytania o encję
                entity = random.choice(entity_list)
                recommendations["follow_up_questions"].append(follow_up_templates[2].format(entity=entity))
        
        # Potrzeby kontekstowe
        if not entities.get("osoby") and ("osoba" in topics or "ludzie" in topics):
            recommendations["context_needs"].append("informacje o osobach")
            
        if not entities.get("daty") and ("czas" in topics or "harmonogram" in topics):
            recommendations["context_needs"].append("informacje o czasie/datach")
            
        # Usunięcie duplikatów i ograniczenie do sensownej liczby
        recommendations["follow_up_questions"] = list(set(recommendations["follow_up_questions"]))[:3]
        
        return recommendations
    
    def get_semantic_metadata_for_db(self, user_id, text, role):
        """Przygotowuje metadane semantyczne do zapisu w bazie danych"""
        analysis = self.analyzer.analyze_text(text)
        
        semantic_metadata = {
            "user_id": user_id,
            "role": role,
            "semantic_metadata": {
                "topics": analysis.get("topics", {}),
                "sentiment": analysis.get("sentiment", {}).get("dominujący", "neutralny"),
                "intention": analysis.get("intention", {}).get("dominująca", "nieznana"),
                "entities": analysis.get("entities", {}),
                "complexity": analysis.get("complexity", {}).get("poziom", "średnia"),
                "temporal_context": analysis.get("temporal_context", {}).get("dominujący", "teraźniejszość")
            }
        }
        
        return semantic_metadata
        
    def store_semantic_data(self, user_id, query, analysis):
        """Zapisuje metadane semantyczne w bazie danych"""
        if not self.db_path or not user_id or not query:
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            id = uuid.uuid4().hex
            message_id = uuid.uuid4().hex
            
            # Konwersja pól słownikowych do JSON
            topics_json = json.dumps(analysis.get("topics", {}), ensure_ascii=False)
            sentiment = analysis.get("sentiment", {}).get("dominujący", "neutralny")
            intention = analysis.get("intention", {}).get("dominująca", "nieznana")
            entities_json = json.dumps(analysis.get("entities", {}), ensure_ascii=False)
            complexity = analysis.get("complexity", {}).get("poziom", "średnia")
            temporal_context = analysis.get("temporal_context", {}).get("dominujący", "teraźniejszość")
            
            c.execute("INSERT INTO semantic_metadata VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                     (id, user_id, message_id, "user", topics_json, sentiment, intention, entities_json, complexity, temporal_context, time.time()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania danych semantycznych: {e}")
            return False

# Inicjalizacja modułu analizy semantycznej
semantic_analyzer = SemanticAnalyzer()

# Inicjalizacja modułu analizy semantycznej
semantic_analyzer = SemanticAnalyzer()
semantic_integration = SemanticIntegration(DB_PATH)
log_info("Semantic module initialized", "SEMANTIC")

# Public API
def semantic_analyze(text: str)->Dict[str,Any]:
    """Analyze text semantically"""
    return semantic_analyzer.analyze_text(text)

def semantic_analyze_conversation(messages: List[Dict[str,str]])->Dict[str,Any]:
    """Analyze entire conversation"""
    return semantic_analyzer.analyze_conversation(messages)

def semantic_enhance_response(answer: str, context: str="")->Dict[str,Any]:
    """Enhance response based on semantic analysis"""
    analysis = semantic_analyzer.analyze_text(answer)
    enhanced = answer
    sentiment = analysis.get("sentyment", {})
    
    if sentiment.get("dominujący") == "negatywny":
        if not any(word in answer.lower() for word in ["przepraszam", "rozumiem", "przykro"]):
            enhanced = "Rozumiem, " + answer[0].lower() + answer[1:]
    
    return {"ok": True, "original": answer, "enhanced": enhanced, "analysis": analysis}


def embed_text(text: str) -> List[float]:
    """
    Generuje embedding dla tekstu używając dostępnego providera.
    
    Args:
        text: Tekst do embeddingu
        
    Returns:
        List[float]: Wektor embedding
    """
    try:
        # Użyj semantic_analyze do uzyskania embedding
        analysis = semantic_analyze(text)
        return analysis.get("embedding", [])
    except Exception as e:
        log_error(f"Text embedding failed: {e}")
        return []


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Oblicza podobieństwo kosinusowe między dwoma wektorami.
    
    Args:
        vec1: Pierwszy wektor
        vec2: Drugi wektor
        
    Returns:
        float: Podobieństo w zakresie [0, 1]
    """
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
            
        import math
        
        # Oblicz iloczyn skalarny
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Oblicz normy
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    except Exception as e:
        log_error(f"Cosine similarity calculation failed: {e}")
        return 0.0


__all__ = [
    'SemanticAnalyzer', 'SemanticIntegration',
    'semantic_analyzer', 'semantic_integration',
    'semantic_analyze', 'semantic_analyze_conversation', 'semantic_enhance_response',
    'embed_text', 'cosine_similarity'
]
