"""Regional tax engine for Spanish FIRE scenarios.

Loads versioned tax packs and computes annual tax drag:
- Savings tax (IRPF base del ahorro, common/foral)
- Wealth tax + ISGF (simplified annual approximation)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


TAXPACK_DIR = Path(__file__).resolve().parent.parent / "data" / "taxpacks"


REGION_LABELS = {
    "andalucia": "Andalucía",
    "aragon": "Aragón",
    "asturias": "Asturias",
    "illes-balears": "Illes Balears",
    "canarias": "Canarias",
    "cantabria": "Cantabria",
    "castilla-la-mancha": "Castilla-La Mancha",
    "castilla-y-leon": "Castilla y León",
    "cataluna": "Cataluña",
    "comunitat-valenciana": "Comunitat Valenciana",
    "extremadura": "Extremadura",
    "galicia": "Galicia",
    "madrid": "Madrid",
    "murcia": "Región de Murcia",
    "la-rioja": "La Rioja",
    "ceuta": "Ceuta",
    "melilla": "Melilla",
    "navarra": "Navarra",
    "pais-vasco-alava": "País Vasco (Álava)",
    "pais-vasco-bizkaia": "País Vasco (Bizkaia)",
    "pais-vasco-gipuzkoa": "País Vasco (Gipuzkoa)",
}


def list_available_taxpack_years(country: str = "es") -> List[int]:
    """List bundled tax pack years for the given country prefix."""
    years: List[int] = []
    prefix = f"{country.lower()}-"
    for path in TAXPACK_DIR.glob(f"{prefix}*.json"):
        stem = path.stem
        year_str = stem.replace(prefix, "")
        if year_str.isdigit():
            years.append(int(year_str))
    return sorted(set(years))


def load_tax_pack(year: int, country: str = "es") -> Dict:
    """Load a bundled tax pack (raises if missing)."""
    path = TAXPACK_DIR / f"{country.lower()}-{year}.json"
    if not path.exists():
        raise FileNotFoundError(f"Tax pack not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_region_options(tax_pack: Dict) -> List[Tuple[str, str]]:
    """Return sorted (region_key, display_label) options from tax pack."""
    regions = tax_pack.get("irpf", {}).get("general", {}).get("autonomousBracketsByRegion", {})
    options = []
    for key in regions.keys():
        options.append((key, REGION_LABELS.get(key, key)))
    options.sort(key=lambda x: x[1])
    return options


def _progressive_tax(base: float, brackets: List[Dict]) -> float:
    """Compute progressive tax for a taxable base and [{upTo, rate}] brackets."""
    taxable = max(0.0, base)
    lower = 0.0
    tax = 0.0
    for bracket in brackets:
        upper = bracket.get("upTo")
        rate = max(0.0, float(bracket.get("rate", 0.0)))
        if upper is None:
            tax += max(0.0, taxable - lower) * rate
            break
        span = max(0.0, min(taxable, float(upper)) - lower)
        tax += span * rate
        lower = float(upper)
        if taxable <= lower:
            break
    return max(0.0, tax)


def _progressive_tax_with_breakdown(base: float, brackets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute progressive tax plus line-by-line bracket trace."""
    taxable = max(0.0, float(base))
    lower = 0.0
    total_tax = 0.0
    lines: List[Dict[str, Any]] = []

    for idx, bracket in enumerate(brackets, start=1):
        upper = bracket.get("upTo")
        rate = max(0.0, float(bracket.get("rate", 0.0)))
        if upper is None:
            span = max(0.0, taxable - lower)
            quota = span * rate
            lines.append(
                {
                    "step": idx,
                    "lower": lower,
                    "upper": None,
                    "rate": rate,
                    "taxable_in_bracket": span,
                    "quota": quota,
                }
            )
            total_tax += quota
            break

        upper_f = float(upper)
        span = max(0.0, min(taxable, upper_f) - lower)
        quota = span * rate
        lines.append(
            {
                "step": idx,
                "lower": lower,
                "upper": upper_f,
                "rate": rate,
                "taxable_in_bracket": span,
                "quota": quota,
            }
        )
        total_tax += quota
        lower = upper_f
        if taxable <= lower:
            break

    return {
        "taxable_base": taxable,
        "lines": lines,
        "tax": max(0.0, total_tax),
    }


def calculate_savings_tax(savings_base: float, tax_pack: Dict, region: str) -> float:
    """Annual IRPF savings tax based on region (foral if available)."""
    savings_base = max(0.0, savings_base)
    foral = tax_pack.get("irpf", {}).get("foral", {})
    foral_brackets = foral.get("savingsBracketsByRegion", {}).get(region)
    if foral_brackets:
        return _progressive_tax(savings_base, foral_brackets)

    common_brackets = tax_pack.get("irpf", {}).get("savings", {}).get("brackets", [])
    return _progressive_tax(savings_base, common_brackets)


def calculate_savings_tax_with_details(savings_base: float, tax_pack: Dict, region: str) -> Dict[str, Any]:
    """Annual IRPF savings tax with bracket-level trace."""
    savings_base = max(0.0, savings_base)
    foral = tax_pack.get("irpf", {}).get("foral", {})
    foral_brackets = foral.get("savingsBracketsByRegion", {}).get(region)
    if foral_brackets:
        breakdown = _progressive_tax_with_breakdown(savings_base, foral_brackets)
        breakdown["system"] = "foral"
        breakdown["region"] = region
        return breakdown

    common_brackets = tax_pack.get("irpf", {}).get("savings", {}).get("brackets", [])
    breakdown = _progressive_tax_with_breakdown(savings_base, common_brackets)
    breakdown["system"] = "common"
    breakdown["region"] = region
    return breakdown


