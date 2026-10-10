# AGENT.MOD — Wood Construction Designer

Status: aktywna specyfikacja produktu i zasady pracy nad aplikacją.
Repozytorium: kadarek2017-coder/-Konstruktor-Wiat-3D

## 1. Cel projektu
Zbuduj nowoczesną, szybką i maksymalnie intuicyjną aplikację desktopową/webową do projektowania konstrukcji drewnianych: więźb dachowych, konstrukcji szkieletowych, wiat, altan, pergoli, stropów, ścian i prostych konstrukcji budynków.

Najważniejsza zasada produktu:
> Użytkownik nie powinien potrzebować specjalistycznej wiedzy CAD. Widzi konstrukcję, klika element, zmienia go i natychmiast widzi rezultat.

## 2. Priorytety
1. Intuicyjność.
2. Prostota obsługi.
3. Szybkość tworzenia konstrukcji.
4. Czytelna wizualizacja 3D.
5. Dokładność wymiarowa.
6. Automatyzacja powtarzalnych czynności.
7. Możliwość późniejszego dodania obliczeń konstrukcyjnych.
8. Możliwość późniejszego eksportu do CNC.

Nie dodawaj skomplikowanych funkcji kosztem prostoty interfejsu.

## 3. Architektura — zasada obowiązkowa
Oddziel warstwy:
UI → logika aplikacji → model konstrukcji → silnik geometrii → dane projektu.

Logika konstrukcji nie może być związana bezpośrednio z interfejsem ani z jednym silnikiem 3D.

Główny model dokumentu:
- ProjectModel
  - elements[]
  - joints[]
  - dimensions[]
  - materials[]
  - groups[]
  - constraints[]
  - settings

TimberElement powinien zawierać co najmniej:
- id
- type
- startPoint
- endPoint
- width
- height
- material
- localAxisX/localAxisY/localAxisZ
- rotationAroundAxis
- connections

Element musi znać własny lokalny układ współrzędnych: początek, koniec, górę, dół, lewą i prawą stronę. Jest to wymagane dla krokwi, elementów obróconych, połączeń ciesielskich i przyszłego CNC.

## 4. Główne systemy aplikacji
Architektura ma przewidywać osobne moduły:
- SelectionManager — zaznaczanie pojedyncze i wielokrotne.
- PlacementEngine — przesuwanie, dokładne pozycjonowanie, kopiowanie i powielanie.
- SnapEngine — inteligentne przyciąganie.
- GuideEngine — linie pomocnicze i relacje geometryczne.
- ConstraintEngine — opcjonalne zależności wymiarowe.
- JointEngine — parametryczne połączenia i cięcia.
- CommandHistory — każda operacja obsługuje undo/redo.
- ProjectSerializer — zapis/odczyt kompletnego projektu.
- Material/BOM Engine — materiały i zestawienie drewna.

## 5. Interfejs
Główne okno: górny pasek, lewe drzewo projektu, centralny viewport, prawy panel właściwości.

Górny pasek pokazuje tylko najważniejsze narzędzia:
Nowy projekt, Otwórz, Zapisz, Cofnij, Ponów, Belka, Słup, Krokiew, Ściana, Strop, Dach, Połączenie, Wymiar, 2D, 3D, Materiały, Dokumentacja.

Zaawansowane funkcje chowaj w dodatkowych panelach.

## 6. Viewport 3D
Użytkownik musi móc:
- obracać, przesuwać i przybliżać kamerę,
- zaznaczać element kliknięciem,
- zaznaczać wiele elementów,
- przeciągać elementy myszką,
- kopiować, obracać i usuwać,
- widzieć podświetlenie elementu pod kursorem.

Po zaznaczeniu pokaż podstawowe dane elementu: ID, typ, przekrój, długość, materiał.

## 7. Selection Manager — obowiązkowe
- klik = zaznacz jeden element,
- Ctrl/Cmd + klik = dodaj/usuń element z zaznaczenia,
- przeciągnięcie obszaru = zaznacz wiele,
- ESC = wyczyść zaznaczenie.

Stan zaznaczenia musi być przechowywany niezależnie od renderera.
Po zaznaczeniu dwóch kompatybilnych elementów aplikacja może zaoferować „Połącz”.

## 8. Panel właściwości
Dla zaznaczonego elementu pokazuj i pozwalaj zmieniać:
typ, materiał, szerokość, wysokość, długość, kąt, X/Y/Z i obrót.
Zmiana wartości natychmiast aktualizuje tylko zmieniony element modelu 3D.

