# Discord Message Cleaner

Skrypt, który usuwa albo zamienia na wskazany tekst **Twoje własne wiadomości** z wybranego kanału (serwer lub DM) w podanym zakresie dat. Działa porcjami z odstępami, a na bieżąco pokazuje postęp i szacowany czas do końca.

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

Skrypt zadaje pytania w tej kolejności:

| Krok | Pytanie | Opis |
|---|---|---|
| 1 | **ID kanału** | ID kanału lub DM. Włącz tryb programisty w Discordzie, kliknij kanał prawym przyciskiem i wybierz "Kopiuj ID kanału". |
| 2 | **Początek zakresu** | `1` od podanej daty, `2` od początku konwersacji. |
| 3 | **Koniec zakresu** | `1` do podanej daty (włącznie), `2` do końca konwersacji (najnowsze wiadomości). |
| 4 | **Tryb** | `1` usuń, `2` zamień na tekst z pliku. |
| 5 | **Plik .txt** (tryb 2) | Skrypt sam znajduje pliki `.txt` w folderze skryptu i bieżącym folderze. Przy jednym pyta o potwierdzenie, przy kilku pokazuje listę. Można też podać ścieżkę ręcznie. Pokazuje podgląd przed zatwierdzeniem. |
| 6 | **Edytowane** | Czy uwzględniać wiadomości, które już były edytowane (Y/N). |
| 7 | **Załączniki/embedy** (tryb 2) | Co robić z wiadomościami z obrazem, plikiem lub podglądem linku. |
| 8 | **Odpowiedzi** | Co robić z wiadomościami, które odpowiadają na inne wiadomości. |
| 9 | **Serie wiadomości** (tryb 2) | Czy usuwać nadmiarowe, następujące po sobie Twoje wiadomości. |
| 10 | **Tempo** | Patrz sekcja "Tempo". |

Po skanowaniu skrypt pokazuje liczbę znalezionych wiadomości, podział na edycje i usunięcia, szacowany czas i prosi o ostateczne potwierdzenie. **Ctrl+C** zatrzymuje skrypt bezpiecznie i pokazuje podsumowanie.

## 4. Zakres dat

- Daty podajesz w formacie `YYYY-MM-DD` i są liczone w **czasie lokalnym** komputera. Dzień "do" jest wliczony w całości.
- Jeśli data "od" jest późniejsza niż "do", skrypt zgłasza błąd i prosi o podanie zakresu ponownie (wcześniej takie zakresy dawały 0 wiadomości).
- Możesz pominąć któryś koniec zakresu: "od początku konwersacji" skanuje do samego początku kanału, a "do końca konwersacji" zaczyna od najnowszej wiadomości. Dla dużych kanałów skanowanie bez granic trwa dłużej.
- Po wyborze skrypt wypisuje, jaki zakres przyjął.

## 5. Tryby działania

### Tryb 1: Usuń
Usuwa wszystkie pasujące wiadomości, razem z załącznikami.

### Tryb 2: Zamień na tekst
Edytuje treść wiadomości na tekst z pliku `.txt`.

- Tekst: maksymalnie **2000 znaków**, cały plik trafia jako jedna wiadomość.
- Wiadomości, które już mają dokładnie ten tekst, są pomijane.
- Edytowana wiadomość dostaje widoczną etykietę **(edited)**. Tego nie da się ukryć.

### Wiadomości z załącznikami i embedami
| Opcja | Działanie |
|---|---|
| `1` Tylko edytuj | Zmienia tekst, **wgrane załączniki (obrazy, pliki) zostają**. |
| `2` Usuń całą wiadomość | Usuwa wiadomość razem z załącznikiem. |
| `3` Pomiń | Takie wiadomości zostają nietknięte. |

Podglądy linków (automatyczne embedy) zwykle znikają po edycji, jeśli nowy tekst nie zawiera tego linku. Wiadomość z samym załącznikiem i bez tekstu dostanie Twój tekst nad załącznikiem. W trybie 1 pytanie o media nie pojawia się, bo usuwane jest wszystko.

### Odpowiedzi na inne wiadomości
| Tryb | Opcje |
|---|---|
| Tryb 2 | `1` edytuj tekst, `2` usuń, `3` zostaw |
| Tryb 1 | `1` usuń, `2` zostaw |

Reguła dla odpowiedzi ma **pierwszeństwo** przed regułą dla mediów. Odpowiedź z załącznikiem jest traktowana wg reguły dla odpowiedzi, a przy edycji załącznik zostaje. W konsoli odpowiedzi mają ikonę ↩.

### Maks. 1 Twoja wiadomość pod rząd (tryb 2)
Opcjonalnie skrypt usuwa nadmiarowe, następujące po sobie Twoje wiadomości, tak żeby na jedną wiadomość drugiej osoby przypadała najwyżej jedna Twoja.

