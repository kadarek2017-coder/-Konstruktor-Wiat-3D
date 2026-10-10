# Połączenie czop–gniazdo w Kumiki

Oddzielny podgląd geometrii; główna aplikacja wiaty nie korzysta jeszcze z tego węzła.
Testowana wersja: Kumiki 0.8.0, Python 3.12.

## Uruchomienie na Macu

W folderze repozytorium:

```bash
python3 -m venv .venv-kumiki
source .venv-kumiki/bin/activate
python -m pip install -r testy_kumiki/requirements.txt
python testy_kumiki/generuj_czop.py
python -m streamlit run testy_kumiki/podglad_obj.py
```

Jeśli środowisko już istnieje, zacznij od polecenia `source`.

W podglądzie wersji 10 przycisk **Wygeneruj poprawiony model** uruchamia
generator tym samym Pythonem co Streamlit i od razu wczytuje nowe pliki.
Każde wyświetlenie sprawdza geometrię OBJ, w tym orientację przekroju
czopa. Stary, błędny model jest blokowany, nawet jeśli pozostał po nim
plik `wymiary.json`. Tabela wymiarów pochodzi bezpośrednio z OBJ.

Pole **Połóż belkę płasko** przełącza przekrój między szerokością 100 mm
i wysokością 200 mm a szerokością 200 mm i wysokością 100 mm. Zmiana
automatycznie generuje dopasowany czop i gniazdo. Oś belki pozostaje na
Z=2200 mm; płaska belka ma spód na 2150 mm, a koniec czopa na 2250 mm.
Czop ma wtedy 150 × 66,67 mm i długość 100 mm.

Suwak **Uniesienie belki** w widoku 3D przesuwa belkę o 0–500 mm w osi Z.
**Rozsuń elementy** ustawia 350 mm, a **Złóż połączenie** przywraca 0 mm.
Rozsuwanie służy do oglądania czopa i gniazda; nie zmienia plików OBJ.
Belkę płasko można wygenerować także poleceniem:

```bash
python testy_kumiki/generuj_czop.py --flat
```

## Pełna rama i przesuwanie elementów

Opcja **Pełna rama** tworzy dwa słupy 200 × 200 mm w rozstawie osiowym
2400 mm i jedną belkę długości 3000 mm. Belka ma dwa rzeczywiste gniazda.
Można ją ustawić na sztorc lub płasko. Podgląd jest dostępny także
przez link **Rama z rzeczywistymi połączeniami** w głównej aplikacji.
Ta strona wymaga osobnych zależności z tego folderu; rama pozostaje
odrębnym modelem i nie zmienia jeszcze pełnej wiaty.

- Kliknij słup lub belkę albo wybierz nazwę w polu **Element**.
- Chwyć sam słup lub belkę lewym przyciskiem i przeciągnij. Element przesuwa się
  w płaszczyźnie ekranu, bez przeskoku do środka i bez obracania kamery.
- Przeciągnięcie tła obraca kamerę; rolka przybliża, prawy przycisk przesuwa widok.
- Opcjonalnie włącz **Strzałki do precyzyjnego przesuwania**, aby przesuwać
  element w wybranej osi X, Y lub Z.
- Pola X/Y/Z pokazują przesunięcie względem pozycji złożonej, w mm.
- **Przywróć element** zeruje jego przesunięcie.
- **Ukryj element** usuwa go z widoku. Ponowny wybór pokazuje go z powrotem.
- **Złóż całą ramę** przywraca pozycje i widoczność wszystkich elementów.
- **Pobierz element OBJ** zapisuje wybraną geometrię z aktualnym przesunięciem
  w milimetrach, bez przesunięcia kamery używanego do centrowania widoku.

Przesuwanie i ukrywanie nie zmienia źródłowych plików ani dopasowania
połączeń. Odświeżenie widoku przywraca złożoną ramę.

```bash
python testy_kumiki/generuj_czop.py --frame
python testy_kumiki/generuj_czop.py --frame --flat
```

## Szkielet przestrzenny

