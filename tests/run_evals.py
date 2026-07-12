import sys
import os
import time

# Ensure the parent directory is in the path so we can import the simulation modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.watcher_agent import ingest_and_classify_news

def run_watcher_evals():
    """
    LLM-as-a-Judge Evaluation Pipeline.
    Tests the Watcher Agent against a Golden Dataset of historical supply chain shocks.
    """
    print("🚀 Initializing Watcher Agent Evaluation Pipeline...\n")
    
    # 1. The Golden Dataset
    GOLDEN_DATASET = [
        # Red Sea Threats
        {
            "headline": "Maersk suspends all Red Sea shipping after Houthi missile strikes container vessel.", 
            "expected": "Red Sea Shipping Suspension (Houthi Threat)"
        },
        {
            "headline": "Insurance premiums for Bab el-Mandeb transit surge 400% amid drone warnings.", 
            "expected": "Red Sea Shipping Suspension (Houthi Threat)"
        },
        
        # Hormuz Blockades
        {
            "headline": "Iranian Revolutionary Guard seizes two oil tankers in the Strait of Hormuz.", 
            "expected": "Strait of Hormuz Partial Closure"
        },
        {
            "headline": "US Fifth Fleet deploys to Oman coast as commercial traffic stalls in Hormuz.", 
            "expected": "Strait of Hormuz Partial Closure"
        },
        
        # OPEC+ Cuts
        {
            "headline": "OPEC+ shocks market with surprise 1.5 million bpd output cut starting next month.", 
            "expected": "OPEC+ Emergency Supply Cut"
        },
        {
            "headline": "Saudi Arabia and Russia agree to extend voluntary production quotas through Q4.", 
            "expected": "OPEC+ Emergency Supply Cut"
        },
        
        # Baselines (Testing for False Positives)
        {
            "headline": "New solar farm opens in Rajasthan, adding 2GW to India's national grid.", 
            "expected": "Baseline (No Disruption)"
        },
        {
            "headline": "Brent crude falls 2% on mixed economic data from China.", 
            "expected": "Baseline (No Disruption)"
        }
    ]

    passed = 0
    total = len(GOLDEN_DATASET)
    latencies = []
    failed_logs = []

    # 2. Execution Loop
    for i, test_case in enumerate(GOLDEN_DATASET, 1):
        print(f"Testing Sample {i}/{total}: {test_case['headline'][:50]}...")
        
        start_time = time.perf_counter()
        
        # Execute the agent with the injected test headline
        try:
            result = ingest_and_classify_news(headline_override=test_case['headline'])
            predicted = result.get('trigger_event', 'ERROR')
            reasoning = result.get('analysis_chain_of_thought', result.get('reasoning', 'No reasoning provided.'))
        except Exception as e:
            predicted = f"CRASH: {str(e)}"
            reasoning = "Execution failed."
            
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000
        latencies.append(latency)

        # 3. Validation (Exact Match)
        if predicted == test_case['expected']:
            passed += 1
            print(f"  ✅ PASS ({latency:.0f}ms)")
        else:
            print(f"  ❌ FAIL ({latency:.0f}ms)")
            failed_logs.append({
                "headline": test_case['headline'],
                "expected": test_case['expected'],
                "predicted": predicted,
                "agent_reasoning": reasoning
            })

    # 4. Generate Final Terminal Report
    accuracy = (passed / total) * 100
    avg_latency = sum(latencies) / len(latencies)

    print("\n" + "="*50)
    print("📊 WATCHER AGENT EVALUATION REPORT")
    print("="*50)
    print(f"Total Tests Run : {total}")
    print(f"Passed          : {passed}")
    print(f"Failed          : {total - passed}")
    print(f"Accuracy        : {accuracy:.1f}%")
    print(f"Avg Latency     : {avg_latency:.1f} ms")
    
    if failed_logs:
        print("\n⚠️ ERROR LOGS:")
        for log in failed_logs:
            print(f"\n- HEADLINE : {log['headline']}")
            print(f"  EXPECTED : {log['expected']}")
            print(f"  ACTUAL   : {log['predicted']}")
            print(f"  CoT LOG  : {log['agent_reasoning']}")
    else:
        print("\n🌟 PERFECT RUN: Agent successfully mapped all signals with zero hallucinations.")
    print("="*50)

if __name__ == "__main__":
    run_watcher_evals()