Przykład: 4 Twoje, 1 cudza, 2 Twoje, 3 cudze → **1 Twoja, 1 cudza, 1 Twoja, 3 cudze**.

- Wybierasz, którą wiadomość z serii zostawić: najnowszą albo najstarszą.
- Zostawiona wiadomość przechodzi przez zwykłe reguły (edycja na tekst z pliku itd.), a pozostałe z serii są usuwane.
- W konsoli nadmiarowe wiadomości mają dopisek "nadmiarowa z serii", a w podsumowaniu przed startem widać, ile ich jest.
- Za wiadomość "drugiej osoby" uznawana jest każda wiadomość, która nie jest Twoją zwykłą wiadomością lub odpowiedzią (w tym systemowe).

**Ograniczenia tej opcji:**
- Serie są liczone **tylko w wybranym zakresie dat**. Jeśli seria zaczyna się przed datą "od" (lub kończy po dacie "do"), skrypt zobaczy tylko jej część.
- Twoje reguły mają pierwszeństwo: nadmiarowa wiadomość nie zostanie usunięta, jeśli wyklucza ją filtr edytowanych, "zostaw odpowiedzi" albo "pomiń media". Wtedy seria może zostać dłuższa niż 1.

## 6. Tempo

| Opcja | Działanie |
|---|---|
| `1` Normalne | Losowy odstęp 1-20 s między akcjami. |
| `2` Auto | Serie 3-6 szybkich akcji (odstęp 1-15 s), potem długa przerwa 6-20 min. Im więcej akcji w ostatniej godzinie, tym dłuższa przerwa. Opcjonalnie podajesz maksymalny czas całości w godzinach, a skrypt dopasowuje przerwy. |
| `3` Ręczne | Własny zakres odstępu w sekundach (1-900). |
| `4` **FAST-RISKY** | Zero odstępu między akcjami. Dostępne zarówno przy usuwaniu, jak i przy edycji. |

**FAST-RISKY:**
- Wymaga dodatkowego potwierdzenia. Po odmowie skrypt przełącza się na tempo Normalne.
- Akcje wykonują się jedna po drugiej. Discord będzie zwracał rate limity (429), a skrypt je respektuje i czeka tyle, ile każe serwer.
- Ryzyko flagi lub blokady konta jest **wyraźnie wyższe**, szczególnie przy edycjach (masowe edycje są częściej limitowane niż usunięcia).
- W podsumowaniu widać liczbę rate limitów, które wystąpiły.

Dodatkowo:
- Po błędzie **429** skrypt trwale zwalnia tempo (mnożnik widoczny w konsoli jako `tempo ×1.5` itd., maksymalnie ×6). Nie dotyczy FAST-RISKY.
- Limit godzin w trybie Auto jest celem, a nie gwarancją. Przerwy nie spadną poniżej 6 minut, więc przy zbyt krótkim limicie skrypt wyświetli ostrzeżenie.
- Przy trybie Auto setki wiadomości to wiele godzin pracy. Komputer nie może w tym czasie zasnąć (Ustawienia, Zasilanie).

## 7. Co widać w konsoli

Dla każdej wiadomości:
- numer, pasek postępu, data i ID,
- podgląd treści, ikony 📎 (załącznik/embed) i ↩ (odpowiedź) oraz planowana akcja (`USUŃ` / `EDYTUJ`),
- wynik: `✔` sukces, `↷` pominięta (już nie istnieje), `✘` błąd z kodem,
- linia czasu: ile upłynęło, ile zostało, **godzina zakończenia** (z datą, jeśli wypada innego dnia), mnożnik tempa i rzeczywiste tempo w akcjach na godzinę,
- timer do następnej akcji z godziną wznowienia i podglądem następnej wiadomości.

### Szacowanie czasu
Szacunek jest korygowany po każdej akcji na podstawie realnego tempa pracy:
- mierzy faktyczny czas akcji (razem z oczekiwaniem na rate limity),
- w trybie Auto mierzy faktyczne krótkie odstępy i długie przerwy oraz liczy, ile przerw jeszcze zostało w kolejnych seriach,
- uwzględnia wolniejsze tempo po rate limitach.

Na początku szacunek jest przybliżony, bo skrypt nie zna jeszcze realnych przerw. Po kilku seriach staje się dokładniejszy.

Na końcu skrypt wyświetla podsumowanie: sukcesy, błędy, pominięte i łączny czas.

## 8. Brak podwójnych akcji

- Wiadomości są deduplikowane już podczas skanowania (po ID).
- Przed każdą akcją skrypt sprawdza, czy ta wiadomość nie została już przetworzona w tym przebiegu.
- Przy ponownym uruchomieniu tryb edycji pomija wiadomości z już wstawionym tekstem, a usunięte wiadomości nie pojawiają się na liście.