Włącz **Szkielet przestrzenny — dwie ramy i belki łączące**.
Model zawiera cztery słupy, dwie belki ram długości 3000 mm i dwie
belki łączące w osi Y. Ramy mają rozstaw 3000 mm, a słupy każdej ramy
rozstaw 2400 mm. Każdy element można chwycić i przeciągnąć osobno,
ukryć, przywrócić lub pobrać jako OBJ.

Obie ramy mają rzeczywiste czopy i gniazda. Belki łączące leżą na
belkach ram, z równym końcem na zewnętrznych krawędziach podpór:
mają długość 3100 mm na sztorc albo 3200 mm płasko. Nie mają jeszcze
wycięć ani łączników. Miecze i krokwie będą dodane w kolejnych etapach.
Suwak uniesienia podnosi wszystkie belki razem; przeciąganie pozostaje
niezależne dla każdego elementu. To model poglądowy, nie ukończony
projekt wykonawczy.

```bash
python testy_kumiki/generuj_czop.py --skeleton
python testy_kumiki/generuj_czop.py --skeleton --flat
```

## Graficzny wybór i katalog części

W wersji 10 panel po prawej zawiera graficzne kafelki wszystkich elementów
modelu. Miniatury powstają z ich rzeczywistej siatki. Kliknij kafelek,
aby zaznaczyć część (również ukrytą), potem chwyć ją w scenie i przeciągnij.
Zaznaczenie jest widoczne na kafelku i na modelu; ukryte części mają
przygaszony kafelek. Obie sekcje panelu można zwinąć.

Katalog dodawania zawiera słup, belkę na sztorc, belkę płasko, miecz,
krokiew i płatew. Przeciągnij kafelek do widoku 3D, aby umieścić nową
część w miejscu upuszczenia, lub kliknij, aby dodać ją w środku widoku.
Następnie przesuwaj część myszką lub polami X/Y/Z.

Włącz **Użyj powyższych wymiarów**, aby zastosować własną długość,
szerokość i wysokość przekroju. Wymiary są podane w milimetrach.
Dla słupa i miecza długość biegnie wzdłuż elementu; miecz ma wstępny
kąt 45°, a krokiew 12°. Katalog dostarcza pełne elementy bez wycięć.
Nie dopasowuje automatycznie czopów i gniazd ani nie sprawdza kolizji
nowych części. Źródłowe połączenia ram pozostają w geometrii OBJ.

Nowe części można zaznaczać, ukrywać, przywracać i pobierać jako OBJ.
Pole **Liczba sztuk** dotyczy klikniętego lub przeciągniętego typu:
wpisz np. 6 i wybierz słup, aby dodać sześć niezależnych słupów.
Liczba musi być całkowita, od 1 do 100; projekt mieści do 500 części.
Serie układają się obok siebie w osi Y z odstępem 150 mm między
przekrojami. Kamera pokazuje cały układ po dodaniu serii; możesz
też użyć **Pokaż wszystkie elementy**. Licznik obejmuje także ukryte części.

**Zapisz projekt** pobiera plik `projekt-wiaty.json` zawierający wymiary
nowych części, pozycje, pozycje przywracania i widoczność wszystkich
elementów. **Wczytaj projekt** zastępuje bieżący układ zapisanym.
Przed wczytaniem ustaw te same opcje belki płasko, pełnej ramy i
szkieletu przestrzennego. Błędny lub niepasujący plik nie zastępuje układu.
Odświeżenie, generowanie lub przełączenie wariantu odtwarza bazowy model,
dlatego wcześniej zapisz własny układ. JSON przechowuje układ, a OBJ
nadal służy do eksportowania geometrii pojedynczego elementu.

## Dokładne ustawienie względem elementu

1. Zaznacz słup lub belkę i w sekcji **Dokładne ustawienie** kliknij
   **Użyj zaznaczonego jako odniesienia**.
2. Wybierz oś X/Y/Z, odległość (np. 2000 mm), pomiar między środkami
   lub prześwit między krawędziami. Ujemna odległość oznacza przeciwny kierunek.
3. Włącz **Dodawaj względem odniesienia** i kliknij typ w katalogu.
   Alternatywnie zaznacz inną istniejącą część i kliknij **Ustaw zaznaczony element**.
4. Przy wielu sztukach pierwsza część otrzymuje podaną odległość, kolejne
   zwiększają ją o **Rozstaw serii**. W trybie prześwitu rozstaw dotyczy
   kolejnych środków części tego samego typu.

