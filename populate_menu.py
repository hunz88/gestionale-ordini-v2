#!/usr/bin/env python3
from backend.server import app, db, Voce

menu = [
    # TOAST
    ("TOAST", "Classico", 5.00),
    ("TOAST", "Parma", 6.50),
    ("TOAST", "Trentino", 6.00),
    ("TOAST", "Onto", 6.50),
    ("TOAST", "Pork", 6.50),

    # SALSE EXTRA
    ("SALSE EXTRA", "Salse extra", 0.50),
    ("SALSE EXTRA", "Aggiunte",   0.50),

    # BRUSCHETTE
    ("BRUSCHETTE", "Piaggio",     6.00),
    ("BRUSCHETTE", "Yamaha",      6.50),
    ("BRUSCHETTE", "KTM",         6.50),
    ("BRUSCHETTE", "Moto Guzzi",  6.50),
    ("BRUSCHETTE", "MV Augusta",  7.00),
    ("BRUSCHETTE", "Lavarda",     6.50),
    ("BRUSCHETTE", "Suzuki",      7.00),
    ("BRUSCHETTE", "Vespa",       6.50),

    # PANINI A PANE MORBIDO
    ("PANINI A PANE MORBIDO", "Procu",         7.50),
    ("PANINI A PANE MORBIDO", "Altopiano",     7.50),
    ("PANINI A PANE MORBIDO", "Crudo Parma",   8.00),
    ("PANINI A PANE MORBIDO", "Golosone",      7.50),
    ("PANINI A PANE MORBIDO", "Veneto",        8.50),
    ("PANINI A PANE MORBIDO", "F.D.C.",        9.50),

    # BURGER & SPECIALITÀ CALDE
    ("BURGER & SPECIALITA CALDE", "Boston Burger",         12.00),
    ("BURGER & SPECIALITA CALDE", "Big Boston Burger",     15.00),
    ("BURGER & SPECIALITA CALDE", "AC/DC",                 14.00),
    ("BURGER & SPECIALITA CALDE", "Rhapsody",              13.00),
    ("BURGER & SPECIALITA CALDE", "Pulled Pork Sandwich",  11.00),
    ("BURGER & SPECIALITA CALDE", "Chili Dog",             10.00),
    ("BURGER & SPECIALITA CALDE", "Wacken (Veg)",          12.00),

    # PIADINE ARTIGIANALI
    ("PIADINE ARTIGIANALI", "Walk",                          6.00),
    ("PIADINE ARTIGIANALI", "Born",                          6.00),
    ("PIADINE ARTIGIANALI", "Alias",                         6.50),
    ("PIADINE ARTIGIANALI", "Wrong",                         6.50),
    ("PIADINE ARTIGIANALI", "Fire",                          6.50),
    ("PIADINE ARTIGIANALI", "Kebit",                         7.00),

    # CAFFETTERIA
    ("CAFFETTERIA", "Caffè espresso",                        1.30),
    ("CAFFETTERIA", "Caffè corretto",                        1.70),
    ("CAFFETTERIA", "Caffè corretto + rasentino",            2.10),
    ("CAFFETTERIA", "Caffè decaffeinato",                    1.40),
    ("CAFFETTERIA", "Caffè decaffeinato macchiato",          1.50),
    ("CAFFETTERIA", "Caffè d'orzo",                          1.50),
    ("CAFFETTERIA", "Caffè ginseng",                         1.50),
    ("CAFFETTERIA", "Caffè shakerato",                       2.00),
    ("CAFFETTERIA", "Caffè americano",                       1.50),
    ("CAFFETTERIA", "Caffè macchiato",                       1.40),
    ("CAFFETTERIA", "Caffè ginseng macchiato",               1.60),
    ("CAFFETTERIA", "Caffè d'orzo macchiato",                1.60),
    ("CAFFETTERIA", "Macchiatone",                           1.60),
    ("CAFFETTERIA", "Macchiatone decaffeinato",              1.70),
    ("CAFFETTERIA", "Macchiatone d'orzo",                    1.70),
    ("CAFFETTERIA", "Macchiatone ginseng",                   1.70),
    ("CAFFETTERIA", "Cappuccino",                            1.70),
    ("CAFFETTERIA", "Cappuccino decaffeinato",               1.80),
    ("CAFFETTERIA", "Cappuccino d'orzo",                     1.80),
    ("CAFFETTERIA", "Cappuccino ginseng",                    1.80),
    ("CAFFETTERIA", "Latte macchiato",                       2.00),
    ("CAFFETTERIA", "Latte e menta",                         2.00),
    ("CAFFETTERIA", "Latte e cacao",                         1.80),
    ("CAFFETTERIA", "Brioches",                              1.50),
    ("CAFFETTERIA", "Cioccolata calda",                      2.50),
    ("CAFFETTERIA", "Cioccolata calda con panna",            3.00),
    ("CAFFETTERIA", "Tè caldo",                              2.30),
    ("CAFFETTERIA", "Infusi",                                2.30),

    # BEVANDE ANALCOLICHE
    ("BEVANDE ANALCOLICHE", "Acqua 0,5 l",                  1.20),
    ("BEVANDE ANALCOLICHE", "Acqua 1 l",                    2.50),
    ("BEVANDE ANALCOLICHE", "Acqua con sciroppo (piccola)", 2.00),
    ("BEVANDE ANALCOLICHE", "Acqua con sciroppo (grande)",  2.50),
    ("BEVANDE ANALCOLICHE", "Lattina 33 cl",                2.50),
    ("BEVANDE ANALCOLICHE", "Lattina 25 cl",                2.50),
    ("BEVANDE ANALCOLICHE", "Bibita alla spina 30 cl",      2.50),
    ("BEVANDE ANALCOLICHE", "Bibita alla spina 40 cl",      4.00),
    ("BEVANDE ANALCOLICHE", "Succo di frutta (sfuso)",      2.00),
    ("BEVANDE ANALCOLICHE", "Gingerino / Crodino",          2.50),
    ("BEVANDE ANALCOLICHE", "Red Bull",                     3.00),
    ("BEVANDE ANALCOLICHE", "Bevande energetiche",          3.50),

    # BIRRE & SPRITZ
    ("BIRRE & SPRITZ", "Birra bionda piccola 20 cl",        3.00),
    ("BIRRE & SPRITZ", "Birra bionda media 40 cl",          5.00),
    ("BIRRE & SPRITZ", "Birra speciale piccola 25 cl",      3.50),
    ("BIRRE & SPRITZ", "Birra speciale media 40 cl",        6.00),
    ("BIRRE & SPRITZ", "Birra in bottiglia 33 cl",          4.50),
    ("BIRRE & SPRITZ", "Birra in lattina 33-55 cl",         4.50),
    ("BIRRE & SPRITZ", "Spritz Aperol",                     2.80),
    ("BIRRE & SPRITZ", "Spritz Campari",                    3.50),
    ("BIRRE & SPRITZ", "Spritz Mezzo e Mezzo",              3.50),
    ("BIRRE & SPRITZ", "Spritz piccoli",                    1.50),
    ("BIRRE & SPRITZ", "Spritz piccoli (acqua & liquore)",  1.30),
    ("BIRRE & SPRITZ", "Vino b/r piccolo (bianco o rosso)", 1.50),

    # AMARI & GRAPPE
    ("AMARI & GRAPPE", "Linea Poli classica",               3.00),
    ("AMARI & GRAPPE", "Linea Poli pregiata",               5.00),
    ("AMARI & GRAPPE", "Amari classici",                    3.00),
    ("AMARI & GRAPPE", "Amari pregiati",                    5.25),
]

with app.app_context():
    # Ricrea da zero il DB (drop+create)
    db.drop_all()
    db.create_all()
    # Inserisci tutte le voci
    for gruppo, nome, prezzo in menu:
        db.session.add(Voce(gruppo=gruppo, nome=nome, prezzo=prezzo))
    db.session.commit()
    print(f"🌅 SUNSET BAR - Inserite {len(menu)} voci nel database.")
