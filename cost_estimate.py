"""
cost_estimate.py -- how many tokens, and how many dollars, would a full se-agent run use?

It never calls a model. It reads your prompts and brief, adds up what each
step would send and what each reply would likely be, and prices the total
with the numbers in prices.json.

  python cost_estimate.py water-tracker.md                  estimate from prompts/ + the brief
  python cost_estimate.py water-tracker.md --prompts prompts
  python cost_estimate.py --measured-in 4297 --measured-out 5638     price a run you already measured

An estimate is a range, not a promise. The three scenarios show how much it
moves. Check your provider's usage page after a real run, and tell this
script the real numbers with --measured-in / --measured-out.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_PRICES = HERE / "prices.json"

CHARS_PER_TOKEN = 3.5      # plain English is ~4; code and tables are lower, so 3.5 is a middle guess
AGENT_REPLY_TOKENS = 3500  # a typical agent reply (the saved full-router run averaged about this)
ROUTER_REPLY_TOKENS = 100  # the router answers with one small JSON object
ROUTER_SYSTEM_CHARS = 900  # the router's fixed instructions
ROSTER_CHARS_PER_AGENT = 330
ROUTER_VIEW_CHARS = 2500   # how much of each earlier output the router reads
HANDOFF_OVERHEAD_CHARS = 400

# (name, steps the router takes, multiplier on reply size)
# The heavy case also stands in for "thinking" models, which bill hidden reasoning as output.
SCENARIOS = [("Light", 4, 0.8), ("Typical", 6, 1.0), ("Heavy", 8, 1.5)]


def tokens(chars, chars_per_token=CHARS_PER_TOKEN):
    return int(round(chars / chars_per_token))


def estimate(prompt_chars, brief_chars, steps, reply_tokens=AGENT_REPLY_TOKENS,
             chars_per_token=CHARS_PER_TOKEN):
    """Token estimate for one run.

    prompt_chars  list: the size in characters of each prompt file
    brief_chars   size of the project brief (it is sent with every call)
    steps         how many agent steps the router takes
    Returns {"rows": [...], "input": n, "output": n, "total": n}
    No trimming is assumed: a paid model with a big window gets all earlier work.
    """
    if not prompt_chars:
        raise ValueError("No prompts to estimate from.")
    avg_prompt = sum(prompt_chars) / len(prompt_chars)
    agent_system = avg_prompt + brief_chars
    roster = ROSTER_CHARS_PER_AGENT * len(prompt_chars)
    rows = []
    earlier = 0                                   # tokens of earlier agent output so far
    for step in range(1, steps + 1):
        router_chars = ROUTER_SYSTEM_CHARS + brief_chars + roster + HANDOFF_OVERHEAD_CHARS
        router_chars += (step - 1) * min(ROUTER_VIEW_CHARS, reply_tokens * chars_per_token)
        router_in = tokens(router_chars, chars_per_token)
        agent_in = tokens(agent_system + HANDOFF_OVERHEAD_CHARS, chars_per_token) + earlier
        rows.append({"step": step, "router_in": router_in, "router_out": ROUTER_REPLY_TOKENS,
                     "agent_in": agent_in, "agent_out": reply_tokens})
        earlier += reply_tokens
    # the router looks once more after the last step, to decide DONE
    final_chars = (ROUTER_SYSTEM_CHARS + brief_chars + roster + HANDOFF_OVERHEAD_CHARS
                   + steps * min(ROUTER_VIEW_CHARS, reply_tokens * chars_per_token))
    final_in = tokens(final_chars, chars_per_token)
    total_in = sum(r["router_in"] + r["agent_in"] for r in rows) + final_in
    total_out = sum(r["router_out"] + r["agent_out"] for r in rows) + ROUTER_REPLY_TOKENS
    return {"rows": rows, "final_router_in": final_in,
            "input": total_in, "output": total_out, "total": total_in + total_out}


def dollars(input_tokens, output_tokens, input_per_m, output_per_m):
    """Cost in dollars, or None if a price is missing. Prices are dollars per million tokens."""
    if input_per_m is None or output_per_m is None:
        return None
    return input_tokens / 1_000_000 * input_per_m + output_tokens / 1_000_000 * output_per_m


def load_prices(path=DEFAULT_PRICES):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "models" not in data:
        raise ValueError(f"{path} has no 'models' section.")
    return data


def find_price(prices, model, price_key=None):
    """The price entry for a model, or None. Looks for the profile's price_key, then the
    exact model name, then any entry whose name contains the model name (or the reverse)."""
    table = prices.get("models", {})
    for key in (price_key, model):
        if key and key in table:
            return table[key]
    low = (model or "").lower()
    for name, entry in table.items():
        n = name.lower()
        if low and (low in n or n.split(" ")[0] in low):
            return entry
    return None


def run_cost(prices, calls, model, price_key=None):
    """Totals for a real run. calls is a list of {"input": n, "output": n}.
    Returns {"calls", "input", "output", "total", "dollars"} where dollars is None if no price is known."""
    tin = sum(c["input"] for c in calls)
    tout = sum(c["output"] for c in calls)
    entry = find_price(prices, model, price_key)
    cost = dollars(tin, tout, entry.get("input_per_m"), entry.get("output_per_m")) if entry else None
    return {"calls": len(calls), "input": tin, "output": tout, "total": tin + tout, "dollars": cost}


def money(x):
    if x is None:
        return "set price"
    if x == 0:
        return "$0 (free)"
    return f"${x:,.2f}" if x >= 0.01 else f"${x:.4f}"


def read_inputs(brief_arg, prompts_dir):
    prompts = sorted(Path(prompts_dir).glob("*.md"))
    if not prompts:
        raise FileNotFoundError(f"No .md prompt files in {prompts_dir}")
    brief = ""
    if brief_arg:
        p = Path(brief_arg)
        brief = p.read_text(encoding="utf-8") if p.is_file() else brief_arg
    return [len(p.read_text(encoding="utf-8")) for p in prompts], len(brief.strip())


def report(prices, runs, title):
    """runs: [(label, input_tokens, output_tokens)] -> text table of dollars per model."""
    lines = [title, ""]
    head = f"{'Model':<30}" + "".join(f"{label:>16}" for label, _, _ in runs)
    lines += [head, "-" * len(head)]
    for name, p in prices["models"].items():
        cells = [money(dollars(i, o, p.get("input_per_m"), p.get("output_per_m")))
                 for _, i, o in runs]
        lines.append(f"{name:<30}" + "".join(f"{c:>16}" for c in cells))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Estimate the token use and cost of a full se-agent run.")
    ap.add_argument("brief", nargs="?", help="the project brief file (e.g. water-tracker.md)")
    ap.add_argument("--prompts", default=str(HERE / "prompts"), help="folder of prompt files")
    ap.add_argument("--prices", default=str(DEFAULT_PRICES), help="price table (prices.json)")
    ap.add_argument("--chars-per-token", type=float, default=CHARS_PER_TOKEN)
    ap.add_argument("--reply-tokens", type=int, default=AGENT_REPLY_TOKENS,
                    help="typical size of one agent reply, in tokens")
    ap.add_argument("--measured-in", type=int, help="input tokens from a real run")
    ap.add_argument("--measured-out", type=int, help="output tokens from a real run")
    args = ap.parse_args(argv)
    try:
        prices = load_prices(args.prices)
    except (OSError, ValueError) as e:
        sys.exit(f"Could not read the price table: {e}")

    if args.measured_in is not None or args.measured_out is not None:
        i, o = args.measured_in or 0, args.measured_out or 0
        print(report(prices, [("This run", i, o)],
                     f"Measured run: {i:,} in + {o:,} out = {i + o:,} tokens"))
        return 0

    try:
        prompt_chars, brief_chars = read_inputs(args.brief, args.prompts)
    except (OSError, FileNotFoundError) as e:
        sys.exit(str(e))
    print(f"Prompts: {len(prompt_chars)} files, about {tokens(sum(prompt_chars) / len(prompt_chars), args.chars_per_token):,} tokens each. "
          f"Brief: about {tokens(brief_chars, args.chars_per_token):,} tokens.\n")
    runs = []
    for label, steps, scale in SCENARIOS:
        est = estimate(prompt_chars, brief_chars, steps,
                       reply_tokens=int(args.reply_tokens * scale),
                       chars_per_token=args.chars_per_token)
        runs.append((f"{label} ({steps})", est["input"], est["output"]))
        print(f"{label:<8} {steps} steps: {est['input']:>8,} in + {est['output']:>7,} out = {est['total']:>8,} tokens"
              f"   (last step sends {est['rows'][-1]['agent_in']:,} in)")
    print()
    print(report(prices, runs, "Estimated cost of one full run"))
    print(f"\nPrices as of {prices.get('as_of', '?')}. Edit {Path(args.prices).name} to change them.")
    print("Models marked 'set price' have no price yet: copy it from the provider's pricing page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