Pomiar używa środka i krawędzi obwiedni rzeczywistej geometrii, w osiach
modelu, niezależnie od kamery. **Wyrównaj spód** ustawia taką samą dolną
wysokość przy dodawaniu w X/Y. Dla elementów ukośnych obwiednia nie jest
osią długości drewna. Niebieska linia i odczyt pokazują odległość zaznaczonej
części od odniesienia. To ustawienie jednorazowe, bez trwałego więzu;
przesunięcie odniesienia nie przesuwa pozostałych części automatycznie.
Pozycje są zachowywane w JSON, a odniesienie wybierasz ponownie po wczytaniu.

## Baza połączeń ciesielskich i stolarskich

Plik `polaczenia.json` zawiera 12 pozycji z kategorią, opisem parametrów
i statusem. Panel **Baza połączeń** pokazuje miniatury i filtr kategorii.
Czop–gniazdo oraz pół drewna mają rzeczywistą geometrię przykładów
wycinaną w Kumiki. **Dodaj przykład z wycięciami** dodaje dwa nowe,
dopasowane elementy. Przykłady można rozsuwać, eksportować i zapisywać
w projekcie. Pozycje pozostałych połączeń mają schematy poglądowe i
status **Katalog — bez generatora**; nie można dodawać ich wycięć.

Czop–gniazdo korzysta ze sprawdzonego słupa 200×200 i belki 1600×100×200.
Pół drewna ma dwie prostopadłe belki 1200×100×200 z wycięciem po połowie
wysokości. Ich objętości, zamknięcie i brak kolizji są sprawdzane przed
udostępnieniem. Parametry tych przykładów są stałe. Wersja 10 nie wycina
jeszcze wybranego połączenia w dowolnej wskazanej parze, nie przelicza
wycięć po przesunięciu ani nie ocenia nośności.

## Jednostki i położenie

Kumiki otrzymuje wymiary w **metrach**, przez `k.mm(...)`.
Eksport OBJ jest przeliczany na **milimetry** przed zapisaniem w `wyniki/`.
Podgląd wczytuje te same zweryfikowane pliki. Nie korzysta z wcześniejszego
katalogu eksperymentalnego `finite_joint` ani z modyfikacji prywatnych pól CSG.

- Słup: przekrój 200 × 200 mm, podstawa Z=0.
- Belka: długość 1600 mm w osi X, szerokość 100 mm w osi Y,
  wysokość 200 mm w osi Z.
- Oś belki: Z=2200 mm. Jej spód i bark słupa: Z=2100 mm.
- Koniec czopa: Z=2300 mm; to całkowita wysokość wyciętego słupa.
  Nominalne `length=2200 mm` w tym teście określa położenie węzła,
  a Kumiki przedłuża czop do góry belki.
- Czop ma 150 mm w osi X (wzdłuż belki) i 33,33 mm w osi Y.
  Gniazdo pozostawia pełne ścianki po obu stronach szerokości belki.
  Wymiary są przekazywane jawnie, ponieważ automatyczny wrapper Kumiki
  zamieniał osie czopa i otwierał gniazdo na boki belki.

Poprzedni skrypt przekazywał milimetry jako metry. Przy nieskończonym końcu
bryły triangulator stosował ograniczenie 1000 jednostek, przez co OBJ słupa
kończył się przed węzłem. Przeliczenie jednostek usuwa przyczynę problemu.

Eksport sprawdza wymiary, położenie, zamknięcie i ubytek objętości brył.
`wymiary.json` zapisuje wynik kontroli. Podgląd pokazuje wymiary i używa
pionowej osi Z. Wyniki i środowisko są pomijane przez Git.

## Test regresji

```bash
python -m unittest testy_kumiki.test_geometria testy_kumiki.test_polaczenia -v
```

Test odczytuje zapisane pliki OBJ, sprawdza ich wymiary i objętości po
wycięciu, brak kolizji, orientację przekroju czopa oraz zamknięty obrys
gniazda na poziomie osi belki.

Geometria służy do podglądu. Wymiary połączenia i nośność wymagają
niezależnej weryfikacji projektowej przed wykonaniem konstrukcji.
