from typing import List
import numpy as np
from scipy import stats

from ragas import SingleTurnSample, EvaluationDataset
from ragas.metrics import Faithfulness, LLMContextPrecisionWithReference, ResponseGroundedness
from ragas.metrics._factual_correctness import FactualCorrectness

import pandas as pd
from scipy.stats import mannwhitneyu
from typing import Dict, List, Any, Tuple
import statistics
import logging
import random
import asyncio


import phoenix as px
import pandas as pd
import asyncio
import random # For placeholder simulation
from typing import List, Dict, Any
from datetime import datetime


import phoenix as px
from phoenix.trace import SpanEvaluations
import pandas as pd
import asyncio
import random # For placeholder simulation
from typing import List, Dict, Any
from datetime import datetime


async def evaluate_response(reference:List[str], user_query:str, model_response:str, evaluation_model = None):
    sample = SingleTurnSample(
        user_input=user_query,
        response = model_response,
        retrieved_context = reference,
        reference = "\n".join(reference),
    )

    # Faithfulness
    faithfulness = Faithfulness(llm = evaluation_model)
    context_precision = LLMContextPrecisionWithReference(llm = evaluation_model)
    groundedness = ResponseGroundedness(llm = evaluation_model)
    factual_correctness = FactualCorrectness(llm = evaluation_model)

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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_single_evaluation(system_id: str, prompt_tag: str, reference: List[str], user_query: str, model_response: str, evaluation_model=None):
    """
    Placeholder to represent getting a response and evaluating it.
    In a real scenario, this would involve:
    1. Calling the specific LLM associated with system_id.
    2. Calling your actual evaluate_response function.
    """
    # Simulate getting metrics from your evaluate_response
    # Replace this with: await evaluate_response(reference, user_query, model_response, evaluation_model)
    await asyncio.sleep(0.1) # Simulate async work
    metrics = {
        "faithfulness": random.uniform(0.6, 1.0),
        "context_precision": random.uniform(0.5, 0.95),
        "groundedness": random.uniform(0.7, 1.0),
        "factual_correctness": random.uniform(0.65, 0.98),
    }
    # Add identifiers
    metrics['system_id'] = system_id
    metrics['prompt_tag'] = prompt_tag
    metrics['user_query'] = user_query # Keep inputs for context if needed later
    metrics['model_response'] = model_response
    metrics['reference'] = reference
    return metrics

