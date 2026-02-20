"""Tests for profile import/export helpers."""

from src.profile_io import (
    PROFILE_SCHEMA_VERSION,
    deserialize_profile,
    derive_simple_two_phase_from_legacy,
    serialize_profile,
    serialize_unified_bundle,
)


def test_serialize_profile_includes_meta_and_config():
    payload = serialize_profile(
        {
            "patrimonio_inicial": 100000,
            "aportacion_mensual": 1200,
            "fiscal_mode": "INTL_BASIC",
            "unknown_key": "ignore",
        }
    )
    assert payload["schema_version"] == PROFILE_SCHEMA_VERSION
    assert "created_at" in payload
    assert "config" in payload
    assert payload["config"]["patrimonio_inicial"] == 100000
    assert "unknown_key" not in payload["config"]


def test_deserialize_profile_filters_unknown_keys():
    config, warnings = deserialize_profile(
        {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "config": {
                "patrimonio_inicial": 200000,
                "bad_key": 123,
            },
        }
    )
    assert config["patrimonio_inicial"] == 200000
    assert "bad_key" not in config
    assert any("bad_key" in w for w in warnings)


def test_deserialize_profile_invalid_payload():
    config, warnings = deserialize_profile({"schema_version": PROFILE_SCHEMA_VERSION})
    assert config == {}
    assert warnings


def test_deserialize_profile_accepts_scenario_wrapper():
    payload = {
        "meta": {"model": "Monte Carlo (Normal)"},
        "params": {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "config": {
                "patrimonio_inicial": 123456,
                "edad_actual": 40,
            },
        },
        "summary": {"success_rate_final": 95.0},
    }
    config, warnings = deserialize_profile(payload)
    assert config["patrimonio_inicial"] == 123456
    assert config["edad_actual"] == 40
    assert any("escenario" in w.lower() for w in warnings)


def test_serialize_unified_bundle_includes_profile_and_legacy_mirrors():
    payload = serialize_unified_bundle(
        {"patrimonio_inicial": 321000, "edad_actual": 44},
        scenario_meta={"model": "Monte Carlo (Normal)"},
        scenario_summary={"success_rate_final": 88.8},
    )
    assert payload["kind"] == "FIRE_BUNDLE"
    assert payload["profile"]["config"]["patrimonio_inicial"] == 321000
    assert payload["config"]["patrimonio_inicial"] == 321000
    assert payload["params"]["config"]["edad_actual"] == 44
    assert payload["meta"]["model"] == "Monte Carlo (Normal)"
    assert payload["summary"]["success_rate_final"] == 88.8


def test_deserialize_profile_accepts_unified_bundle_profile_block():
    payload = {
        "kind": "FIRE_BUNDLE",
        "profile": {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "config": {
                "patrimonio_inicial": 555000,
                "edad_actual": 39,
            },
        },
    }
    config, warnings = deserialize_profile(payload)
    assert config["patrimonio_inicial"] == 555000
    assert config["edad_actual"] == 39
    assert any("unificado" in w.lower() for w in warnings)


def test_derive_simple_two_phase_from_legacy_uses_income_backfill():
    derived = derive_simple_two_phase_from_legacy(
        {
            "gastos_anuales": 25_000,
            "coste_pre_pension_anual": 2_000,
            "pension_publica_neta_anual_efectiva": 12_000,
            "plan_pensiones_privado_neto_anual": 3_000,
            "otras_rentas_post_jubilacion_netas": 1_000,
            "edad_inicio_pension_publica": 67,
            "edad_objetivo": 58,
            "edad_inicio_plan_privado": 70,
            "duracion_plan_privado_anos": 0,
        }
    )
    assert derived["two_phase_switch_age"] == 67
    assert derived["two_phase_withdrawal_stage1_net_annual"] == 27_000.0
    assert derived["two_phase_withdrawal_stage2_net_annual"] == 7_500.0
    assert derived["two_phase_post_pension_income_annual"] == 17_500.0


def test_derive_simple_two_phase_from_legacy_supports_pre_fire_private_plan():
    derived = derive_simple_two_phase_from_legacy(
        {
            "gastos_anuales": 20_000,
            "coste_pre_pension_anual": 0,
            "plan_pensiones_privado_neto_anual": 4_000,
            "duracion_plan_privado_anos": 5,
            "edad_inicio_plan_privado": 55,
            "edad_objetivo": 57,
            "edad_pension_oficial": 66,
        }
    )
    assert derived["two_phase_switch_age"] == 66
    assert derived["two_phase_withdrawal_stage1_net_annual"] == 16_000.0
    assert derived["two_phase_withdrawal_stage2_net_annual"] == 2_500.0
    assert derived["two_phase_post_pension_income_annual"] == 17_500.0


def test_derive_simple_two_phase_keeps_higher_post_income_when_available():
    derived = derive_simple_two_phase_from_legacy(
        {
            "gastos_anuales": 30_000,
            "pension_publica_neta_anual_efectiva": 22_000,
            "plan_pensiones_privado_neto_anual": 3_000,
            "otras_rentas_post_jubilacion_netas": 2_000,
            "edad_inicio_pension_publica": 67,
        }
    )
    assert derived["two_phase_post_pension_income_annual"] == 27_000.0
    assert derived["two_phase_withdrawal_stage2_net_annual"] == 3_000.0
