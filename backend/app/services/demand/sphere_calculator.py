"""
RELIEFOS Lite — Humanitarian Demand & Sphere Standards Calculation Service
Implements internationally accepted Sphere Minimum Standards for Humanitarian Disaster Response:
- Nutrition: 2,100 kcal / person / day (~0.45 kg dry food rations: fortified cereal, pulses, edible oil, salt)
- Water, Sanitation & Hygiene (WASH): 15.0 Litres / person / day potable water for drinking, cooking & hygiene
- Emergency Shelter: 1 heavy-duty family tarpaulin kit (HDPE reinforced 4x5m) per 5 persons
- Sanitation & Hygiene Packs: 1 family pack (soap, chlorine purification tablets, sanitary pads) per 5 persons
- Multi-horizon supply requirements: 24 Hours (Immediate), 72 Hours (Surge Wave), 7 Days (Sustenance)

Distinguishes between:
1. MEASURED_DEMAND: Derived from verified headcounts of registered evacuees in designated relief camps.
2. ESTIMATED_DEMAND: Derived from GIS inundation extent multiplied by census population exposure models.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math


# Sphere Minimum Standards Constants
SPHERE_KCAL_PER_PERSON_DAY = 2100
SPHERE_FOOD_KG_PER_PERSON_DAY = 0.45      # Balanced dry composite ration (Rice 350g, Dal 60g, Oil 25g, Salt 15g)
SPHERE_WATER_LITERS_PER_PERSON_DAY = 15.0  # 3L survival drinking + 4L food preparation + 8L personal hygiene
PERSONS_PER_FAMILY_UNIT = 5
TARPAULIN_KIT_PER_FAMILY = 1.0
HYGIENE_KIT_PER_FAMILY = 1.0


def calculate_sphere_humanitarian_demand(
    population_affected: int,
    evacuees_in_shelters: int,
    time_horizon_hours: int = 72,
    infant_count: int = 0,
    elderly_count: int = 0,
    contingency_buffer_pct: float = 15.0,
    location_id: str = "kamrup_metro"
) -> Dict[str, Any]:
    """
    Computes rigorous Sphere-standard humanitarian relief requirements with multi-horizon projections.
    """
    days = max(1.0, time_horizon_hours / 24.0)
    buffer_multiplier = 1.0 + (max(0.0, contingency_buffer_pct) / 100.0)

    # 1. Measured Shelter Population Requirements (Primary verified priority)
    measured_pop = max(0, evacuees_in_shelters)
    measured_food_kg = round(measured_pop * SPHERE_FOOD_KG_PER_PERSON_DAY * days * buffer_multiplier, 1)
    measured_water_l = round(measured_pop * SPHERE_WATER_LITERS_PER_PERSON_DAY * days * buffer_multiplier, 1)
    measured_families = math.ceil(measured_pop / PERSONS_PER_FAMILY_UNIT) if measured_pop > 0 else 0
    measured_tarpaulins = measured_families
    measured_hygiene_kits = measured_families

    # 2. Estimated Surrounding Community Demand (Unsheltered or isolated clusters)
    unsheltered_pop = max(0, population_affected - evacuees_in_shelters)
    estimated_food_kg = round(unsheltered_pop * SPHERE_FOOD_KG_PER_PERSON_DAY * days * buffer_multiplier, 1)
    estimated_water_l = round(unsheltered_pop * SPHERE_WATER_LITERS_PER_PERSON_DAY * days * buffer_multiplier, 1)
    estimated_families = math.ceil(unsheltered_pop / PERSONS_PER_FAMILY_UNIT) if unsheltered_pop > 0 else 0

    # Total combined requirements
    total_food_kg = round(measured_food_kg + estimated_food_kg, 1)
    total_water_l = round(measured_water_l + estimated_water_l, 1)
    total_tarpaulins = measured_tarpaulins + estimated_families
    total_hygiene_packs = measured_hygiene_kits + estimated_families

    # Specialized baby food / oral rehydration salts (ORS) requirement
    ors_sachets_count = (infant_count * 2 + elderly_count * 1) * int(days)
    baby_cereal_kg = round(infant_count * 0.15 * days, 1)

    return {
        "calculation_timestamp": datetime.now(timezone.utc).isoformat(),
        "standard_reference": "The Sphere Handbook: Humanitarian Charter & Minimum Standards (2018 Edition)",
        "location_id": location_id,
        "input_parameters": {
            "population_affected_total": population_affected,
            "evacuees_verified_in_shelters": evacuees_in_shelters,
            "unsheltered_isolated_estimate": unsheltered_pop,
            "planning_horizon_hours": time_horizon_hours,
            "planning_horizon_days": round(days, 2),
            "contingency_buffer_pct": contingency_buffer_pct,
            "demographic_vulnerability": {
                "infants_under_5": infant_count,
                "elderly_above_65": elderly_count
            }
        },
        "sphere_per_capita_baselines": {
            "food_energy_kcal_per_person_day": SPHERE_KCAL_PER_PERSON_DAY,
            "food_dry_rations_kg_per_person_day": SPHERE_FOOD_KG_PER_PERSON_DAY,
            "potable_water_liters_per_person_day": SPHERE_WATER_LITERS_PER_PERSON_DAY,
            "ration_breakdown": {
                "fortified_rice_or_flour_g": 350,
                "pulses_dal_g": 60,
                "fortified_edible_oil_g": 25,
                "iodized_salt_g": 15
            }
        },
        "measured_shelter_demand": {
            "category": "VERIFIED_SHELTER_EVACUEES",
            "evacuee_headcount": measured_pop,
            "food_rations_kg": measured_food_kg,
            "potable_water_liters": measured_water_l,
            "emergency_tarpaulins_units": measured_tarpaulins,
            "family_hygiene_packs": measured_hygiene_kits,
            "confidence_level": "HIGH (Registered Shelter Registry)"
        },
        "estimated_unregistered_demand": {
            "category": "ESTIMATED_INUNDATED_ZONE_POPULATION",
            "estimated_headcount": unsheltered_pop,
            "food_rations_kg": estimated_food_kg,
            "potable_water_liters": estimated_water_l,
            "emergency_tarpaulins_units": estimated_families,
            "family_hygiene_packs": estimated_families,
            "confidence_level": "MODERATE (Derived from Census Density * Flood Polygon)"
        },
        "consolidated_humanitarian_requirement": {
            "total_beneficiaries": population_affected,
            "food_rations_total_kg": total_food_kg,
            "potable_water_total_liters": total_water_l,
            "water_storage_20L_jerrycans_needed": math.ceil(total_water_l / 20.0),
            "emergency_tarpaulins_units": total_tarpaulins,
            "family_hygiene_packs": total_hygiene_packs,
            "specialized_medical_nutrition": {
                "ors_rehydration_sachets": ors_sachets_count,
                "baby_cereal_kg": baby_cereal_kg
            }
        },
        "horizon_breakdown": {
            "24_hours_immediate_kg": round(total_food_kg / days, 1),
            "72_hours_surge_kg": round((total_food_kg / days) * 3.0, 1),
            "7_days_sustenance_kg": round((total_food_kg / days) * 7.0, 1)
        },
        "uncertainty_and_governance_notice": (
            "Sphere calculations serve as empirical statutory baseline guidelines under ASDMA relief codes. "
            "Actual distribution manifests require Field Verification Form 3 validation prior to physical rollout."
        )
    }