def compare_systems(
    evaluation_results: Dict[str, List[Dict[str, Any]]],
    alpha: float = 0.05
) -> Dict[str, Dict[str, Any]]:
    """
    Compares multiple systems based on evaluation metrics using statistical tests.

    Args:
        evaluation_results: A dictionary where keys are system identifiers
                            (e.g., 'llm_model_A+prompt_v1') and values are lists
                            of metric dictionaries returned by evaluate_response
                            for multiple runs of that system.
                            Example:
                            {
                                "system_A": [{"faithfulness": 0.8, "cp": 0.9}, {"faithfulness": 0.85, "cp": 0.92}, ...],
                                "system_B": [{"faithfulness": 0.7, "cp": 0.8}, {"faithfulness": 0.75, "cp": 0.85}, ...],
                            }
        alpha: The significance level for statistical tests (default: 0.05).

    Returns:
        A dictionary where keys are metric names. Values are dictionaries
        containing comparison results, like the best-performing system
        (if significantly different) and p-values.
    """
    if not evaluation_results:
        logging.warning("No evaluation results provided for comparison.")
        return {}

    if len(evaluation_results) < 2:
        logging.warning("Need at least two systems to compare.")
        return {}

    comparison_summary = {}
    system_ids = list(evaluation_results.keys())

    # Identify all unique metric keys from the first result of the first system
    # Assumes all results dictionaries have the same metric keys
    sample_result = evaluation_results[system_ids[0]][0]
    metric_keys = [k for k, v in sample_result.items() if isinstance(v, (int, float))]

    if not metric_keys:
        logging.warning("No numeric metric keys found in evaluation results.")
        return {}

    logging.info(f"Comparing systems: {system_ids} on metrics: {metric_keys}")

    for metric in metric_keys:
        comparison_summary[metric] = {
            "comparison_details": {},
            "best_system": "N/A",
            "significantly_different": False
        }
        metric_data = {sys_id: [res.get(metric) for res in results if res.get(metric) is not None]
                       for sys_id, results in evaluation_results.items()}

        # Perform pairwise comparisons using Mann-Whitney U test
        # Note: For >2 systems, Kruskal-Wallis followed by post-hoc (e.g., Dunn's)
        # is more appropriate for an overall test. Here we do pairwise.
        best_performing_system = None
        highest_median = -float('inf')
        is_significant = False

        system_medians = {}
        for sys_id, scores in metric_data.items():
             if scores:
                 system_medians[sys_id] = statistics.median(scores)
             else:
                 system_medians[sys_id] = -float('inf') # Handle empty scores case

        # Find the system with the highest median score initially
        initial_best_sys = max(system_medians, key=system_medians.get) if system_medians else None

        if not initial_best_sys or system_medians[initial_best_sys] == -float('inf'):
             comparison_summary[metric]["notes"] = "Insufficient data for comparison."
             continue

        # Compare the initial best against all others
        all_comparisons_significant = True
        is_potentially_better = True
        for other_sys_id in system_ids:
            if other_sys_id == initial_best_sys:
                continue

            scores1 = metric_data[initial_best_sys]
            scores2 = metric_data[other_sys_id]

            if not scores1 or not scores2 or len(scores1) < 3 or len(scores2) < 3: # Need min samples for meaningful test
                comparison_summary[metric]["comparison_details"][f"{initial_best_sys}_vs_{other_sys_id}"] = "Insufficient data"
                is_potentially_better = False
                all_comparisons_significant = False # Cannot claim significance if any pair has insufficient data
                logging.warning(f"Skipping comparison for {metric} between {initial_best_sys} and {other_sys_id} due to insufficient data.")
                continue

            try:
                # We test if scores1 > scores2 (one-sided)
                stat, p_value = mannwhitneyu(scores1, scores2, alternative='greater')

                comparison_summary[metric]["comparison_details"][f"{initial_best_sys}_vs_{other_sys_id}"] = {
                    "median_diff": system_medians[initial_best_sys] - system_medians[other_sys_id],
                    "p_value": p_value,
                    "significant": p_value < alpha
                }

                if p_value >= alpha:
                   # If not significantly greater than even one other system, it's not definitively the best
                   all_comparisons_significant = False

            except ValueError as e:
                # Handle cases like all values being identical
                logging.warning(f"Mann-Whitney U test failed for {metric} between {initial_best_sys} and {other_sys_id}: {e}")
                comparison_summary[metric]["comparison_details"][f"{initial_best_sys}_vs_{other_sys_id}"] = f"Test failed: {e}"
                all_comparisons_significant = False


        if is_potentially_better and all_comparisons_significant:
             comparison_summary[metric]["best_system"] = initial_best_sys
             comparison_summary[metric]["significantly_different"] = True
             comparison_summary[metric]["notes"] = f"{initial_best_sys} median ({system_medians[initial_best_sys]:.3f}) is significantly higher than all others (p < {alpha})."
        elif is_potentially_better:
             # It had the highest median, but wasn't significantly better than *all* others
             comparison_summary[metric]["best_system"] = initial_best_sys
             comparison_summary[metric]["significantly_different"] = False
             comparison_summary[metric]["notes"] = f"{initial_best_sys} has the highest median ({system_medians[initial_best_sys]:.3f}), but not significantly higher than all compared systems."
        else:
             # Often due to insufficient data for the top system
             comparison_summary[metric]["best_system"] = initial_best_sys if initial_best_sys else "N/A"
             comparison_summary[metric]["significantly_different"] = False
             comparison_summary[metric]["notes"] = f"No single system found to be significantly better than all others. Highest median observed for {initial_best_sys} ({system_medians.get(initial_best_sys, 'N/A'):.3f}). Check comparison details."


    return comparison_summary

# Assume your original evaluate_response is defined elsewhere
# from your_module import evaluate_response, SingleTurnSample, Faithfulness, ...

# --- Phoenix Setup ---
# Start the Phoenix app session. Data will be viewable at the printed URL.
# Note: In production or long-running scenarios, consider running the Phoenix server separately.
# try:
#     session = px.launch_app()
#     logging.info(f"Phoenix UI running at: {session.url}")
# except Exception as e:
#     logging.error(f"Failed to launch Phoenix: {e}. Tracking will be disabled.")
#     session = None # Disable logging if launch fails