## 9. Dodawanie elementów
Belka/krokiew: klik 1 = początek, klik 2 = koniec.
Słup: prosty tryb wstawiania z wysokością.
Domyślny przekrój może wynosić 80 × 180 mm.
Po utworzeniu wszystkie parametry są edytowalne.

Obsługiwane typy minimum:
BELKA, SŁUP, KROKIEW, PŁATEW, MURŁATA, ŁATA, DESKA, BELKA STROPOWA, SŁUPEK ŚCIENNY.

## 10. Smart Snap
Przyciąganie do:
- końca,
- środka,
- krawędzi,
- osi,
- narożnika,
- powierzchni,
- punktu przecięcia.

Pokazuj czytelne oznaczenie: KONIEC, ŚRODEK, OŚ itd.

## 11. Smart Guides
Podczas rysowania i przesuwania wykrywaj:
- równoległość,
- prostopadłość,
- wspólną wysokość,
- wspólną oś,
- środek elementu.

## 12. Precyzyjne pozycjonowanie
Użytkownik może przeciągać element swobodnie, ale zawsze musi istnieć możliwość podania dokładnej wartości.

Przykład: kopiowanie słupa → przeciągnięcie → wyświetlenie odległości → wpisanie „2000” → Enter.

Obsługuj odległość względem elementu, osi, powierzchni lub punktu odniesienia.

## 13. Powielanie / Array
Użytkownik może podać:
- liczbę elementów,
- rozstaw,
- kierunek X/Y/Z lub kierunek wskazany w modelu.

Każda kopia dostaje własne ID. Funkcja jest szczególnie ważna dla słupów, krokwi, łat, belek stropowych i ścian.

## 14. Constraints
Opcjonalne, proste dla użytkownika zależności:
- odległość,
- równoległość,
- prostopadłość,
- wspólna wysokość/oś.

Możliwość „zablokowania” wymiaru. ConstraintEngine ma być niezależny od UI.

## 15. Biblioteka drewna
Materiały minimum: C24, C30, GL24, GL28.
Model danych musi pozwalać później dodawać parametry techniczne i inne materiały.

## 16. Połączenia — Joint Engine
Joint jest osobnym, parametrycznym obiektem odnoszącym się do elementów; nie jest tylko geometrią renderera.

Przykład:
Joint J001:
- elementA = S001
- elementB = B004
- type = mortise_tenon
- parameters = szerokość, głębokość, offset itd.

Kategorie relacji:
- Belka ↔ Słup
- Belka ↔ Belka
- Krokiew ↔ Murłata
- Krokiew ↔ Kalenica
- Płatew ↔ Słup
- Belka ↔ Fundament

Biblioteka ma przewidywać:
czop i gniazdo, wrąb prosty, wrąb ukośny, zakładkę, połączenie krzyżowe, jaskółczy ogon, nakładkę, połączenie śrubowe, kołki i łączniki stalowe.

Po zaznaczeniu dwóch elementów JointEngine analizuje ich typy, położenie, kąt i przecięcie i pokazuje tylko geometrycznie sensowne połączenia.

## 17. Połączenia niedestrukcyjne
Połączenie nie może bezpowrotnie niszczyć bazowego TimberElement.
Zasada: TimberElement + Joint = geometria wynikowa.
Usunięcie Joint przywraca bazową geometrię.
Zmiana wymiarów elementu powinna powodować przeliczenie połączenia, jeśli jest to możliwe.

## 18. Automatyczne docinanie
Dla przecinających się elementów udostępnij „Dopasuj elementy”.
Oblicz geometrię przecięcia i dopasuj elementy poprzez parametryczną operację.
Każda operacja musi być odwracalna przez Cofnij.

## 19. Wymiary
Narzędzie WYMIAR: wybór dwóch punktów.
Obsługuj długość, wysokość, odległość i kąt.

## 20. Tryb 2D
Widoki: góra, przód, bok, wybrany przekrój.
Przełączanie 2D/3D powinno być szybkie.

## 21. Drzewo projektu
Struktura przykładowa:
Projekt → Dom → Parter → Ściany/Słupy → Strop/Belki → Dach/Krokwie/Płatwie/Murłaty.
Grupy można ukrywać.

## 22. Numerowanie
Automatyczne oznaczenia, np. B001, K001, S001. Użytkownik może zmienić oznaczenie ręcznie.

## 23. Zestawienie materiałów
Automatyczna tabela:
ID, typ, przekrój, długość, ilość, materiał.
Obliczaj też całkowitą długość, liczbę elementów i objętość drewna.
Aktualizuj po zmianie modelu.

