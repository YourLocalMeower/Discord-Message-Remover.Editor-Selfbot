# Discord Message Cleaner

Skrypt, który usuwa albo zamienia na wskazany tekst **Twoje własne wiadomości** z wybranego kanału (serwer lub DM) w podanym zakresie dat. Działa wolno i porcjami, żeby nie przekraczać limitów API.

> **Ostrzeżenie:** używanie tokena konta użytkownika do automatyzacji ("selfbot") łamie regulamin Discorda. Konto może zostać zablokowane. Używasz skryptu na własne ryzyko.

---

## 1. Instalacja

Wymagany jest Python 3.9 lub nowszy.

```
python -m pip install requests python-dotenv
```

Jeśli `pip` nie działa:

```
python -m ensurepip --upgrade
python -m pip install requests python-dotenv
```

Dla launchera Windows: `py -m pip install requests python-dotenv`.

## 2. Konfiguracja tokena

W folderze ze skryptem (`bot.py`) utwórz plik `.env`:

```
TOKEN=twój_token
```

- Bez cudzysłowów i bez spacji wokół `=`.
- Token to to samo co hasło do konta. Nie wysyłaj go nikomu i nie wklejaj na czaty.
- Jeśli wrzucasz projekt na GitHub, dodaj `.env` do `.gitignore`.
- Jeśli token wyciekł, zmień hasło do konta, co unieważni stary token.

## 3. Uruchomienie

```
python bot.py
```

Skrypt zadaje pytania po kolei:

| Pytanie | Opis |
|---|---|
| **ID kanału** | ID kanału lub DM. Włącz tryb programisty w Discordzie, kliknij kanał prawym przyciskiem i wybierz "Kopiuj ID kanału". |
| **Data od / do** | Format `YYYY-MM-DD`. Dzień "do" jest wliczony. |
| **Tryb** | `1` usuń, `2` zamień na tekst z pliku. |
| **Plik .txt** (tryb 2) | Skrypt sam znajduje pliki `.txt` w folderze skryptu i bieżącym folderze. Przy jednym pyta o potwierdzenie, przy kilku pokazuje listę. Można też podać ścieżkę ręcznie. Pokazuje podgląd przed zatwierdzeniem. |
| **Edytowane** | Czy uwzględniać wiadomości, które już były edytowane (Y/N). |
| **Załączniki/embedy** (tryb 2) | Co robić z wiadomościami z obrazem, plikiem lub podglądem linku (patrz niżej). |
| **Tempo** | Patrz sekcja "Tempo". |

Po skanowaniu skrypt pokazuje liczbę znalezionych wiadomości, szacowany czas i prosi o ostateczne potwierdzenie. **Ctrl+C** zatrzymuje skrypt bezpiecznie i pokazuje podsumowanie.

## 4. Tryby działania

### Tryb 1: Usuń
Usuwa wszystkie pasujące wiadomości, razem z załącznikami.

### Tryb 2: Zamień na tekst
Edytuje treść wiadomości na tekst z pliku `.txt`.

- Tekst: maksymalnie **2000 znaków**, cały plik trafia jako jedna wiadomość.
- Wiadomości, które już mają dokładnie ten tekst, są pomijane.
- Edytowana wiadomość dostaje widoczną etykietę **(edited)**. Tego nie da się ukryć.

#### Wiadomości z załącznikami i embedami
| Opcja | Działanie |
|---|---|
| `1` Tylko edytuj | Zmienia tekst, **wgrane załączniki (obrazy, pliki) zostają**. |
| `2` Usuń całą wiadomość | Usuwa wiadomość razem z załącznikiem. |
| `3` Pomiń | Takie wiadomości zostają nietknięte. |

Podglądy linków (automatyczne embedy) zwykle znikają po edycji, jeśli nowy tekst nie zawiera tego linku. Wiadomość z samym załącznikiem i bez tekstu dostanie Twój tekst nad załącznikiem.

## 5. Tempo

| Opcja | Działanie |
|---|---|
| `1` Normalne | Losowy odstęp 1-20 s między akcjami. |
| `2` Auto | Serie 3-6 szybkich akcji (odstęp 1-15 s), potem długa przerwa 6-20 min. Im więcej akcji w ostatniej godzinie, tym dłuższa przerwa. Opcjonalnie podajesz maksymalny czas całości w godzinach, a skrypt dopasowuje przerwy. |
| `3` Ręczne | Własny zakres odstępu w sekundach (1-900). |

Dodatkowo:
- Po błędzie **429 (rate limit)** skrypt czeka tyle, ile każe Discord, i trwale zwalnia tempo (mnożnik widoczny w konsoli jako `tempo ×1.5` itd., maksymalnie ×6).
- Limit godzin w trybie Auto jest celem, a nie gwarancją. Przerwy nie spadną poniżej 6 minut, więc przy zbyt krótkim limicie skrypt wyświetli ostrzeżenie.
- Przy trybie Auto setki wiadomości to wiele godzin pracy. Komputer nie może w tym czasie zasnąć (Ustawienia, Zasilanie).

