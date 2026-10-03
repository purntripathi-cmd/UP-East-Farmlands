"""
Purvanchal & UP East Regional Land Measurement Converter
Accurately maps between Western metric/imperial units (Acres, Hectares, Sq. Metres, Sq. Feet)
and regional East UP revenue measurements (Pakka Bigha, Kachha Bigha, Biswa, Kattha, Dhur).
"""

from typing import Dict, Any


# Standard conversion factors for Eastern UP / Purvanchal (Varanasi / Mirzapur / Jaunpur / Chandauli)
SQFT_PER_ACRE = 43560.0
SQMETRES_PER_ACRE = 4046.8564224
HECTARES_PER_ACRE = 0.40468564224

# 1 Pakka Bigha in Varanasi & Purvanchal = 27,225 sq.ft = 0.625 Acres (1 Acre = 1.60 Pakka Bigha)
ACRES_PER_PAKKA_BIGHA = 0.625
PAKKA_BIGHA_PER_ACRE = 1.60
BISWA_PER_PAKKA_BIGHA = 20.0
BISWA_PER_ACRE = 32.0

# Bihar Border (Buxar, Kaimur, Rohtas) Kattha system (32 Kattha per Acre, 20 Dhur per Kattha)
KATTHA_PER_ACRE = 32.0
DHUR_PER_KATTHA = 20.0

# Kachha Bigha (common in parts of Rohilkhand and fringe Bundelkhand, 1/3 of Pakka Bigha)
KACHHA_BIGHA_PER_ACRE = 4.80


class LandUnitConverter:
    """Provides high-precision calculations for regional Indian land parcels."""

    @staticmethod
    def calculate_all_units(acres: float) -> Dict[str, Any]:
        """Calculates exact regional equivalents for a given acreage."""
        acres = float(acres)
        pakka_bigha = acres * PAKKA_BIGHA_PER_ACRE
        biswa = pakka_bigha * BISWA_PER_PAKKA_BIGHA
        kachha_bigha = acres * KACHHA_BIGHA_PER_ACRE
        kattha = acres * KATTHA_PER_ACRE
        dhur = kattha * DHUR_PER_KATTHA
        hectares = acres * HECTARES_PER_ACRE
        sq_metres = acres * SQMETRES_PER_ACRE
        sq_feet = acres * SQFT_PER_ACRE

        return {
            "acres": round(acres, 3),
            "hectares": round(hectares, 3),
            "pakka_bigha": round(pakka_bigha, 2),
            "biswa": round(biswa, 1),
            "kachha_bigha": round(kachha_bigha, 2),
            "kattha": round(kattha, 1),
            "dhur": round(dhur, 1),
            "sq_metres": round(sq_metres, 1),
            "sq_feet": round(sq_feet, 1),
            "pakka_bigha_display": f"{pakka_bigha:.2f} Pakka Bigha ({biswa:.1f} Biswa)",
            "kattha_display": f"{kattha:.1f} Kattha ({dhur:.0f} Dhur)",
            "sq_metres_display": f"{sq_metres:,.1f} sq.m",
            "sq_feet_display": f"{sq_feet:,.0f} sq.ft",
            "summary_tag": f"{acres:.2f} Acres • {pakka_bigha:.2f} Bigha • {hectares:.2f} Ha"
        }

    @staticmethod
    def format_extent_string(acres: float) -> str:
        """Returns standard Purvanchal revenue ledger display format."""
        meta = LandUnitConverter.calculate_all_units(acres)
        return f"{acres:.2f} Acres ({meta['pakka_bigha_display']})"
