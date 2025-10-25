# Przełącznik osobowości dla Mordzix AI Pro

## Instrukcja implementacji

1. Stworzono plik `personality_switcher.js`, który zawiera:
   - Przyciski do wyboru osobowości (Normalny, Ziomek, Literat, Aukcja)
   - Style CSS dla interfejsu przełącznika
   - Funkcje do zmiany i zapisywania stanu osobowości
   - Powiadomienia o zmianie trybu

2. W pliku `chat_pro.html`:
   - Dodano import skryptu przełącznika osobowości
   - Rozbudowano funkcję wykrywania osobowości (`detectPersonalityMode`)
   - Zaimplementowano system dodawania instrukcji osobowości do wiadomości
   - Dodano wsparcie dla zapisywania preferencji w `localStorage`

## Tryby osobowości

### Normalny (profesjonalny)
Standardowy tryb asystenta - profesjonalny, pomocny, merytoryczny.

### Ziomek (luzny)
- Osobowość: Luzny ziomek, przyjaciel z poczuciem humoru
- Styl: Ironiczny, sarkastyczny, bezpośredni
- Zastosowanie: Rozmowy luźne, pomoc techniczna, programowanie

### Literat (kreatywny)
- Osobowość: Kreatywny pisarz, mistrz słowa
- Styl: Bogaty język, nawiązania literackie, obrazowy
- Zastosowanie: Wiersze, opowiadania, fraszki, eseje

### Aukcja (sprzedażowy)
- Osobowość: Kreatywny copywriter aukcyjny
- Styl: Przekonujący, żartobliwy, zwracający uwagę
- Zastosowanie: Opisy produktów, ogłoszenia sprzedaży

## Funkcjonalność

1. **Automatyczna detekcja kontekstu**:
   - Rozpoznawanie intencji użytkownika na podstawie wzorców słownych
   - Automatyczne przełączanie trybu osobowości w zależności od zapytania
   - Rozbudowane wyrażenia regularne dla precyzyjnej detekcji

2. **Integracja z API**:
   - Dodawanie instrukcji systemowych do wiadomości użytkownika
   - Modyfikacja zapytań przed wysłaniem do API
   - Zachowanie wszystkich istniejących funkcji

3. **Interfejs użytkownika**:
   - Przyciski z wizualnym wskaźnikiem aktualnego trybu
   - Wizualne powiadomienia o zmianie trybu
   - Zapisywanie preferencji użytkownika między sesjami

## Uwagi techniczne

- Instrukcje osobowości są dodawane do ostatniej wiadomości użytkownika przed wysłaniem do API
- Zmodyfikowano pipeline przetwarzania wiadomości w funkcji `sendMessage()`
- Dodano nowe wzorce dla detekcji kontekstu dla każdej osobowości
- Implementacja uwzględnia prawidłowe wykrywanie konfliktów kontekstów