## 24. Generator dachu
Kreator: wymiary budynku → typ dachu (dwuspadowy/jednospadowy/czterospadowy) → kąt → rozstaw krokwi → przekrój → podgląd → GENERUJ.
Generator ma korzystać z tego samego modelu TimberElement/Placement/Joint, a nie tworzyć osobnej logiki geometrii.

## 25. Generator ścian
Użytkownik rysuje linię i podaje wysokość, grubość, rozstaw oraz przekrój słupków. Program rozmieszcza elementy. Później: drzwi, okna, dodatkowe słupki.

## 26. Generator stropu
Użytkownik wskazuje obszar, kierunek belek, rozstaw, przekrój i materiał. Program generuje TimberElementy przez ten sam wspólny model danych.

## 27. Dokumentacja
Na podstawie modelu: rzuty, widoki, przekroje, wymiary, zestawienia. Docelowo PDF.

## 28. Zapis projektu i autosave
Projekt zapisuje geometrię, elementy, materiały, joints, constraints, wymiary, ustawienia i strukturę.
Autosave ma chronić przed utratą pracy.
Format danych powinien być wersjonowany, aby przyszłe wersje aplikacji mogły migrować stare projekty.

## 29. Undo / Redo
Każda mutacja modelu ma być komendą odwracalną: tworzenie, usuwanie, przesuwanie, obrót, kopiowanie, zmiana wymiarów, powielanie, połączenia i constraints.

## 30. UX
Każde narzędzie ma nazwę, prostą ikonę, tooltip i krótki opis kolejnego kroku.
Program zawsze informuje użytkownika, co zrobić dalej.
Nie twórz atrap przycisków bez działania, chyba że są jednoznacznie oznaczone jako planowane.

## 31. Menu kontekstowe
Prawy przycisk: Edytuj, Kopiuj, Przesuń, Obróć, Połącz, Ukryj, Usuń.
Menu zależy od rodzaju i liczby zaznaczonych elementów.

## 32. Wyszukiwanie funkcji
Wyszukiwarka poleceń, np. „krokiew” → Dodaj krokiew, Edytuj krokiew, Rozstaw krokwi, Generator dachu.

## 33. Skróty
Ctrl/Cmd+Z Cofnij; Ctrl/Cmd+Y lub Shift+Cmd+Z Ponów; Ctrl/Cmd+S Zapisz; Delete Usuń; ESC Anuluj.
Skróty nigdy nie są wymagane do obsługi.

## 34. Pierwsze uruchomienie
„Co chcesz zaprojektować?” → Dach / Wiata-Altana / Ściany szkieletowe / Strop / Pusty projekt.
Prowadź użytkownika krok po kroku.

## 35. Bezpieczeństwo obliczeń
Dopóki nie istnieje zweryfikowany moduł obliczeń, pokazuj:
„Model geometryczny — konstrukcja nie została zweryfikowana obliczeniowo.”
Nie przedstawiaj geometrii ani automatycznych połączeń jako potwierdzenia bezpieczeństwa konstrukcji.

## 36. Przyszłe moduły
Eurokod 5, statyka, śnieg, wiatr, ugięcie, nośność, wykrywanie błędów, zaawansowane połączenia, IFC, DXF/DWG, CNC, optymalizacja rozkroju, kosztorys, wizualizacja i współpraca wielu użytkowników.

## 37. Wydajność
Nie przebudowuj całego modelu po każdej zmianie. Aktualizuj tylko zmodyfikowane elementy i zależne joints/constraints.
Orbitowanie, przesuwanie, zaznaczanie i edycja mają pozostać płynne.

## 38. MVP — kolejność realizacji
Etap 1 — rdzeń:
ProjectModel → TimberElement → zapis/odczyt → CommandHistory.

Etap 2 — edytor 3D:
kamera → dodawanie → zaznaczanie wielu → przeciąganie → obrót → kopiowanie → usuwanie.

Etap 3 — precyzja:
Snap → Guides → dokładne odległości → wymiary → Array/Powiel.

Etap 4 — drewno:
przekroje → materiały → typy → numeracja → BOM.

Etap 5 — połączenia:
wybór 2 elementów → analiza relacji/przecięcia → biblioteka połączeń → Joint → rzeczywiste cięcie 3D.

Dopiero po stabilizacji powyższego:
Generator dachu → Generator ścian → Generator stropu → Dokumentacja → Eksport → Obliczenia.