def calculate_wealth_taxes(investable_wealth: float, tax_pack: Dict, region: str) -> Dict[str, float]:
    """Approximate annual wealth taxes (IP + ISGF net of IP deduction).

    Note: this is an annual approximation on investable wealth only.
    """
    wealth = max(0.0, investable_wealth)
    wealth_pack = tax_pack.get("wealth", {})
    region_rules = wealth_pack.get("regions", {}).get(region)
    if not region_rules:
        return {"ip_tax": 0.0, "isgf_tax": 0.0, "total_wealth_tax": 0.0}

    ip_base = max(0.0, wealth - float(region_rules.get("minExempt", 0.0)))
    ip_tax = _progressive_tax(ip_base, region_rules.get("brackets", []))

    bonus = region_rules.get("bonus", {}) or {}
    if bonus.get("mode") == "fixedPct":
        pct = min(1.0, max(0.0, float(bonus.get("pct", 0.0))))
        ip_tax = ip_tax * (1.0 - pct)

    isgf = wealth_pack.get("isgf", {})
    threshold = float(isgf.get("threshold", 0.0))
    min_exempt = float(isgf.get("minExempt", 0.0))
    if wealth <= threshold:
        gross_isgf = 0.0
    else:
        isgf_base = max(0.0, wealth - min_exempt)
        gross_isgf = _progressive_tax(isgf_base, isgf.get("brackets", []))
    isgf_tax = max(0.0, gross_isgf - ip_tax)

    total = max(0.0, ip_tax + isgf_tax)
    return {
        "ip_tax": ip_tax,
        "isgf_tax": isgf_tax,
        "total_wealth_tax": total,
    }


def calculate_wealth_taxes_with_details(investable_wealth: float, tax_pack: Dict, region: str) -> Dict[str, Any]:
    """Approximate annual wealth taxes (IP + ISGF) with calculation trace."""
    wealth = max(0.0, investable_wealth)
    wealth_pack = tax_pack.get("wealth", {})
    region_rules = wealth_pack.get("regions", {}).get(region)
    if not region_rules:
        return {
            "region": region,
            "wealth": wealth,
            "ip_base": 0.0,
            "ip_breakdown": {"taxable_base": 0.0, "lines": [], "tax": 0.0},
            "ip_tax_before_bonus": 0.0,
            "ip_bonus_pct": 0.0,
            "ip_tax": 0.0,
            "isgf_base": 0.0,
            "isgf_breakdown": {"taxable_base": 0.0, "lines": [], "tax": 0.0},
            "isgf_tax_gross": 0.0,
            "isgf_tax_net": 0.0,
            "total_wealth_tax": 0.0,
        }

    ip_base = max(0.0, wealth - float(region_rules.get("minExempt", 0.0)))
    ip_breakdown = _progressive_tax_with_breakdown(ip_base, region_rules.get("brackets", []))
    ip_tax_before_bonus = ip_breakdown["tax"]

    bonus = region_rules.get("bonus", {}) or {}
    bonus_pct = 0.0
    if bonus.get("mode") == "fixedPct":
        bonus_pct = min(1.0, max(0.0, float(bonus.get("pct", 0.0))))
    ip_tax = ip_tax_before_bonus * (1.0 - bonus_pct)

    isgf = wealth_pack.get("isgf", {})
    threshold = float(isgf.get("threshold", 0.0))
    min_exempt = float(isgf.get("minExempt", 0.0))
    if wealth <= threshold:
        isgf_base = 0.0
        isgf_breakdown = {"taxable_base": 0.0, "lines": [], "tax": 0.0}
        gross_isgf = 0.0
    else:
        isgf_base = max(0.0, wealth - min_exempt)
        isgf_breakdown = _progressive_tax_with_breakdown(isgf_base, isgf.get("brackets", []))
        gross_isgf = isgf_breakdown["tax"]

    isgf_tax = max(0.0, gross_isgf - ip_tax)
    total = max(0.0, ip_tax + isgf_tax)
    return {
        "region": region,
        "wealth": wealth,
        "ip_base": ip_base,
        "ip_breakdown": ip_breakdown,
        "ip_tax_before_bonus": ip_tax_before_bonus,
        "ip_bonus_pct": bonus_pct,
        "ip_tax": ip_tax,
        "isgf_base": isgf_base,
        "isgf_breakdown": isgf_breakdown,
        "isgf_tax_gross": gross_isgf,
        "isgf_tax_net": isgf_tax,
        "total_wealth_tax": total,
    }


def validate_tax_pack_metadata(tax_pack: Dict[str, Any]) -> List[str]:
    """Return metadata validation errors for a tax pack."""
    errors: List[str] = []
    meta = tax_pack.get("meta", {})
    required_fields = ("country", "year", "version", "generatedAt", "lastReviewed", "sources")
    for field in required_fields:
        if field not in meta:
            errors.append(f"Missing meta.{field}")
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("meta.sources must be a non-empty list")
    return errors
