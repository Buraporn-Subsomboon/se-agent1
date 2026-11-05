"""Counting real tokens, pricing the run, and the settings that differ by provider."""
import json
import pytest
import prompt_router as pr
import cost_estimate as ce
from conftest import FakeModel, make_prompt, _resp


@pytest.fixture
def prompts_dir(tmp_path, monkeypatch):
    d = tmp_path / "prompts"; d.mkdir()
    (d / "Alpha.md").write_text(make_prompt("a"))
    monkeypatch.setattr(pr, "PROMPTS_DIR", d)
    monkeypatch.setattr(pr, "OUTPUT_DIR", tmp_path / "out")
    return d


class UsageModel(FakeModel):
    """Like FakeModel, but every reply reports real token counts."""
    def create(self, model, messages, **kw):
        reply = super().create(model, messages, **kw)
        reply.usage = type("U", (), {"prompt_tokens": 1000, "completion_tokens": 200, "total_tokens": 1200})
        return reply


def test_real_token_counts_are_recorded(monkeypatch):
    fake = UsageModel(); fake.script("DONE")
    monkeypatch.setattr(pr.client.chat, "completions", fake)
    pr.call_model("sys", "user")
    assert pr._calls == [{"input": 1000, "output": 200}]

def test_estimates_are_used_when_the_provider_gives_no_counts(model):
    pr.call_model("x" * 300, "y" * 300)          # FakeModel's reply has no usage
    call = pr._calls[0]
    assert call["input"] == 600 // pr.CHARS_PER_TOKEN and call["output"] > 0

def test_a_run_reports_totals_and_saves_usage_json(model, prompts_dir, monkeypatch):
    fake = UsageModel(); fake.script("1", "DONE")
    monkeypatch.setattr(pr.client.chat, "completions", fake)
    monkeypatch.setattr(pr.time, "sleep", lambda s: None)
    result = pr.run_router("A tiny app.")
    u = result["usage"]
    assert u["calls"] == 3 and u["input"] == 3000 and u["output"] == 600 and u["total"] == 3600
    saved = json.loads((result["run_dir"] / "usage.json").read_text())
    assert saved["total"] == 3600 and saved["model"] == pr.MODEL

def test_usage_is_counted_per_run_not_forever(model, prompts_dir, monkeypatch):
    fake = UsageModel(); fake.script("1", "DONE", "1", "DONE")
    monkeypatch.setattr(pr.client.chat, "completions", fake)
    monkeypatch.setattr(pr.time, "sleep", lambda s: None)
    pr.run_router("one"); second = pr.run_router("two")
    assert second["usage"]["calls"] == 3

def test_the_printed_report_names_profile_model_and_tokens(model, prompts_dir, capsys, monkeypatch):
    fake = UsageModel(); fake.script("1", "DONE")
    monkeypatch.setattr(pr.client.chat, "completions", fake)
    monkeypatch.setattr(pr.time, "sleep", lambda s: None)
    pr.run_router("A tiny app.")
    out = capsys.readouterr().out
    assert "TOKENS AND COST" in out and "3 model calls" in out and "3,600" in out


# ---- pricing ---------------------------------------------------------------------------
PRICES = {"as_of": "t", "models": {
    "groq-free (x)": {"input_per_m": 0, "output_per_m": 0},
    "big-model": {"input_per_m": 2.0, "output_per_m": 10.0},
    "blank": {"input_per_m": None, "output_per_m": None}}}
CALLS = [{"input": 500_000, "output": 100_000}, {"input": 500_000, "output": 100_000}]

def test_cost_of_a_run_uses_the_price_table():
    r = ce.run_cost(PRICES, CALLS, "big-model")
    assert r["total"] == 1_200_000 and r["dollars"] == pytest.approx(2.0 + 2.0)

def test_price_found_by_price_key_before_model_name():
    r = ce.run_cost(PRICES, CALLS, "anything", price_key="groq-free (x)")
    assert r["dollars"] == 0

