"""Choosing where the model lives: plain dictionaries in, plain dictionaries out."""
import pytest
import providers as pv


def test_default_is_openai_with_a_cheap_model_and_a_spending_cap():
    p = pv.get_profile({"OPENAI_API_KEY": "k"})
    assert p["name"] == "openai" and p["model"] == "gpt-6-luna" and p["tpm"] == 0
    assert p["max_cost"] == 2.0 and p["run_tokens"] == 1_000_000

def test_spending_cap_can_be_changed_and_bad_values_are_explained():
    p = pv.get_profile({"OPENAI_API_KEY": "k", "MAX_COST_USD": "5.5", "MAX_RUN_TOKENS": "50000"})
    assert p["max_cost"] == 5.5 and p["run_tokens"] == 50000
    with pytest.raises(pv.SetupError, match="MAX_COST_USD"):
        pv.get_profile({"OPENAI_API_KEY": "k", "MAX_COST_USD": "lots"})

def test_groq_has_small_free_tier_limits():
    p = pv.get_profile({"PROFILE": "groq", "GROQ_API_KEY": "k"})
    assert p["name"] == "groq" and p["tpm"] == 8000 and p["input_budget"] == 7000
    assert p["token_param"] == "max_tokens" and p["model"] == "openai/gpt-oss-120b"

def test_missing_key_names_the_variable():
    with pytest.raises(pv.SetupError, match="OPENAI_API_KEY"):
        pv.get_profile({})

def test_paid_profiles_have_no_pacing_and_a_big_budget():
    for name, key in (("openai", "OPENAI_API_KEY"),):
        p = pv.get_profile({"PROFILE": name, key: "k", "MODEL": "m"})
        assert p["tpm"] == 0 and p["input_budget"] >= 30000 and p["max_steps"] > 8

def test_openai_uses_max_completion_tokens():
    p = pv.get_profile({"PROFILE": "openai", "OPENAI_API_KEY": "k", "MODEL": "m"})
    assert p["token_param"] == "max_completion_tokens"

def test_ollama_needs_no_key_and_has_a_small_budget():
    p = pv.get_profile({"PROFILE": "ollama"})
    assert p["tpm"] == 0 and "11434" in p["api_base"] and p["input_budget"] <= 8000

def test_custom_needs_a_base_url_and_reads_its_key():
    with pytest.raises(pv.SetupError, match="API_BASE"):
        pv.get_profile({"PROFILE": "custom", "MODEL": "m"})
    p = pv.get_profile({"PROFILE": "custom", "MODEL": "m", "API_BASE": "http://x/v1", "API_KEY": "k"})
    assert p["api_base"] == "http://x/v1" and p["api_key"] == "k"

def test_numbers_can_be_overridden():
    p = pv.get_profile({"PROFILE": "groq", "GROQ_API_KEY": "k", "TPM_LIMIT": "12000", "INPUT_TOKEN_BUDGET": "9000",
                        "MAX_STEPS": "5", "REPLY_TOKENS": "2000"})
    assert (p["tpm"], p["input_budget"], p["max_steps"], p["reply_tokens"]) == (12000, 9000, 5, 2000)

def test_a_non_number_override_is_explained():
    with pytest.raises(pv.SetupError, match="TPM_LIMIT"):
        pv.get_profile({"PROFILE": "groq", "GROQ_API_KEY": "k", "TPM_LIMIT": "lots"})

def test_unknown_profile_lists_the_choices():
    with pytest.raises(pv.SetupError, match="openai"):
        pv.get_profile({"PROFILE": "nope"})

def test_profile_name_ignores_case_and_spaces():
    assert pv.get_profile({"PROFILE": " Ollama "})["name"] == "ollama"

def test_every_profile_has_every_setting():
    needed = {"api_base", "key_env", "model", "tpm", "input_budget", "reply_tokens",
              "router_reply", "max_steps", "token_param", "price_key"}
    for name, p in pv.PROFILES.items():
        assert needed <= set(p), name

def test_the_client_can_be_built_without_calling_anything():
    client = pv.make_client(pv.get_profile({"OPENAI_API_KEY": "k"}))
    assert hasattr(client.chat, "completions")