## 6. Co widać w konsoli

Dla każdej wiadomości:
- numer, pasek postępu, data i ID,
- podgląd treści, ikona 📎 (jeśli ma załącznik/embed) i planowana akcja (`USUŃ` / `EDYTUJ`),
- wynik: `✔` sukces, `↷` pominięta (już nie istnieje), `✘` błąd z kodem,
- timer do następnej akcji z godziną wznowienia i podglądem następnej wiadomości,
- czas, który upłynął, szacowany czas do końca i aktualny mnożnik tempa.

Na końcu: podsumowanie (sukcesy, błędy, pominięte, łączny czas).

## 7. Wznawianie po przerwie

Po Ctrl+C, awarii lub utracie internetu uruchom skrypt ponownie z **tym samym kanałem i zakresem dat**.

- Tryb usuwania: usunięte wiadomości zniknęły, więc nie pojawią się na liście.
- Tryb edycji: wiadomości z już wstawionym tekstem są pomijane.

## 8. Obsługa błędów

- **Timeouty i utrata połączenia:** każde żądanie ma limit 10 s (połączenie) i 30 s (odpowiedź). Skrypt ponawia do 6 razy z rosnącym odstępem (5, 10, 20... do 120 s), potem kończy się z komunikatem.
- **401:** token odrzucony, skrypt się zatrzymuje.
- **403:** brak uprawnień. Po 3 błędach skrypt się zatrzymuje.
- **404:** wiadomość już nie istnieje, jest pomijana.

## 9. Co i jak zmienić w kodzie

Stałe na górze pliku `bot.py`:

| Stała | Znaczenie | Domyślnie |
|---|---|---|
| `MAX_LEN` | Maks. długość tekstu (limit Discorda) | 2000 |
| `MIN_DELAY` | Minimalny odstęp między akcjami (s) | 1 |
| `MAX_DELAY` | Maksymalny odstęp między akcjami (s) | 900 (15 min) |
| `BREAK_MIN` | Minimalna długa przerwa w trybie Auto (s) | 60 (1 min) |
| `BREAK_MAX` | Maksymalna długa przerwa w trybie Auto (s) | 1200 (20 min) |

Inne miejsca:

- **Zakres trybu "Normalne":** w `main()` linia `manual = (1, 20)`. Zmień na np. `(2, 30)`.
- **Długość serii szybkich akcji:** w klasie `Pacer` wartość `random.randint(3, 6)` (występuje w `__init__` i `next_wait`).
- **Rozkład krótkich odstępów w trybie Auto:** `random.triangular(MIN_DELAY, 15, 4)` w `short_delay()`. Parametry to min, max i najczęstsza wartość.
- **Limity czasu połączenia:** `kwargs.setdefault("timeout", (10, 30))` w `request()`.
- **Liczba ponowień przy braku połączenia:** wartość `6` w `request()`.
- **Które wiadomości są brane pod uwagę:** warunek `m["type"] not in (0, 19)` (0 to zwykła wiadomość, 19 to odpowiedź). Inne typy (systemowe) nie są ruszane.
- **Folder, w którym szukane są pliki .txt:** funkcja `find_txt_files()`.

## 10. Ograniczenia

- **Nie da się cofnąć** usunięcia ani edycji. Skrypt nie robi kopii zapasowej.
- Skrypt rusza **tylko Twoje wiadomości** (filtr po ID Twojego konta).
- **Edycja zmienia tylko treść. Załączniki zostają.**
- Wiadomość oznaczona jako edytowana jest widoczna dla innych osób na czacie.
- Masowe operacje mogą skutkować powiadomieniem o zbyt wielu akcjach lub blokadą konta. Zawężaj zakres dat i rozkładaj pracę na kilka dni.
- Skrypt nie ukrywa, że jest automatem, i nie podszywa się pod oficjalnego klienta.

## 11. Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---|---|
| `ModuleNotFoundError: No module named 'requests'` | `python -m pip install requests python-dotenv` (tym samym Pythonem, którym uruchamiasz skrypt). |
| `Brak TOKEN w pliku .env` | Plik `.env` musi leżeć w folderze, z którego uruchamiasz skrypt, i zawierać linię `TOKEN=...`. |
| `Nieprawidłowy token` / `401` | Token wygasł lub jest błędny. Po zmianie hasła trzeba pobrać nowy. |
| `Błąd pobierania: 403` / `404` przy skanowaniu | Zły ID kanału albo brak dostępu do kanału. |
| Brak znalezionych wiadomości | Sprawdź zakres dat, ID kanału i ustawienia "Edytowane" oraz "Załączniki". |
| Dużo timeoutów | Sprawdź internet, VPN i antywirus (mogą blokować `discord.com`). |
| Ciągłe rate limity | Wybierz wolniejsze tempo lub zawęź zakres dat. |

**Zalecenie:** przed pierwszym użyciem przetestuj skrypt na małym zakresie dat, np. jednym dniu.
