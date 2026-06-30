# Weather Alerting System 
## Przedmiot: Autonomiczne Systemy Eksperckie i Eksploracja Danych

Niniejsze repozytorium zawiera implementację serverless systemu ostrzegania przed niebezpiecznymi lub istotnymi zjawiskami pogodowymi, opartego na chmurze **Amazon Web Services (AWS)**. System cyklicznie pobiera dane z udostępnionego Weather REST API, archiwizuje surowe odczyty, dokonuje ewaluacji reguł eksperckich oraz rejestruje i opcjonalnie dystrybuuje alerty w czasie rzeczywistym.

---

## 1. Cel Projektu
Głównym celem systemu jest ciągły i zautomatyzowany monitoring warunków meteorologicznych dla stacji pogodowej, wykrywanie anomalii i stanów niebezpiecznych w oparciu o zdefiniowane progi eksperckie, oraz natychmiastowe logowanie zdarzeń do bazy danych i powiadamianie użytkowników za pomocą wiadomości e-mail.

## 2. Architektura Referencyjna i Przepływ Danych
Projekt ściśle separuje poszczególne etapy przetwarzania zgodnie z zalecaną architekturą:
`REST API Collector -> Raw Storage (S3) -> Validation/Expert Rules Engine (Lambda) -> Alert History Database (DynamoDB) & Notification Workflow (SNS)`

### Komponenty AWS:
1. **Amazon EventBridge:** Służy jako harmonogram wyzwalający system automatycznie co 15 minut, zapewniając cykliczne pobieranie danych bez konieczności ciągłego uruchamiania serwerów.
2. **AWS Lambda:** Kod systemu napisane w języku Python. Odpowiada za pobranie danych z API, natychmiastowy zapis surowego pliku JSON, walidację danych oraz ewaluację reguł.
3. **Amazon S3:** Służy jako niezmienny magazyn danych surowych. Zapisuje pełne odpowiedzi JSON z API.
4. **Amazon DynamoDB:** Baza danych przechowująca kompletną historię alertów. Każdy wpis zawiera unikalny identyfikator alertu, znacznik czasu, identyfikator stacji, wyzwolone reguły oraz aktualne parametry fizyczne.
5. **Amazon SNS:** Usługa powiadomień, która w ułamku sekundy dystrybuuje komunikaty o krytycznych zagrożeniach bezpośrednio na adres e-mail subskrybenta.

---

## 3. Struktura Projektu i Magazynu Danych
* **S3 Bucket Layout:**
    * – niezmienione, surowe odpowiedzi z API pogodowego.
* **DynamoDB Table Scheme:**
    * `alert_id` (String, Partition Key) – unikalny identyfikator UUID v4.
    * `timestamp` (String) – czas wykrycia zdarzenia w formacie ISO 8601.
    * `station_id` (String) – identyfikator stacji monitorowanej.
    * `triggered_rules` (String) – opisowa nazwa złamanych reguł eksperckich.
    * `current_temp` (String) – temperatura w momencie alertu.
    * `current_wind` (String) – prędkość wiatru w momencie alertu.

---

## 4. Instrukcja Uruchomienia i Wdrożenia (Execution Steps)

### Krok 1: Konfiguracja Magazynu Surowego (Amazon S3)
1. Przejdź do usługi **S3** w konsoli AWS i kliknij **Create bucket**.
2. Wprowadź nazwę koszyka: `weather-raw-data-198093-197564` w regionie `us-east-1`.
3. Pozostaw opcję *Block all public access* włączoną i utwórz koszyk.

### Krok 2: Konfiguracja Rejestru Alertów (Amazon DynamoDB)
1. Przejdź do usługi **DynamoDB** i kliknij **Create table**.
2. Wprowadź nazwę tabeli: `WeatherAlertHistory`.
3. Jako **Partition key** ustaw pole `alert_id` (typ: **String**). Pozostałe opcje pozostaw domyślne i kliknij **Create table**.

### Krok 3: Konfiguracja Systemu Powiadomień (Amazon SNS)
1. Przejdź do usługi **SNS** -> **Topics** -> **Create topic**.
2. Wybierz typ **Standard**, nadaj nazwę `WeatherAlerts` i utwórz temat.
3. Skopiuj wygenerowany identyfikator **ARN** tematu.
4. Kliknij **Create subscription**, jako protokół wybierz **Email**, a w polu *Endpoint* wpisz swój adres e-mail.
5. Odbierz pocztę elektroniczną i kliknij link **Confirm subscription**, aby aktywować powiadomienia.

### Krok 4: Wdrożenie Logiki Przetwarzania (AWS Lambda)
1. Przejdź do usługi **Lambda** -> **Create function** (Author from scratch).
2. Nazwij funkcję `WeatherAlertEngine`, jako środowisko (Runtime) wybierz **Python 3.12**.
3. W sekcji *Advanced settings* włącz opcję *Custom execution role* i z listy wybierz **LabRole** (zapewnia ona uprawnienia zapisu do S3, DynamoDB i SNS).
4. Po utworzeniu funkcji przejdź do zakładki **Configuration** -> **General configuration** -> **Edit** i zmień wartość parametru **Timeout** z 3 sekund na **15 sekund**, a następnie zapisz.
5. W zakładce **Code** wklej zawartość pliku skryptu silnika reguł (upewnij się, że nazwa bucketu S3 i ARN z SNS odpowiadają Twoim zasobom).
6. Kliknij **Deploy**. Przeprowadź test ręczny za pomocą przycisku **Test**, konfigurując dowolne zdarzenie testowe o nazwie `Test1`.

### Krok 5: Automatyzacja Cykliczna (Amazon EventBridge)
1. W panelu swojej funkcji Lambda kliknij przycisk **+ Add trigger**.
2. Z listy wybierz **EventBridge (CloudWatch Events)**.
3. Wybierz opcję *Create a new rule*, nadaj jej nazwę `SkanerPogodyCo15Minut`.
4. Jako typ reguły wybierz *Schedule expression* i wprowadź wartość `rate(15 minutes)`.
5. Kliknij **Add**. Od tej pory system będzie działał w pełni autonomicznie.

---
## 5. Wykorzystane Biblioteki
Kod został napisany przy użyciu wyłącznie natywnych bibliotek standardowych Pythona:
* `json` – serializacja i deserializacja struktur danych.
* `urllib.request` – bezobsługowe wysyłanie zapytań HTTP/HTTPS do REST API.
* `boto3` – wbudowane w środowisko AWS SDK dla języka Python 
* `datetime`, `uuid` – generowanie sygnatur czasowych i losowych identyfikatorów.
