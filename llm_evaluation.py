import pandas as pd
from scipy.stats import mannwhitneyu
from typing import Dict, List, Any, Tuple
import statistics
import logging
import asyncio
import random # Keep for evaluate_response simulation if needed
from datetime import datetime

from ragas import SingleTurnSample
from ragas.metrics import Faithfulness, LLMContextPrecisionWithReference, ResponseGroundedness
from ragas.metrics._factual_correctness import FactualCorrectness

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Your Evaluation Function (Provided by User) ---
async def evaluate_response(reference:List[str], user_query:str, model_response:str, evaluation_model = None):
    """Calculates Ragas metrics for a given interaction."""
    # Added basic error handling for robustness
    metrics_result = {}
    try:
        sample = SingleTurnSample(
            user_input=user_query,
            response=model_response,
            retrieved_context=reference, # Assuming reference is the retrieved context
            reference="\n".join(reference), # Assuming reference is also the ground truth reference
        )

        # Initialize metrics (consider doing this once outside if evaluation_model is constant)
        faithfulness = Faithfulness(llm=evaluation_model)
        context_precision = LLMContextPrecisionWithReference(llm=evaluation_model)
        groundedness = ResponseGroundedness(llm=evaluation_model)
        factual_correctness = FactualCorrectness(llm=evaluation_model)

        faithfulness_score = await faithfulness.single_turn_ascore(sample)
        context_precision_score = await context_precision.single_turn_ascore(sample)
        groundedness_score = await groundedness.single_turn_ascore(sample)
        factual_correctness_score = await factual_correctness.single_turn_ascore(sample)

        return {
            "faithfulness": faithfulness_score,
            "context_precision": context_precision_score,
            "groundedness": groundedness_score,
            "factual_correctness": factual_correctness_score,
        }


    except Exception as e:
        logging.error(f"Error creating Ragas sample or initializing metrics for query '{user_query[:30]}...': {e}")
        # Return None for all metrics if sample creation fails
        metrics_result = {
           "faithfulness": None, "context_precision": None,
           "groundedness": None, "factual_correctness": None
        }

    return metrics_result