## 9. Wznawianie po przerwie

Po Ctrl+C, awarii lub utracie internetu uruchom skrypt ponownie z **tym samym kanałem i zakresem dat**. Pracę wznowi od miejsca przerwania (patrz sekcja 8).

## 10. Obsługa błędów

- **Timeouty i utrata połączenia:** każde żądanie ma limit 10 s (połączenie) i 30 s (odpowiedź). Skrypt ponawia do 6 razy z rosnącym odstępem (5, 10, 20... do 120 s), potem kończy się z komunikatem.
- **401:** token odrzucony, skrypt się zatrzymuje.
- **403:** brak uprawnień. Po 3 błędach skrypt się zatrzymuje.
- **404:** wiadomość już nie istnieje, jest pomijana.

## 11. Co i jak zmienić w kodzie

Stałe na górze pliku `bot.py`:

| Stała | Znaczenie | Domyślnie |
|---|---|---|
| `MAX_LEN` | Maks. długość tekstu (limit Discorda) | 2000 |
| `MIN_DELAY` | Minimalny odstęp między akcjami (s) | 1 |
| `MAX_DELAY` | Maksymalny odstęp między akcjami (s) | 900 (15 min) |
| `BREAK_MIN` | Minimalna długa przerwa w trybie Auto (s) | 360 (6 min) |
| `BREAK_MAX` | Maksymalna długa przerwa w trybie Auto (s) | 1200 (20 min) |

Inne miejsca:

- **Zakres trybu "Normalne":** w `main()` linia `manual = (1, 20)` (występuje dwa razy: przy wyborze `1` i przy odmowie FAST-RISKY). Zmień na np. `(2, 30)`.
- **Długość serii szybkich akcji (Auto):** w klasie `Pacer` wartość `random.randint(3, 6)` (w `__init__` i `next_wait`).
- **Rozkład krótkich odstępów (Auto):** `random.triangular(MIN_DELAY, 15, 4)` w `short_delay()`. Parametry to min, max i najczęstsza wartość.
- **Limity czasu połączenia:** `kwargs.setdefault("timeout", (10, 30))` w `request()`.
- **Liczba ponowień przy braku połączenia:** wartość `6` w `request()`.
- **Które wiadomości są brane pod uwagę:** funkcja `mine_ok()` (typ `0` to zwykła wiadomość, `19` to odpowiedź). Inne typy (systemowe) nie są ruszane.
- **Reguły decydujące o akcji dla wiadomości:** funkcja `decide()` w `main()`.
- **Folder, w którym szukane są pliki .txt:** funkcja `find_txt_files()`.

## 12. Ograniczenia

- **Nie da się cofnąć** usunięcia ani edycji. Skrypt nie robi kopii zapasowej.
- Skrypt rusza **tylko Twoje wiadomości** (filtr po ID Twojego konta).
- Edycja zmienia tylko treść. Załączniki zostają.
- Wiadomość oznaczona jako edytowana jest widoczna dla innych osób na czacie.
- Masowe operacje mogą skutkować powiadomieniem o zbyt wielu akcjach lub blokadą konta. Zawężaj zakres dat i rozkładaj pracę na kilka dni.
- Skrypt nie ukrywa, że jest automatem, i nie podszywa się pod oficjalnego klienta.

## 13. Rozwiązywanie problemów

| Problem | Rozwiązanie |
|---|---|
| `ModuleNotFoundError: No module named 'requests'` | `python -m pip install requests python-dotenv` (tym samym Pythonem, którym uruchamiasz skrypt). |
| `Brak TOKEN w pliku .env` | Plik `.env` musi leżeć w folderze, z którego uruchamiasz skrypt, i zawierać linię `TOKEN=...`. |
| `Nieprawidłowy token` / `401` | Token wygasł lub jest błędny. Po zmianie hasła trzeba pobrać nowy. |
| `Błąd pobierania: 403` / `404` przy skanowaniu | Zły ID kanału albo brak dostępu do kanału. |
| 0 znalezionych wiadomości | Sprawdź ID kanału, zakres dat (czas lokalny, "od" nie może być późniejsze niż "do") oraz ustawienia: edytowane, media, odpowiedzi. Wiadomości wykluczone przez Twoje reguły są liczone w linii "pominięte". |
| Wiadomości z krańców zakresu nie są wykrywane | Granice dni są liczone w czasie lokalnym. Rozszerz zakres o jeden dzień z każdej strony. |
| Dużo timeoutów | Sprawdź internet, VPN i antywirus (mogą blokować `discord.com`). |
| Ciągłe rate limity | Wybierz wolniejsze tempo lub zawęź zakres dat. W FAST-RISKY rate limity są normalne. |

**Zalecenie:** przed pierwszym użyciem przetestuj skrypt na małym zakresie dat, np. jednym dniu.
