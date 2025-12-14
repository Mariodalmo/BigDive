from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Account:
    code: str
    name: str
    kind: str  # ASSET | LIABILITY | EQUITY | INCOME | EXPENSE


DEFAULT_CHART: list[Account] = [
    # Liquidità
    Account("1000", "Cassa", "ASSET"),
    Account("1010", "Banca", "ASSET"),

    # Crediti / Debiti
    Account("1100", "Crediti v/clienti", "ASSET"),
    Account("2000", "Debiti v/fornitori", "LIABILITY"),

    # IVA
    Account("2100", "IVA a debito", "LIABILITY"),
    Account("1200", "IVA a credito", "ASSET"),

    # Immobilizzazioni / Investimenti
    Account("1300", "Immobilizzazioni materiali", "ASSET"),
    Account("1310", "Immobilizzazioni immateriali", "ASSET"),

    # Patrimonio netto
    Account("3000", "Capitale sociale", "EQUITY"),
    Account("3100", "Utile (perdita) d'esercizio", "EQUITY"),

    # Ricavi
    Account("4000", "Ricavi vendite/servizi", "INCOME"),
    Account("4100", "Altri ricavi", "INCOME"),

    # Costi
    Account("5000", "Acquisti merci", "EXPENSE"),
    Account("5100", "Servizi", "EXPENSE"),
    Account("5200", "Affitti", "EXPENSE"),
    Account("5300", "Utenze", "EXPENSE"),
    Account("5400", "Personale", "EXPENSE"),
    Account("5500", "Ammortamenti", "EXPENSE"),
    Account("5600", "Imposte e tasse", "EXPENSE"),
]