# --- Statistical Comparison Function (Unchanged Logic) ---
def compare_systems(
    evaluation_results: Dict[str, List[Dict[str, Any]]],
    alpha: float = 0.05
) -> Dict[str, Dict[str, Any]]:
    """
    Compares multiple systems based on evaluation metrics using statistical tests.
    (Logic remains the same as it compares distributions independently)
    """
    if not evaluation_results:
        logging.warning("No evaluation results provided for comparison.")
        return {}

    # Filter out systems with no valid results
    valid_results = {
        sys_id: results for sys_id, results in evaluation_results.items() if results
    }

    if len(valid_results) < 2:
        logging.warning(f"Need at least two systems with valid results to compare. Found: {list(valid_results.keys())}")
        return {}

    comparison_summary = {}
    system_ids = list(valid_results.keys())

    # Identify all unique numeric metric keys robustly
    all_metric_keys = set()
    for results in valid_results.values():
        for res_dict in results:
            for k, v in res_dict.items():
                if isinstance(v, (int, float)):
                    all_metric_keys.add(k)

    metric_keys = sorted(list(all_metric_keys))

    if not metric_keys:
        logging.warning("No numeric metric keys found across all evaluation results.")
        return {}

    logging.info(f"Comparing systems: {system_ids} on metrics: {metric_keys}")

    for metric in metric_keys:
        comparison_summary[metric] = {
            "comparison_details": {},
            "best_system": "N/A",
            "significantly_different": False,
            "notes": ""
        }
        # Extract scores, explicitly handling None/NaN
        metric_data = {}
        for sys_id, results in valid_results.items():
             scores = [res.get(metric) for res in results]
             # Filter out None values before statistical analysis
             valid_scores = [s for s in scores if s is not None and not pd.isna(s)]
             metric_data[sys_id] = valid_scores

        # Check if any system has data for this metric
        if not any(metric_data.values()):
             comparison_summary[metric]["notes"] = "No valid data found for any system for this metric."
             continue

        system_medians = {}
        for sys_id, scores in metric_data.items():
             if scores:
                 system_medians[sys_id] = statistics.median(scores)
             else:
                 # Keep track, but maybe don't calculate median
                 system_medians[sys_id] = None # Explicitly None if no valid scores

        # Find the system with the highest median score among those with scores
        valid_medians = {k: v for k, v in system_medians.items() if v is not None}
        if not valid_medians:
            comparison_summary[metric]["notes"] = "No systems had valid scores to calculate a median."
            continue

        initial_best_sys = max(valid_medians, key=valid_medians.get)
        highest_median_val = valid_medians[initial_best_sys]

        # Compare the initial best against all *other* systems that have valid data
        all_comparisons_significant = True
        potential_competitors = [sid for sid in system_ids if sid != initial_best_sys and metric_data.get(sid)] # Only compare against systems with data

        if not potential_competitors:
             comparison_summary[metric]["best_system"] = initial_best_sys
             comparison_summary[metric]["significantly_different"] = False # Cannot be significant if no competitors
             comparison_summary[metric]["notes"] = f"{initial_best_sys} has the highest median ({highest_median_val:.3f}), but no other systems had valid data for comparison on this metric."
             continue


        for other_sys_id in potential_competitors:
            scores1 = metric_data[initial_best_sys]
            scores2 = metric_data[other_sys_id]

            # Check sample size AFTER filtering None
            if len(scores1) < 3 or len(scores2) < 3:
                comparison_summary[metric]["comparison_details"][f"{initial_best_sys}_vs_{other_sys_id}"] = f"Insufficient data (need >=3 samples per group, got {len(scores1)} vs {len(scores2)})"
                all_comparisons_significant = False
                logging.warning(f"Skipping comparison for {metric} between {initial_best_sys} and {other_sys_id} due to insufficient valid data.")
                continue

            try:
                # Test if scores1 > scores2 (one-sided Mann-Whitney U)
                # This test assumes scores are continuous or ordinal.
                stat, p_value = mannwhitneyu(scores1, scores2, alternative='greater', nan_policy='omit') # nan_policy='omit' might be redundant due to prior filtering

                comparison_summary[metric]["comparison_details"][f"{initial_best_sys}_vs_{other_sys_id}"] = {
                    "median_diff": highest_median_val - (system_medians.get(other_sys_id) if system_medians.get(other_sys_id) is not None else float('nan')),
                    "p_value": p_value,
                    "significant": p_value < alpha
                }

                if p_value >= alpha:
                    all_comparisons_significant = False # Not significantly better than this competitor

            except ValueError as e:
                # Handle cases like all values being identical or other issues
                logging.warning(f"Mann-Whitney U test failed for {metric} between {initial_best_sys} and {other_sys_id}: {e}")
                comparison_summary[metric]["comparison_details"][f"{initial_best_sys}_vs_{other_sys_id}"] = f"Test failed: {e}"
                all_comparisons_significant = False

        # Summarize findings
        if all_comparisons_significant:
             comparison_summary[metric]["best_system"] = initial_best_sys
             comparison_summary[metric]["significantly_different"] = True
             comparison_summary[metric]["notes"] = f"{initial_best_sys} median ({highest_median_val:.3f}) is significantly higher than all other comparable systems (p < {alpha})."
        else:
             comparison_summary[metric]["best_system"] = initial_best_sys # Still has highest median
             comparison_summary[metric]["significantly_different"] = False
             comparison_summary[metric]["notes"] = f"{initial_best_sys} has the highest median ({highest_median_val:.3f}), but was not significantly higher than all comparable systems (alpha={alpha}). Check details."

    return comparison_summary


