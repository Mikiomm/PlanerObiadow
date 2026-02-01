# PlanerObiadow

Krótkie instrukcje uruchomienia i konfiguracji środowiska lokalnego.

## Konfiguracja zmiennych środowiskowych ✅
1. Skopiuj przykładowy plik:

   cp .env.example .env

   (Na Windows PowerShell: `Copy-Item .env.example .env`)

2. Otwórz `.env` i uzupełnij wartość `DATABASE_URL` (connection string do PostgreSQL / Supabase):

   Format przykładowy: `postgresql://username:password@host:5432/dbname`

3. Plik `.env` jest ignorowany przez Git (już zdefiniowany w `.gitignore`). Nie commituj sekretów.

## Uruchomienie lokalne
1. Zainstaluj zależności:

   pip install -r requirements.txt

2. Uruchom aplikację:

   python app.py

Aplikacja przy pierwszym uruchomieniu stworzy tabelę `dinners` i zainicjalizuje przykładowe dania, jeśli `DATABASE_URL` jest ustawiony.

## Uwaga
- Jeżeli `DATABASE_URL` nie jest ustawiony, aplikacja działa na wewnętrznej liście przykładowych dań (fallback). Aby korzystać z bazy Supabase ustaw `DATABASE_URL` w `.env` lub w systemowych zmiennych środowiskowych.