## 39. Zasada pracy agenta
Przed większą funkcją:
1. określ cel,
2. zaprojektuj prosty UX,
3. określ strukturę danych,
4. zaimplementuj logikę,
5. podłącz UI,
6. dodaj obsługę błędów,
7. przetestuj,
8. sprawdź undo/redo,
9. sprawdź zapis/odczyt,
10. dopiero przejdź dalej.

Przed zmianą kodu sprawdzaj zgodność z tym plikiem. Gdy decyzja projektowa zmienia założenia produktu lub architektury, aktualizuj AGENT.MOD w tym samym etapie prac.

## 40. Aktualny najbliższy cel
SelectionManager — wdrożony etap 1:
- pojedyncze zaznaczenie,
- Shift/Ctrl/Cmd + klik dodaje lub usuwa element z zaznaczenia,
- dwa zaznaczone elementy tworzą parę A/B,
- czytelne podświetlenie,
- zaznaczenie wielokrotne jest przechowywane niezależnie od aktywnego elementu do edycji.

Następny etap:
zaznaczenie dwóch elementów → automatyczne rozpoznanie ich typów, położenia, kąta i przecięcia → lista właściwych połączeń ciesielskich → parametryczny Joint → rzeczywiste cięcie widoczne w 3D.

SelectionManager pozostaje do dalszego rozwinięcia o zaznaczanie prostokątem i operacje grupowe.


## 41. Generator konstrukcji z opisu — etap 1
Wdrożono pierwszy generator tekst → parametry → edytowalny model 3D dla wiaty.
- rozpoznaje zapis typu „7x6 m, 9 słupów”,
- rozpoznaje także słowa „szerokość”, „długość” i „słupy”,
- użytkownik podaje wysokość,
- 9 słupów jest rozmieszczane jako siatka 3 × 3,
- inne liczby słupów są rozkładane równomiernie po obwodzie,
- generator tworzy normalne elementy katalogowe, które można dalej zaznaczać, przesuwać i edytować,
- dodawane są cztery belki obwodowe,
- model jest oznaczony jako geometryczny, bez weryfikacji obliczeniowej.

Dalszy rozwój generatora:
typ dachu → spadek → krokwie/płatwie → edycja parametrów wygenerowanej wiaty → podgląd przed zatwierdzeniem → bardziej naturalne rozumienie polskich opisów.


## 42. Generator dachu z opisu — etap 2
Generator rozpoznaje dodatkowo:
- dach dwuspadowy,
- dach jednospadowy,
- kąt podany w stopniach,
- wysokość podaną w metrach lub milimetrach.

Dach jest generowany z osobnych edytowalnych elementów:
- dach dwuspadowy: kalenica + pary krokwi,
- dach jednospadowy: równoległe krokwie ze spadkiem,
- początkowy rozstaw krokwi geometrycznych około 800 mm.

Rozstaw i przekroje są na tym etapie parametrami modelu geometrycznego, a nie wynikiem obliczeń konstrukcyjnych.


## 43. Podgląd 3D na żywo z opisu — etap 3
Wprowadzono automatyczny podgląd graficzny podczas pisania opisu wiaty.
- parser uruchamia się automatycznie po krótkiej przerwie w pisaniu,
- po uzyskaniu kompletu poprawnych parametrów powstaje tymczasowy model 3D,
- zmiana tekstu zastępuje poprzedni podgląd zamiast dokładać kolejne konstrukcje,
- podgląd obejmuje słupy, belki obwodowe oraz dach jedno- lub dwuspadowy,
- zmiana wysokości aktualizuje podgląd,
- podgląd można wyłączyć,
- dopiero zatwierdzenie tworzy normalne edytowalne elementy projektu.

Następny kierunek: wizualne oznaczenie wymiarów na podglądzie, formularz rozpoznanych parametrów oraz aktualizacja zatwierdzonej konstrukcji bez jej dublowania.


## 44. Automatyczne węzły ciesielskie generatora — etap 4
Generator wiaty potrafi rozpoznać styki słupów z belkami obwodowymi.
- każdy słup i belka wygenerowana automatycznie otrzymuje metadane roli,
- styki słup–belka są zapisywane jako węzły typu `czop_gniazdo`,
- węzeł przechowuje indeks drugiego elementu i punkt połączenia XYZ,
- dane połączeń są zapisywane w stanie projektu,
- interfejs ma opcję „Automatyczne połączenia ciesielskie”,
- etap ten tworzy trwałą relację konstrukcyjną; fizyczne seryjne wycinanie wszystkich wykrytych węzłów będzie następnym krokiem.

Nie oznaczamy połączeń katalogowych jako wykonanych, dopóki nie istnieje rzeczywisty generator geometrii i kontrola kolizji.
