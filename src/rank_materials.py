import pandas as pd


def normalize(series, higher_is_better=True):
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return series * 0 + 1

    normalized = (series - min_val) / (max_val - min_val)

    if higher_is_better:
        return normalized
    else:
        return 1 - normalized


def score_materials(df):
    df = df.copy()

    df["stability_score"] = normalize(df["energy_above_hull"], higher_is_better=False)
    df["voltage_score"] = normalize(df["voltage"], higher_is_better=True)
    df["capacity_score"] = normalize(df["capacity"], higher_is_better=True)
    df["risk_score"] = normalize(df["supply_risk"], higher_is_better=False)

    df["final_score"] = (
        0.30 * df["stability_score"]
        + 0.25 * df["voltage_score"]
        + 0.25 * df["capacity_score"]
        + 0.10 * df["cost_score"]
        + 0.10 * df["risk_score"]
    )

    return df.sort_values("final_score", ascending=False)


def explain_material(row):
    reasons = []

    if row["stability_score"] > 0.7:
        reasons.append("strong stability")
    if row["voltage_score"] > 0.7:
        reasons.append("high voltage")
    if row["capacity_score"] > 0.7:
        reasons.append("high capacity")
    if row["cost_score"] > 0.7:
        reasons.append("good cost practicality")
    if row["risk_score"] > 0.7:
        reasons.append("low supply risk")

    if not reasons:
        reasons.append("balanced but not outstanding properties")

    return ", ".join(reasons)


def main():
    df = pd.read_csv("data/cathode_candidates.csv")
    ranked = score_materials(df)

    ranked["explanation"] = ranked.apply(explain_material, axis=1)

    print(ranked[["formula", "final_score", "explanation"]])

    ranked.to_csv("data/ranked_cathode_candidates.csv", index=False)


if __name__ == "__main__":
    main()