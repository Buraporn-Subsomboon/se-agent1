"""
providers.py -- which model the router uses, and what limits come with it.

PROFILE in your .env file picks the package. The course uses the default, openai.

    PROFILE   model runs on        key needed       notes
    openai    OpenAI (paid)        OPENAI_API_KEY   the course default; big context, no pacing
    groq      Groq (free tier)     GROQ_API_KEY     tiny limits (8,000 tokens/minute); for tinkering
    ollama    your own computer    (none)           small context, no rate limit
    custom    any OpenAI-style     see .env.example

Any number below can be overridden in .env (see OVERRIDES).

Spending guard: the router stops after any agent step once the run has cost MAX_COST_USD
(default $2.00) or used MAX_RUN_TOKENS tokens (default 1,000,000). Work finished before
the stop is still saved. Raise the limits in .env only when you mean to.
"""
import os

# tpm:          tokens per minute the provider allows (0 = do not pace)
# input_budget: most tokens to put into ONE request (earlier work is trimmed to fit)
# reply_tokens: longest reply we allow an agent to write
# router_reply: longest reply for the router's small JSON decision
# max_steps:    most agent runs in one workflow
# token_param:  what this provider calls the reply-length setting
PROFILES = {
    "openai": dict(api_base=None, key_env="OPENAI_API_KEY", model="gpt-6-luna", tpm=0,
                   input_budget=60000, reply_tokens=16000, router_reply=4000, max_steps=12,
                   token_param="max_completion_tokens", price_key=None,
                   max_cost=2.0, run_tokens=1_000_000),
    "groq": dict(api_base="https://api.groq.com/openai/v1", key_env="GROQ_API_KEY",
                 model="openai/gpt-oss-120b", tpm=8000, input_budget=7000, reply_tokens=4096,
                 router_reply=1000, max_steps=8, token_param="max_tokens", price_key="groq-free",
                 max_cost=2.0, run_tokens=1_000_000),
    "ollama": dict(api_base="http://localhost:11434/v1", key_env=None, model="gpt-oss:20b",
                   tpm=0, input_budget=6000, reply_tokens=4096, router_reply=1500,
                   max_steps=8, token_param="max_tokens", price_key="ollama-local",
                   max_cost=2.0, run_tokens=1_000_000),
    "custom": dict(api_base=None, key_env=None, model=None, tpm=0, input_budget=30000,
                   reply_tokens=8000, router_reply=2000, max_steps=10,
                   token_param="max_tokens", price_key=None,
                   max_cost=2.0, run_tokens=1_000_000),
}

# Settings in .env that replace a profile's number: ENV NAME -> profile field
OVERRIDES = {"MODEL": "model", "API_BASE": "api_base", "TPM_LIMIT": "tpm",
             "INPUT_TOKEN_BUDGET": "input_budget", "REPLY_TOKENS": "reply_tokens",
             "ROUTER_REPLY_TOKENS": "router_reply", "MAX_STEPS": "max_steps",
             "TOKEN_PARAM": "token_param", "PRICE_KEY": "price_key",
             "MAX_COST_USD": "max_cost", "MAX_RUN_TOKENS": "run_tokens"}
_NUMBERS = {"tpm", "input_budget", "reply_tokens", "router_reply", "max_steps", "run_tokens"}
_DECIMALS = {"max_cost"}


class SetupError(Exception):
    """Something is missing from the setup. The message says what to do."""


def get_profile(env=None):
    """Read PROFILE and any overrides from the environment and return the settings."""
    env = os.environ if env is None else env
    name = env.get("PROFILE", "openai").strip().lower()
    if name not in PROFILES:
        raise SetupError(f"PROFILE='{name}' is not one of: {', '.join(PROFILES)}.")
    p = dict(PROFILES[name], name=name)
    if name == "custom":
        p["key_env"] = env.get("API_KEY_ENV", "API_KEY")
    for env_name, field in OVERRIDES.items():
        value = env.get(env_name)
        if value not in (None, ""):
            if field in _NUMBERS:
                try:
                    value = int(value)
                except ValueError:
                    raise SetupError(f"{env_name} must be a whole number, not '{value}'.")
            elif field in _DECIMALS:
                try:
                    value = float(value)
                except ValueError:
                    raise SetupError(f"{env_name} must be a number like 2.00, not '{value}'.")
            p[field] = value
    if name == "custom" and not p["api_base"]:
        raise SetupError("PROFILE=custom needs API_BASE in your .env.")
    if not p["model"]:
        raise SetupError(f"PROFILE={name} needs MODEL (the model's name) in your .env.")
    p["api_key"] = env.get(p["key_env"]) if p["key_env"] else "not-needed"
    if not p["api_key"]:
        raise SetupError(f"No key found. Put {p['key_env']}=... in your .env file "
                         f"(same folder as prompt_router.py).")
    return p


def make_client(profile):
    """The client the router talks to. Imported here so tests that never call it stay light."""
    from openai import OpenAI
    # timeout: a reply from a thinking model can take minutes, but not forever. Without a limit a
# stalled connection would look exactly like a slow answer.
    return OpenAI(api_key=profile["api_key"], base_url=profile["api_base"], max_retries=2, timeout=300)
