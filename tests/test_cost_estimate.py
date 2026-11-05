"""Tests for cost_estimate.py: pure arithmetic, no network, no key."""
import json
import pytest
import cost_estimate as ce


def test_dollars_uses_price_per_million():
    assert ce.dollars(1_000_000, 0, 2.0, 10.0) == pytest.approx(2.0)
    assert ce.dollars(0, 1_000_000, 2.0, 10.0) == pytest.approx(10.0)
    assert ce.dollars(500_000, 250_000, 2.0, 10.0) == pytest.approx(3.5)

def test_dollars_is_none_when_a_price_is_missing():
    assert ce.dollars(1000, 1000, None, 10.0) is None
    assert ce.dollars(1000, 1000, 2.0, None) is None

def test_free_models_cost_zero():
    assert ce.dollars(9999, 9999, 0, 0) == 0

def test_input_grows_with_every_step():
    est = ce.estimate([10000, 12000], 900, steps=5)
    agent_in = [r["agent_in"] for r in est["rows"]]
    assert agent_in == sorted(agent_in) and len(set(agent_in)) == 5

def test_growth_per_step_equals_one_reply():
    est = ce.estimate([10000], 900, steps=3, reply_tokens=2000)
    rows = est["rows"]
    assert rows[1]["agent_in"] - rows[0]["agent_in"] == 2000

def test_totals_add_up():
    est = ce.estimate([10000, 12000, 9000], 900, steps=4)
    ins = sum(r["router_in"] + r["agent_in"] for r in est["rows"]) + est["final_router_in"]
    outs = sum(r["router_out"] + r["agent_out"] for r in est["rows"]) + ce.ROUTER_REPLY_TOKENS
    assert (est["input"], est["output"]) == (ins, outs)
    assert est["total"] == ins + outs

def test_more_steps_cost_more():
    small = ce.estimate([10000], 900, steps=3)["total"]
    big = ce.estimate([10000], 900, steps=8)["total"]
    assert big > small

def test_a_longer_brief_means_more_input():
    short = ce.estimate([10000], 500, steps=3)["input"]
    long_ = ce.estimate([10000], 3000, steps=3)["input"]
    assert long_ > short

def test_bigger_replies_cost_more_both_ways():
    a = ce.estimate([10000], 900, steps=4, reply_tokens=1000)
    b = ce.estimate([10000], 900, steps=4, reply_tokens=4000)
    assert b["output"] > a["output"] and b["input"] > a["input"]

def test_no_prompts_is_an_error():
    with pytest.raises(ValueError):
        ce.estimate([], 900, steps=3)

def test_money_formatting():
    assert ce.money(None) == "set price"
    assert ce.money(0) == "$0 (free)"
    assert ce.money(1.234) == "$1.23"
    assert ce.money(0.0042) == "$0.0042"

def test_price_file_is_valid_and_has_free_options():
    prices = ce.load_prices(ce.DEFAULT_PRICES)
    assert prices["models"]["ollama-local"]["input_per_m"] == 0
    assert prices["models"]["gpt-6-luna"]["input_per_m"] > 0     # the course's default model is priced
    for p in prices["models"].values():
        assert set(p) >= {"input_per_m", "output_per_m", "source"}

def test_missing_models_section_is_reported(tmp_path):
    bad = tmp_path / "p.json"
    bad.write_text(json.dumps({"as_of": "x"}))
    with pytest.raises(ValueError):
        ce.load_prices(bad)

def test_cli_with_real_files(tmp_path, capsys):
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "a.md").write_text("x" * 9000)
    (tmp_path / "prompts" / "b.md").write_text("y" * 12000)
    brief = tmp_path / "brief.md"; brief.write_text("z" * 900)
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps({"as_of": "t", "models": {
        "paid": {"input_per_m": 2, "output_per_m": 10, "source": "s"},
        "blank": {"input_per_m": None, "output_per_m": None, "source": "s"}}}))
    code = ce.main([str(brief), "--prompts", str(tmp_path / "prompts"), "--prices", str(prices)])
    out = capsys.readouterr().out
    assert code == 0
    assert "Light" in out and "Typical" in out and "Heavy" in out
    assert "set price" in out and "$" in out

def test_cli_measured_mode(tmp_path, capsys):
    prices = tmp_path / "p.json"
    prices.write_text(json.dumps({"as_of": "t", "models": {
        "paid": {"input_per_m": 1.0, "output_per_m": 2.0, "source": "s"}}}))
    ce.main(["--measured-in", "1000000", "--measured-out", "1000000", "--prices", str(prices)])
    assert "$3.00" in capsys.readouterr().out

def test_cli_exits_cleanly_with_no_prompts(tmp_path):
    prices = tmp_path / "p.json"
    prices.write_text(json.dumps({"as_of": "t", "models": {}}))
    (tmp_path / "empty").mkdir()
    with pytest.raises(SystemExit):
        ce.main(["--prompts", str(tmp_path / "empty"), "--prices", str(prices)])
