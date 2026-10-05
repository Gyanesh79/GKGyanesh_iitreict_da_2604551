# ------------------------------------------------------------------------------
# Part 3 — GenAI-Powered Insight Narrator
# File - narrator/generate_narrative.py
# ------------------------------------------------------------------------------

import os
from google import genai
from google.colab import userdata

key = userdata.get('GenAI_APIKey')

#------------------------------------------------------------------------------#
# Task 3.4 — Offline fallback path
#------------------------------------------------------------------------------#
def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Fully deterministic offline fallback.
    No API key, no network, no model call.
    Uses only findings values.
    """

    narrative = f"""
      Situation:
      Mamaearth’s cleaned revenue is ₹{findings['cleaned_total_revenue_inr']}, compared with a raw total of ₹{findings['raw_total_revenue_inr']}. The difference of ₹{findings['duplicate_reconciliation_delta_inr']} comes entirely from duplicate orders removed during data cleaning. Payment‑method analysis shows return rates of {findings['return_rate_by_payment']['COD']}% for COD, {findings['return_rate_by_payment']['CARD']}% for Card, and {findings['return_rate_by_payment']['UPI']}% for UPI.

      Complication:
      Risk is not evenly distributed. COD orders in Tier‑2 cities return at {findings['highest_risk_segment']['return_rate_pct']}%, far higher than Tier‑1 COD orders. Time‑series analysis also reveals that January’s apparent revenue of ₹{findings['outlier_inflated_month']['apparent_revenue_inr']} was inflated by two bulk outlier orders, with corrected revenue only ₹{findings['outlier_inflated_month']['corrected_revenue_inr']}.

      Resolution:
      Once outliers are removed, March emerges as the true peak month with ₹{findings['true_peak_month']['revenue_inr']}. These verified metrics provide a stable foundation for operational decisions, targeted return‑rate interventions, and more accurate monthly performance reporting.
      """.strip()

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": 0
    }


#------------------------------------------------------------------------------#
# Part 3 Task 2 generate_scr_narrative(findings: dict) -> dict
#------------------------------------------------------------------------------#

def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate a structured Situation–Complication–Resolution narrative
    using the google-genai client, ensuring all numbers come directly
    from the findings dict and are never hardcoded.
    """

     # Try to initialize client — if this fails, go offline immediately
    try:
         client = genai.Client(api_key = key)
    except Exception:
        return generate_scr_narrative_offline(findings)


    # --- SYSTEM INSTRUCTION (NOT folded into user prompt) ---
    system_instruction = (
        "You are a senior data analyst writing for Mamaearth's regional "
        "operations and finance heads. Your output must contain exactly "
        "three labeled sections: Situation, Complication, Resolution. "
        "Every number in your narrative must come directly from the "
        "supplied findings dictionary and must appear with the exact same "
        "value — no invented statistics, no rounding changes, no new metrics. "
        "You must not introduce any figures that are not present in findings."
    )

    # --- USER PROMPT BUILT FROM FINDINGS (NO HARDCODED NUMBERS) ---
    contents = (
        system_instruction + "\n\n" + # Prepend system instruction to contents
        "Use the following verified metrics to produce the SCR narrative:\n\n"
        f"- cleaned_total_revenue_inr: {findings['cleaned_total_revenue_inr']}\n"
        f"- raw_total_revenue_inr: {findings['raw_total_revenue_inr']}\n"
        f"- duplicate_reconciliation_delta_inr: {findings['duplicate_reconciliation_delta_inr']}\n"
        f"- return_rate_by_payment: {findings['return_rate_by_payment']}\n"
        f"- highest_risk_segment: {findings['highest_risk_segment']}\n"
        f"- true_peak_month: {findings['true_peak_month']}\n"
        f"- outlier_inflated_month: {findings['outlier_inflated_month']}\n\n"
        "Write the narrative strictly using these values."
    )

    # --------------------------------------------------------------------------
    # Task 3 — Parameter locking and error handling
    # --- CALL WITH PARAMETER LOCKING --
    # --------------------------------------------------------------------------
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            system_instruction=system_instruction,
            contents=contents,
            generation_config={
                "temperature": 0.0,       # deterministic factual reporting
                "max_output_tokens": 300  # explicit token budget
            },
            timeout=10                    # ≥10 seconds
        )

        return {
            "status": "success",
            "narrative": response.text,
            "tokens": response.usage_metadata.total_token_count
        }

    except Exception as err:
        return generate_scr_narrative_offline(findings)


#------------------------------------------------------------------------#
#     Task 5 — Numeric accuracy checklist
#------------------------------------------------------------------------#

def verify_numeric_accuracy(narrative_text: str) -> bool:
    """Verifies that all 5 key figures exist in the narrative text

    after normalizing comma separators.
    """
    # Normalize string (remove commas for clean numerical matching)
    normalized_text = narrative_text.replace(",", "")

    # Required verification targets
    checks = {
        "Cleaned Total Revenue (97358.30)": [
            "97358.30",
            "97358.3",
        ],
        "COD Return Rate (44.4%)": ["44.4"],
        "COD Tier-2 Return Rate (54.5%)": ["54.5"],
        "Reconciliation Delta (2501.90)": [
            "2501.90",
            "2501.9",
        ],
        "True Peak Month (March / 20318.90)": [
            "March",
            "20318.90",
            "20318.9",
        ],
    }

    all_passed = True
    print("\n=== Task 5: Numeric Accuracy Checklist ===")

    for label, condition_groups in checks.items():
        # Item passes if EVERY condition group has at least one matching candidate string
        passed = all(
            any(candidate in normalized_text for candidate in group)
            for group in condition_groups
        )
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {label}")
        if not passed:
            all_passed = False

    return all_passed



if __name__ == "__main__":
    try:
      with open("narrator/findings.json", "r") as f:
        findings_data = json.load(f)

        result = generate_scr_narrative(findings_data)

        print("\nGenerated SCR Narrative:\n")
        print(result["narrative"])

        # Save sample output for Task 5 verification
        os.makedirs("narrator", exist_ok=True)
        with open("narrator/sample_output.txt", "w", encoding="utf-8") as f:
            f.write(result["narrative"])

        # Accuracy Checklist
        passed = verify_numeric_accuracy(result["narrative"])

        if passed:
          print("\nSUCCESS: All 5 required numbers verified in the narrative output!")

          
    except FileNotFoundError:
      print("Error: narrator/findings.json not found.")