# --- Modified Evaluation and Tracking Function ---
async def evaluate_systems_and_track(
    systems_config: Dict[str, Dict[str, Any]], # Key: system_id, Value: {'llm_model': obj, 'prompt_tag': str} - NO prompt_text needed here
    evaluation_data_per_system: Dict[str, List[Dict[str, Any]]], # Key: system_id, Value: List of {'user_query': str, 'reference': List[str], 'model_response': str}
    evaluation_llm=None # The LLM used by Ragas evaluate_response function
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Runs evaluations for multiple systems using provided data for each, logs to Phoenix.

    Args:
        systems_config: Dictionary defining system configurations (like model client, tags).
             Example: { "gpt4_prompt_v1": {"llm_model": gpt4_client, "prompt_tag": "v1"} }
                     (Note: 'llm_model' here is the one being *evaluated*, not the Ragas evaluation_llm)
        evaluation_data_per_system: Dictionary where keys are system_ids matching systems_config,
            and values are lists of evaluation data points for that system. Each data point is a dict:
            {'user_query': str, 'reference': List[str], 'model_response': str}
        evaluation_llm: Model used by the Ragas evaluate_response function itself.

    Returns:
        A dictionary containing the raw evaluation metric results for each system.
    """
    all_results = {sys_id: [] for sys_id in systems_config.keys()}
    phoenix_data = []
    total_evals = sum(len(data) for data in evaluation_data_per_system.values())
    eval_count = 0

    # --- Evaluation Loop ---
    for system_id, data_points in evaluation_data_per_system.items():
        if system_id not in systems_config:
            logging.warning(f"Skipping system '{system_id}' found in data but not in systems_config.")
            continue

        config = systems_config[system_id]
        prompt_tag = config.get('prompt_tag', 'unknown') # Get tag from config
        # llm_model_client = config.get('llm_model', None) # Client of the model *being* evaluated (useful for logging tags/metadata)

        logging.info(f"--- Evaluating System: {system_id} ({len(data_points)} data points) ---")

        for i, data_point in enumerate(data_points):
            eval_count += 1
            user_query = data_point.get('user_query')
            reference = data_point.get('reference')
            model_response = data_point.get('model_response')

            if not all([user_query, reference, model_response]):
                logging.warning(f"Skipping data point {i} for system {system_id} due to missing 'user_query', 'reference', or 'model_response'.")
                continue

            logging.info(f"Processing {system_id} - item {i+1}/{len(data_points)} (Total {eval_count}/{total_evals})")

            # --- Evaluate Response ---
            try:
                # *** Call your ACTUAL evaluate_response function ***
                # metrics = await evaluate_response(
                #     reference=reference,
                #     user_query=user_query,
                #     model_response=model_response,
                #     evaluation_model=evaluation_llm # Pass the Ragas evaluation LLM
                # )

                await asyncio.sleep(0.1) # Simulate async work
                metrics = {
                    "faithfulness": random.uniform(0.6, 1.0),
                    "context_precision": random.uniform(0.5, 0.95),
                    "groundedness": random.uniform(0.7, 1.0),
                    "factual_correctness": random.uniform(0.65, 0.98),
                }

                # Add identifiers to the results dict *before* storing/logging
                metrics['system_id'] = system_id
                metrics['prompt_tag'] = prompt_tag
                # Store raw results for the comparison function
                all_results[system_id].append(metrics)

                # --- Prepare data for Phoenix ---
                # Only log rows where metrics calculation didn't completely fail
                if any(v is not None for k, v in metrics.items() if k not in ['system_id', 'prompt_tag']):
                    log_entry = {
                        # Identifiers
                        "run_id": f"run_{datetime.now().strftime('%Y%m%d%H%M%S')}_{eval_count}", # Unique ID
                        "system_id": system_id,
                        "prompt_tag": prompt_tag,
                        # Inputs / Outputs (log references if not too large/sensitive)
                        "user_query": user_query,
                        # "reference_context": "\n".join(reference), # Example: Log context if needed
                        "model_response": model_response,
                        # Metrics (flatten the dict, prefix, handle None)
                        **{f"metric_{k}": (float(v) if v is not None else None)
                           for k, v in metrics.items()
                           if k not in ['system_id', 'prompt_tag'] and isinstance(v, (int, float, type(None)))} # Filter system_id/tag and ensure numeric/None
                    }
                    phoenix_data.append(log_entry)
                else:
                     logging.warning(f"Skipping Phoenix logging for run {eval_count} (system {system_id}) as all metrics were None.")


            except Exception as e:
                logging.error(f"Failed evaluation for system {system_id} on item {i}: {e}", exc_info=True)
                # Store error information if needed
                all_results[system_id].append({
                    "system_id": system_id,
                    "prompt_tag": prompt_tag,
                    "error": str(e),
                    "faithfulness": None, "context_precision": None, # Ensure keys exist for comparison fn
                    "groundedness": None, "factual_correctness": None
                })

    return all_results


# --- Example Usage ---
async def main():
    # Define system configurations (placeholders for actual LLM clients used for generation)
    # The 'llm_model' here is metadata about the system being tested, not the Ragas evaluator
    systems_config = {
        "gpt4_prompt_v1.1": {"llm_model_name": "GPT-4", "prompt_tag": "v1.1-summary"},
        "claude3_prompt_v2.0": {"llm_model_name": "Claude-3-Opus", "prompt_tag": "v2.0-summary-bullets"},
        "mistral_prompt_v1.0": {"llm_model_name": "Mistral-Large", "prompt_tag": "v1.0-concise"}
    }

    # --- Define Evaluation Data PER SYSTEM ---
    # Note: The number of data points can differ between systems
    evaluation_data = {
        "gpt4_prompt_v1.1": [
            {"user_query": "Explain quantum entanglement simply.", "reference": ["Quantum physics concept", "Spooky action"], "model_response": "Quantum entanglement links particles instantly over distance. (GPT4-v1.1)"},
            {"user_query": "What are the benefits of Python?", "reference": ["Easy syntax", "Large community"], "model_response": "Python is easy to learn, versatile, and has many libraries. (GPT4-v1.1)"},
            {"user_query": "Summarize the plot of Hamlet.", "reference": ["Shakespearean tragedy", "Revenge plot"], "model_response": "Hamlet seeks revenge for his father's murder by his uncle. (GPT4-v1.1)"},
        ] * 5, # Repeat for more data
        "claude3_prompt_v2.0": [
            {"user_query": "Explain quantum entanglement simply.", "reference": ["Quantum physics concept", "Spooky action"], "model_response": "* Entanglement: Linked particles. * Measurement: Instantly affects partner. (Claude3-v2.0)"},
            # This system has one less data point for this query
            {"user_query": "Summarize the plot of Hamlet.", "reference": ["Shakespearean tragedy", "Revenge plot"], "model_response": "* Prince Hamlet's father killed. * Uncle Claudius marries mother. * Hamlet seeks vengeance. (Claude3-v2.0)"},
        ] * 6, # Repeat for more data
         "mistral_prompt_v1.0": [
            {"user_query": "Explain quantum entanglement simply.", "reference": ["Quantum physics concept", "Spooky action"], "model_response": "Particles linked instantly. (Mistral-v1.0)"},
            {"user_query": "What are the benefits of Python?", "reference": ["Easy syntax", "Large community"], "model_response": "Simple, versatile, big community. (Mistral-v1.0)"},
            {"user_query": "Summarize the plot of Hamlet.", "reference": ["Shakespearean tragedy", "Revenge plot"], "model_response": "Hamlet seeks revenge. (Mistral-v1.0)"},
            {"user_query": "Capital of Australia?", "reference": ["Canberra"], "model_response": "Canberra. (Mistral-v1.0)"}, # Extra data point for this system
        ] * 4, # Repeat for more data
    }

    # --- Define the Evaluation LLM (used by Ragas) ---
    # Replace with your actual Ragas evaluation model setup (e.g., Langchain LLM)
    ragas_evaluation_llm = None # Or: LangchainLLM(llm=YourChatModel())
    logging.warning("Using 'None' for Ragas evaluation LLM. Real evaluations require a configured LLM.")


    # --- Run Evaluations and Track ---
    raw_results = await evaluate_systems_and_track(
        systems_config=systems_config,
        evaluation_data_per_system=evaluation_data,
        evaluation_llm=ragas_evaluation_llm
    )

    # --- Perform Statistical Comparison ---
    comparison_report = compare_systems(raw_results)

    print("\n--- Statistical Comparison Report ---")
    if comparison_report:
        for metric, result in comparison_report.items():
            print(f"\nMetric: {metric}")
            print(f"  Best Performing System (Highest Median): {result.get('best_system', 'N/A')}")
            print(f"  Significantly Better than ALL others?: {result.get('significantly_different', False)}")
            print(f"  Notes: {result.get('notes', '')}")
            # Uncomment to see pairwise details:
            # print(f"  Comparison Details: {result.get('comparison_details', {})}")
    else:
        print("Comparison could not be performed. Check logs for warnings.")

    print("\n--- End of Report ---")

if __name__ == "__main__":
    asyncio.run(main())