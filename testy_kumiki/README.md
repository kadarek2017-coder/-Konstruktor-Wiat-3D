# Próba integracji Kumiki — połączenia ciesielskie

Ten folder jest **oddzielnym eksperymentem** i nie wpływa na uruchamianie Konstruktora Wiat 3D.

## Cel

Wykonać rzeczywistą geometrię czopa i gniazda między słupem 200 × 200 mm
a belką 100 × 200 mm i wyeksportować do OBJ, by później wyświetlić
w Three.js. To **cel testu**, a nie funkcja już wdrożona.

## Etap 1 — weryfikacja API

Kumiki nie jest dodawane do głównego `requirements.txt`, żeby nie
zepsuć istniejącej aplikacji ani procesu pakowania na macOS.

W osobnym środowisku:

```bash
python3 -m venv .venv-kumiki
source .venv-kumiki/bin/activate
python -m pip install kumiki
python testy_kumiki/sprawdz_kumiki.py
```

Skrypt sprawdza, czy zainstalowana wersja udostępnia wymagane funkcje,
i wypisuje ich sygnatury. **Nie generuje jeszcze modelu ani pliku OBJ**.

## Etap 2 — do zrobienia po potwierdzeniu API

- ustawić słup i belkę w odpowiedniej orientacji;
- wywołać funkcję połączenia czop–gniazdo;
- zbudować `Frame` i wyeksportować obie wycięte bryły do OBJ;
- zweryfikować geometrię i jednostki;
- przygotować import OBJ do Three.js i podgląd pojedynczego węzła.

Wymiary czopa, gniazda i sprawdzenie nośności wymagają niezależnej
weryfikacji projektowej. Sam model CAD nie jest projektem wykonawczym.

Dokumentacja: https://kumiki.build/docs/