def test_an_unknown_model_has_no_dollar_figure():
    assert ce.run_cost(PRICES, CALLS, "mystery")["dollars"] is None

def test_a_model_with_blank_prices_has_no_dollar_figure():
    assert ce.run_cost(PRICES, CALLS, "blank")["dollars"] is None


# ---- settings that differ by provider ---------------------------------------------------
def test_the_reply_limit_uses_the_providers_own_parameter_name(model, monkeypatch):
    monkeypatch.setitem(pr.PROFILE, "token_param", "max_completion_tokens")
    pr.call_model("s", "u", max_tokens=123)
    assert model.last_kwargs["max_completion_tokens"] == 123 and "max_tokens" not in model.last_kwargs

def test_the_default_reply_limit_comes_from_the_profile(model, monkeypatch):
    monkeypatch.setattr(pr, "REPLY_TOKENS", 777)
    pr.call_model("s", "u")
    assert model.last_kwargs["max_tokens"] == 777

def test_an_empty_reply_is_explained_not_passed_on(model):
    model.agent_reply = lambda n: "   "
    with pytest.raises(pr.ModelCallError, match="REPLY_TOKENS"):
        pr.call_model("You are a tester", "do it")

def test_pacing_is_off_when_the_profile_has_no_limit(model, monkeypatch):
    waits = []
    monkeypatch.setattr(pr.time, "sleep", lambda s: waits.append(s))
    monkeypatch.setattr(pr, "TPM_LIMIT", 0)
    for _ in range(5):
        pr.call_model("s" * 3000, "u" * 3000)
    assert waits == []


def test_each_call_announces_itself_and_reports_its_time(model, capsys):
    pr.call_model("s", "u")
    out = capsys.readouterr().out
    assert "[model] asking" in out and "[model] answered in" in out

def test_the_report_after_a_call_shows_real_token_counts(monkeypatch, capsys):
    fake = UsageModel(); fake.script("DONE")
    monkeypatch.setattr(pr.client.chat, "completions", fake)
    pr.call_model("s", "u")
    assert "1,000 in + 200 out" in capsys.readouterr().out


# ---- the spending guard: a run stops itself once it has used too much -----------------------

def _three_step_model(monkeypatch):
    fake = UsageModel(); fake.script("1", "1", "1", "DONE")
    monkeypatch.setattr(pr.client.chat, "completions", fake)
    monkeypatch.setattr(pr.time, "sleep", lambda s: None)
    return fake

def test_a_run_stops_at_the_token_cap_and_keeps_its_work(model, prompts_dir, monkeypatch, capsys):
    _three_step_model(monkeypatch)
    monkeypatch.setattr(pr, "MAX_RUN_TOKENS", 1500)         # first route + first agent = 2,400
    result = pr.run_router("A tiny app.")
    assert len(result["steps"]) == 1
    assert "Spending guard" in capsys.readouterr().out
    assert result["run_dir"] is not None                    # what finished is still saved

def test_a_run_stops_at_the_dollar_cap(model, prompts_dir, monkeypatch, tmp_path, capsys):
    _three_step_model(monkeypatch)
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps({"as_of": "x", "models": {
        pr.PROFILE["price_key"] or pr.MODEL: {"input_per_m": 1000, "output_per_m": 1000, "source": "t"}}}))
    monkeypatch.setattr(pr, "PRICES_FILE", prices)
    monkeypatch.setattr(pr, "MAX_COST_USD", 1.0)            # 2,400 tokens at $1000/M = $2.40
    result = pr.run_router("A tiny app.")
    assert len(result["steps"]) == 1
    assert "$1.00" in capsys.readouterr().out

def test_a_run_under_the_caps_is_not_interrupted(model, prompts_dir, monkeypatch):
    _three_step_model(monkeypatch)
    result = pr.run_router("A tiny app.")
    assert len(result["steps"]) == 3