async def evaluate_systems_and_track(
    systems_to_evaluate: Dict[str, Dict[str, Any]], # Key: system_id, Value: {'llm_model': obj, 'prompt_tag': str, 'prompt_text': str}
    evaluation_dataset: List[Dict[str, Any]], # List of {'user_query': str, 'reference': List[str]}
    evaluation_llm=None # The LLM used for running evaluations (e.g., GPT-4)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Runs evaluations for multiple systems on a dataset and logs results to Phoenix.

    Args:
        systems_to_evaluate: Dictionary defining the systems.
            Example: {
                "gpt4_prompt_v1": {"llm_model": gpt4_client, "prompt_tag": "v1", "prompt_text": "Answer..." },
                "claude3_prompt_v2": {"llm_model": claude_client, "prompt_tag": "v2", "prompt_text": "Provide details..."}
            }
        evaluation_dataset: List of data points to evaluate on.
        evaluation_llm: Model used by the evaluate_response function itself.

    Returns:
        A dictionary containing the raw evaluation results for each system,
        suitable for input into the compare_systems function.
    """
    all_results = {sys_id: [] for sys_id in systems_to_evaluate}
    phoenix_data = []

    for i, data_point in enumerate(evaluation_dataset):
        user_query = data_point['user_query']
        reference = data_point['reference']
        logging.info(f"Processing data point {i+1}/{len(evaluation_dataset)}: {user_query[:50]}...")

        for system_id, config in systems_to_evaluate.items():
            llm_model_client = config['llm_model'] # In real code, use this client
            prompt_tag = config['prompt_tag']
            prompt_text = config['prompt_text'] # Use this specific prompt text

            # --- Simulate LLM Call ---
            # Replace with actual call:
            # model_response = await llm_model_client.generate(prompt=prompt_text.format(query=user_query), ...)
            await asyncio.sleep(0.2) # Simulate API call
            model_response = f"Response from {system_id} for query '{user_query[:20]}...' - {random.random():.3f}"
            # -------------------------

            # --- Evaluate Response ---
            try:
                # *** Replace with your actual call ***
                # metrics = await evaluate_response(reference, user_query, model_response, evaluation_llm)

                # Using placeholder for now:
                metrics = await run_single_evaluation(system_id, prompt_tag, reference, user_query, model_response, evaluation_llm)

                # --- Prepare data for Phoenix ---
                log_entry = {
                    # Identifiers
                    "run_id": f"run_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}_{system_id}", # Unique ID for the eval row
                    "system_id": system_id, # Combined LLM+Prompt ID
                    "prompt_tag": prompt_tag, # Specific tag for the prompt version
                    # Inputs
                    "user_query": user_query,
                    # "reference": "\n".join(reference), # Can be large, log if needed
                    # Outputs
                    "model_response": model_response,
                    # Metrics (flatten the dict)
                    **{f"metric_{k}": v for k, v in metrics.items() if isinstance(v, (int, float))} # Prefix metrics
                }
                phoenix_data.append(log_entry)

                # Store result for statistical comparison later
                all_results[system_id].append(metrics) # Store the original metrics dict

            except Exception as e:
                logging.error(f"Failed to evaluate system {system_id} on data point {i}: {e}")
                # Store a failure or skip? Decide based on your needs.
                # For now, we just log the error and skip storing the result.
                all_results[system_id].append({"error": str(e)}) # Or handle differently

    return all_results

# --- Example Usage ---

async def main():
    # Define your systems (LLM clients would be real objects)
    systems = {
        "gpt4_prompt_v1.1": {"llm_model": "GPT-4 Client Placeholder", "prompt_tag": "v1.1-summary", "prompt_text": "Summarize this concisely: {query}"},
        "claude3_prompt_v2.0": {"llm_model": "Claude3 Client Placeholder", "prompt_tag": "v2.0-summary-bullets", "prompt_text": "Summarize this as bullet points: {query}"},
         "gpt4_prompt_v1.2": {"llm_model": "GPT-4 Client Placeholder", "prompt_tag": "v1.2-summary-detail", "prompt_text": "Summarize this with detail: {query}"}
    }

    # Define your evaluation dataset
    dataset = [
        {"user_query": "The quick brown fox jumps over the lazy dog.", "reference": ["A sentence describing animal actions."]},
        {"user_query": "Artificial intelligence is transforming industries.", "reference": ["AI impacts business.", "Machine learning applications."]},
        {"user_query": "Python is a versatile programming language.", "reference": ["Python details", "Programming language info"]},
        # Add more data points (ideally 20+ for meaningful stats)
        {"user_query": "What is the capital of France?", "reference": ["Paris is the capital."]},
        {"user_query": "Explain the theory of relativity.", "reference": ["Einstein's theory", "Physics concept"]},
    ] * 5 # Multiply for more data points in example

    # Run evaluations and track with Phoenix
    raw_results = await evaluate_systems_and_track(systems, dataset)

    # Perform statistical comparison on the results
    comparison_report = compare_systems(raw_results)

    print("\n--- Statistical Comparison Report ---")
    for metric, result in comparison_report.items():
        print(f"\nMetric: {metric}")
        print(f"  Best Performing System (if significant): {result.get('best_system', 'N/A')}")
        print(f"  Significantly Different: {result.get('significantly_different', False)}")
        print(f"  Notes: {result.get('notes', '')}")
        # Optionally print pairwise details
        # print(f"  Comparison Details: {result.get('comparison_details', {})}")

    print("\n--- End of Report ---")
    # print(f"Check the Phoenix UI for detailed run logs: {session.url if session else 'Phoenix not running'}")

    # # Keep the script running briefly if Phoenix was launched inline
    # if session:
    #     print("Phoenix UI is running. Press Ctrl+C to exit.")
    #     await asyncio.sleep(300) # Keep alive for 5 mins

if __name__ == "__main__":
    # Setup asyncio event loop and run main
    asyncio.run(main())
