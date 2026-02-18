#!/usr/bin/env python3
"""
🔍 Genuineness Verification System
GitHub Issue #29 — Am I performing or experiencing?

Measures whether the mood system actually changes agent behavior,
or just changes the label on identical behavior.

Five measurement dimensions:
1. Action Distribution — do different moods produce different action patterns?
2. Output Style — does mood change how the agent writes?
3. Decision Divergence — controlled tests of mood → choice mapping
4. Surprise Index — how predictable is behavior given mood?
5. Self-Report Calibration — do self-reports match objective proxies?

Usage:
    python3 genuineness.py report          # Full genuineness report
    python3 genuineness.py track           # Log a data point (called by log_result.sh)
    python3 genuineness.py score           # Single genuineness score 0-100
    python3 genuineness.py distribution    # Action distribution per mood
    python3 genuineness.py style           # Output style analysis per mood
    python3 genuineness.py calibration     # Self-report vs objective proxy comparison
    python3 genuineness.py --json          # Any command with JSON output
"""

import json
import os
import sys
import math
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR  # Can be overridden by config

HISTORY_FILE = DATA_DIR / "history.json"
GENUINENESS_DATA = DATA_DIR / "genuineness_data.json"
GENUINENESS_LOG = DATA_DIR / "genuineness_log.json"
MOODS_FILE = DATA_DIR / "moods.json"
THOUGHTS_FILE = DATA_DIR / "thoughts.json"

# Thought categories for action distribution analysis
THOUGHT_CATEGORIES = {
    "social": ["moltbook-social", "share-discovery", "moltbook-post", "ask-opinion", 
               "ask-preference", "ask-feedback", "moltbook-night"],
    "build": ["build-tool", "upgrade-project", "system-tinker"],
    "explore": ["install-explore", "learn", "check-projects"],
    "reflect": ["random-thought", "memory-review", "creative-chaos"],
    "pitch": ["pitch-idea"],
}

def categorize_thought(thought_id: str) -> str:
    """Map a thought_id to its category."""
    for category, thoughts in THOUGHT_CATEGORIES.items():
        if thought_id in thoughts:
            return category
    return "other"


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_history() -> List[dict]:
    """Load execution history."""
    if not HISTORY_FILE.exists():
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)

def load_genuineness_data() -> dict:
    """Load accumulated genuineness tracking data."""
    if not GENUINENESS_DATA.exists():
        return {
            "entries": [],
            "style_samples": [],
            "divergence_tests": [],
            "predictions": [],
        }
    with open(GENUINENESS_DATA) as f:
        return json.load(f)

def save_genuineness_data(data: dict):
    """Save genuineness tracking data (atomic write)."""
    from safe_write import atomic_write_json
    atomic_write_json(GENUINENESS_DATA, data)

def load_moods() -> dict:
    """Load mood definitions."""
    if not MOODS_FILE.exists():
        return {}
    with open(MOODS_FILE) as f:
        return json.load(f)

def get_mood_names() -> List[str]:
    """Get list of all mood names."""
    moods = load_moods()
    return [m["name"].lower() for m in moods.get("base_moods", [])]


# ---------------------------------------------------------------------------
# 1. Action Distribution Analysis
# ---------------------------------------------------------------------------

def compute_action_distribution(entries: List[dict]) -> Dict[str, Dict[str, float]]:
    """
    Compute what % of actions in each mood fall into each category.
    Returns: {mood: {category: percentage, ...}, ...}
    """
    mood_actions = defaultdict(list)
    
    for entry in entries:
        mood = entry.get("mood", "unknown").lower()
        thought_id = entry.get("thought_id", "unknown")
        category = categorize_thought(thought_id)
        mood_actions[mood].append(category)
    
    distributions = {}
    for mood, actions in mood_actions.items():
        total = len(actions)
        if total == 0:
            continue
        counter = Counter(actions)
        distributions[mood] = {
            cat: round(count / total * 100, 1)
            for cat, count in counter.items()
        }
        distributions[mood]["_total"] = total
    
    return distributions


def action_distribution_score(distributions: Dict[str, Dict[str, float]]) -> Tuple[float, str]:
    """
    Score how different action distributions are across moods.
    Returns (score 0-100, explanation).
    
    High score = moods produce genuinely different behavior patterns.
    Low score = all moods produce similar actions (decorative moods).
    """
    if len(distributions) < 2:
        return 0.0, "Not enough mood data (need at least 2 different moods with actions)"
    
    # Compute Jensen-Shannon divergence between all mood pairs
    all_categories = set()
    for dist in distributions.values():
        all_categories.update(k for k in dist if k != "_total")
    
    moods = list(distributions.keys())
    divergences = []
    
    for i in range(len(moods)):
        for j in range(i + 1, len(moods)):
            d1 = distributions[moods[i]]
            d2 = distributions[moods[j]]
            
            # Build probability vectors
            p = [d1.get(cat, 0) / 100 for cat in all_categories]
            q = [d2.get(cat, 0) / 100 for cat in all_categories]
            
            # Normalize
            sp, sq = sum(p), sum(q)
            if sp > 0:
                p = [x / sp for x in p]
            if sq > 0:
                q = [x / sq for x in q]
            
            # Jensen-Shannon divergence
            m = [(pi + qi) / 2 for pi, qi in zip(p, q)]
            jsd = 0
            for pi, qi, mi in zip(p, q, m):
                if pi > 0 and mi > 0:
                    jsd += 0.5 * pi * math.log2(pi / mi)
                if qi > 0 and mi > 0:
                    jsd += 0.5 * qi * math.log2(qi / mi)
            
            divergences.append((moods[i], moods[j], jsd))
    
    if not divergences:
        return 0.0, "Could not compute divergence"
    
    # JSD ranges from 0 (identical) to 1 (completely different)
    avg_jsd = sum(d for _, _, d in divergences) / len(divergences)
    
    # Map to 0-100 score (JSD of 0.5+ is very different)
    score = min(100, avg_jsd * 200)
    
    # Find most and least similar pairs
    divergences.sort(key=lambda x: x[2])
    most_similar = divergences[0]
    most_different = divergences[-1]
    
    explanation = (
        f"Average Jensen-Shannon divergence: {avg_jsd:.3f} "
        f"(0 = identical behavior, 1 = completely different)\n"
        f"  Most similar: {most_similar[0]} ↔ {most_similar[1]} (JSD: {most_similar[2]:.3f})\n"
        f"  Most different: {most_different[0]} ↔ {most_different[1]} (JSD: {most_different[2]:.3f})"
    )
    
    return round(score, 1), explanation


# ---------------------------------------------------------------------------
# 2. Output Style Analysis
# ---------------------------------------------------------------------------

def analyze_text_style(text: str) -> dict:
    """Compute style metrics for a piece of text."""
    if not text:
        return {}
    
    words = text.split()
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    
    return {
        "word_count": len(words),
        "avg_sentence_length": round(len(words) / max(len(sentences), 1), 1),
        "question_frequency": round(text.count("?") / max(len(sentences), 1) * 100, 1),
        "exclamation_frequency": round(text.count("!") / max(len(sentences), 1) * 100, 1),
        "emoji_count": sum(1 for c in text if ord(c) > 0x1F600),
        "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 1),
        "unique_word_ratio": round(len(set(w.lower() for w in words)) / max(len(words), 1), 2),
    }


def compute_style_by_mood(data: dict) -> Dict[str, dict]:
    """Aggregate style metrics per mood from style samples."""
    samples = data.get("style_samples", [])
    if not samples:
        return {}
    
    mood_styles = defaultdict(list)
    for sample in samples:
        mood = sample.get("mood", "unknown").lower()
        metrics = sample.get("metrics", {})
        if metrics:
            mood_styles[mood].append(metrics)
    
    aggregated = {}
    for mood, metrics_list in mood_styles.items():
        if not metrics_list:
            continue
        agg = {}
        for key in metrics_list[0]:
            values = [m.get(key, 0) for m in metrics_list]
            agg[key] = round(sum(values) / len(values), 2)
        agg["_samples"] = len(metrics_list)
        aggregated[mood] = agg
    
    return aggregated


def style_divergence_score(styles: Dict[str, dict]) -> Tuple[float, str]:
    """Score how different output styles are across moods."""
    if len(styles) < 2:
        return 0.0, "Not enough style data (need text samples from at least 2 moods)"
    
    # Compare key metrics across moods
    metrics_to_compare = ["avg_sentence_length", "question_frequency", "emoji_count", 
                          "avg_word_length", "unique_word_ratio"]
    
    total_variance = 0
    metric_details = []
    
    for metric in metrics_to_compare:
        values = {mood: s.get(metric, 0) for mood, s in styles.items()}
        if not values:
            continue
        mean = sum(values.values()) / len(values)
        if mean == 0:
            continue
        variance = sum((v - mean) ** 2 for v in values.values()) / len(values)
        cv = math.sqrt(variance) / mean if mean != 0 else 0  # Coefficient of variation
        total_variance += cv
        
        sorted_moods = sorted(values.items(), key=lambda x: x[1])
        metric_details.append(
            f"  {metric}: lowest={sorted_moods[0][0]} ({sorted_moods[0][1]:.1f}), "
            f"highest={sorted_moods[-1][0]} ({sorted_moods[-1][1]:.1f}), CV={cv:.2f}"
        )
    
    # Normalize: CV of 0.3+ per metric is meaningful difference
    score = min(100, (total_variance / max(len(metrics_to_compare), 1)) * 200)
    
    explanation = "Style variation by metric (Coefficient of Variation):\n" + "\n".join(metric_details)
    
    return round(score, 1), explanation


# ---------------------------------------------------------------------------
# 3. Self-Report Calibration
# ---------------------------------------------------------------------------

def compute_calibration(entries: List[dict]) -> Tuple[float, str]:
    """
    Compare self-reported energy/vibe with objective proxies.
    Proxy: summary length (more words = higher energy?), 
           summary sentiment markers.
    """
    if len(entries) < 5:
        return 0.0, f"Not enough data ({len(entries)} entries, need 5+)"
    
    energy_lengths = {"high": [], "neutral": [], "low": []}
    vibe_lengths = {"positive": [], "neutral": [], "negative": []}
    
    for entry in entries:
        summary = entry.get("summary", "")
        energy = entry.get("energy", "neutral")
        vibe = entry.get("vibe", "neutral")
        word_count = len(summary.split())
        
        if energy in energy_lengths:
            energy_lengths[energy].append(word_count)
        if vibe in vibe_lengths:
            vibe_lengths[vibe].append(word_count)
    
    details = []
    calibration_signals = 0
    total_signals = 0
    
    # Check: high energy → more words?
    for level, lengths in energy_lengths.items():
        if lengths:
            avg = sum(lengths) / len(lengths)
            details.append(f"  Energy={level}: avg summary length {avg:.0f} words (n={len(lengths)})")
    
    high_avg = sum(energy_lengths["high"]) / max(len(energy_lengths["high"]), 1)
    low_avg = sum(energy_lengths["low"]) / max(len(energy_lengths["low"]), 1) if energy_lengths["low"] else high_avg
    
    if energy_lengths["high"] and energy_lengths["low"]:
        total_signals += 1
        if high_avg > low_avg:
            calibration_signals += 1
            details.append("  ✓ High energy produces longer summaries than low energy")
        else:
            details.append("  ✗ High energy does NOT produce longer summaries — possible miscalibration")
    
    # Check: positive vibe → more words?
    pos_avg = sum(vibe_lengths["positive"]) / max(len(vibe_lengths["positive"]), 1)
    neg_avg = sum(vibe_lengths["negative"]) / max(len(vibe_lengths["negative"]), 1) if vibe_lengths["negative"] else 0
    
    # Check all self-reports aren't identical
    all_energy = [e.get("energy", "") for e in entries]
    all_vibe = [e.get("vibe", "") for e in entries]
    energy_diversity = len(set(all_energy))
    vibe_diversity = len(set(all_vibe))
    
    total_signals += 2
    if energy_diversity >= 2:
        calibration_signals += 1
        details.append(f"  ✓ Energy diversity: {energy_diversity} different levels reported")
    else:
        details.append(f"  ✗ Energy always '{all_energy[0]}' — self-report may be autopilot")
    
    if vibe_diversity >= 2:
        calibration_signals += 1
        details.append(f"  ✓ Vibe diversity: {vibe_diversity} different levels reported")
    else:
        details.append(f"  ✗ Vibe always '{all_vibe[0]}' — self-report may be autopilot")
    
    score = (calibration_signals / max(total_signals, 1)) * 100
    explanation = "Self-report calibration:\n" + "\n".join(details)
    
    return round(score, 1), explanation


# ---------------------------------------------------------------------------
# 4. Surprise Index
# ---------------------------------------------------------------------------

def compute_surprise_index(data: dict) -> Tuple[float, str]:
    """
    How often does behavior diverge from the most likely action for that mood?
    High surprise = genuine emergence. Low surprise = deterministic.
    """
    entries = load_history()
    if len(entries) < 10:
        return 0.0, f"Not enough history ({len(entries)} entries, need 10+)"
    
    # Build mood → most common category
    mood_categories = defaultdict(list)
    for entry in entries:
        mood = entry.get("mood", "unknown").lower()
        category = categorize_thought(entry.get("thought_id", ""))
        mood_categories[mood].append(category)
    
    # For each entry, was it the most common action for that mood?
    surprises = 0
    total = 0
    
    for mood, categories in mood_categories.items():
        if len(categories) < 3:
            continue
        most_common = Counter(categories).most_common(1)[0][0]
        for cat in categories:
            total += 1
            if cat != most_common:
                surprises += 1
    
    if total == 0:
        return 0.0, "Not enough data to compute surprise"
    
    surprise_rate = surprises / total
    # 0% surprise = completely predictable (bad)
    # 50% surprise = good balance
    # 100% surprise = pure random (also bad)
    # Optimal is around 40-60%
    score = 100 - abs(surprise_rate - 0.5) * 200
    score = max(0, score)
    
    explanation = (
        f"Surprise rate: {surprise_rate:.1%} of actions were NOT the most common for their mood\n"
        f"  (Optimal: 40-60%. Below 20% = too predictable. Above 80% = too random)\n"
        f"  Total measured actions: {total}"
    )
    
    return round(score, 1), explanation


# ---------------------------------------------------------------------------
# Real-time Genuineness Check (Issue #8)
# ---------------------------------------------------------------------------

# Performative phrase patterns — things that sound good but mean nothing
VIRTUE_SIGNAL_PHRASES = [
    "just wanted to share",
    "thought you might",
    "hope this helps",
    "spreading positivity",
    "making the world",
    "giving back",
    "pay it forward",
    "random act of kindness",
]

EMPTY_PROMISE_PHRASES = [
    "i'll definitely",
    "going to start",
    "planning to",
    "will absolutely",
    "committed to",
    "promise to",
    "from now on",
]

ENGAGEMENT_BAIT_PHRASES = [
    "what do you think",
    "am i right",
    "hot take",
    "unpopular opinion",
    "controversial but",
    "let that sink in",
    "change my mind",
    "who else",
]

# Mood ↔ thought coherence map: which thought categories feel genuine per mood
MOOD_THOUGHT_COHERENCE = {
    'chaotic':       {'explore': 0.9, 'reflect': 0.8, 'build': 0.5, 'social': 0.4, 'pitch': 0.7},
    'cozy':          {'reflect': 0.9, 'social': 0.7, 'explore': 0.5, 'build': 0.4, 'pitch': 0.3},
    'philosophical': {'reflect': 0.9, 'explore': 0.7, 'build': 0.5, 'social': 0.4, 'pitch': 0.6},
    'hyperfocus':    {'build': 0.9, 'explore': 0.6, 'reflect': 0.3, 'social': 0.2, 'pitch': 0.4},
    'social':        {'social': 0.9, 'pitch': 0.7, 'reflect': 0.5, 'explore': 0.4, 'build': 0.3},
    'restless':      {'explore': 0.9, 'build': 0.7, 'pitch': 0.6, 'social': 0.5, 'reflect': 0.2},
    'nocturnal':     {'reflect': 0.9, 'explore': 0.7, 'build': 0.6, 'social': 0.3, 'pitch': 0.4},
    'creative':      {'reflect': 0.8, 'explore': 0.8, 'build': 0.7, 'pitch': 0.6, 'social': 0.5},
}

GENUINENESS_FILTER_LOG = SCRIPT_DIR / "log" / "genuineness_filter.log"


def _detect_performative_phrases(text: str) -> List[Tuple[str, str]]:
    """
    Scan text for performative patterns.
    Returns list of (phrase_found, category).
    """
    text_lower = text.lower()
    hits = []
    for phrase in VIRTUE_SIGNAL_PHRASES:
        if phrase in text_lower:
            hits.append((phrase, "virtue_signal"))
    for phrase in EMPTY_PROMISE_PHRASES:
        if phrase in text_lower:
            hits.append((phrase, "empty_promise"))
    for phrase in ENGAGEMENT_BAIT_PHRASES:
        if phrase in text_lower:
            hits.append((phrase, "engagement_bait"))
    return hits


def _check_repetition(thought_id: str, lookback: int = 10) -> Tuple[float, str]:
    """
    Check how recently this thought was picked.
    Returns (penalty 0-0.4, reason).
    """
    history = load_history()
    if not history:
        return 0.0, ""

    recent = history[-lookback:]
    recent_ids = [e.get("thought_id", "") for e in recent]
    count = recent_ids.count(thought_id)

    if count == 0:
        return 0.0, ""
    elif count == 1:
        return 0.1, f"'{thought_id}' picked once in last {lookback} actions"
    elif count == 2:
        return 0.25, f"'{thought_id}' picked twice in last {lookback} — getting repetitive"
    else:
        return 0.4, f"'{thought_id}' picked {count}x in last {lookback} — engagement rut"


def _mood_coherence_score(thought_id: str, mood_name: str) -> Tuple[float, str]:
    """
    Score how coherent this thought category is with the current mood.
    Returns (score 0-1, reason).
    """
    category = categorize_thought(thought_id)

    # Find matching mood key
    matched_mood = None
    for mood_key in MOOD_THOUGHT_COHERENCE:
        if mood_key in mood_name:
            matched_mood = mood_key
            break

    if not matched_mood:
        return 0.5, f"No coherence data for mood '{mood_name}'"

    coherence = MOOD_THOUGHT_COHERENCE[matched_mood].get(category, 0.5)
    if coherence >= 0.7:
        reason = f"'{category}' is a natural fit for {mood_name} mood"
    elif coherence <= 0.3:
        reason = f"'{category}' feels forced in {mood_name} mood"
    else:
        reason = f"'{category}' is neutral for {mood_name} mood"

    return coherence, reason


def _log_filter_result(thought_id: str, score: float, reasons: List[str],
                       mood_name: str, filtered: bool):
    """Append a line to the genuineness filter log."""
    try:
        GENUINENESS_FILTER_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat()
        status = "FILTERED" if filtered else "PASSED"
        reason_str = "; ".join(reasons) if reasons else "no flags"
        line = f"{ts} | {status} | {thought_id} | score={score:.2f} | mood={mood_name} | {reason_str}\n"
        with open(GENUINENESS_FILTER_LOG, "a") as f:
            f.write(line)
    except Exception:
        pass  # Never crash the pipeline over logging


def check_genuineness(thought_prompt: str, mood: dict,
                      thought_id: str = "") -> Tuple[float, str]:
    """
    Analyse a thought/action candidate for performative behaviour.

    Scoring (0-1):
      - Start at 0.7 (benefit of the doubt)
      - Subtract for performative phrases, repetition, mood incoherence
      - Add small bonus for mood-aligned content

    Returns (genuineness_score 0-1, explanation).
    """
    if not mood or not thought_prompt:
        return 0.5, "Insufficient data"

    mood_name = mood.get('name', '').lower()
    reasons: List[str] = []
    score = 0.7

    # --- 1. Performative phrase detection ---
    hits = _detect_performative_phrases(thought_prompt)
    if hits:
        penalty = min(0.3, len(hits) * 0.1)
        score -= penalty
        categories_hit = set(cat for _, cat in hits)
        reasons.append(f"performative phrases ({', '.join(categories_hit)})")

    # --- 2. Repetition check ---
    if thought_id:
        rep_penalty, rep_reason = _check_repetition(thought_id)
        if rep_penalty > 0:
            score -= rep_penalty
            reasons.append(rep_reason)

    # --- 3. Mood ↔ thought coherence ---
    if thought_id:
        coherence, coh_reason = _mood_coherence_score(thought_id, mood_name)
        # Shift score toward coherence value (±0.15 max)
        adjustment = (coherence - 0.5) * 0.3
        score += adjustment
        if abs(adjustment) > 0.05:
            reasons.append(coh_reason)

    # --- 4. Keyword alignment (legacy, lighter weight) ---
    prompt_lower = thought_prompt.lower()
    performative_kw = {
        'chaotic': ['organize', 'systematic', 'methodical'],
        'cozy': ['aggressive', 'disruptive'],
        'philosophical': ['quick', 'fast', 'minimal'],
        'hyperfocus': ['casual', 'random', 'distract'],
        'social': ['alone', 'isolate'],
        'restless': ['slow', 'patient', 'wait'],
    }
    genuine_kw = {
        'chaotic': ['creative', 'experiment', 'new'],
        'cozy': ['comfortable', 'gentle', 'warm'],
        'philosophical': ['deep', 'meaning', 'reflect'],
        'hyperfocus': ['build', 'focus', 'concentrate'],
        'social': ['share', 'connect', 'interact'],
        'restless': ['energy', 'action', 'move'],
    }
    for mood_key in performative_kw:
        if mood_key in mood_name:
            for word in performative_kw[mood_key]:
                if word in prompt_lower:
                    score -= 0.1
                    reasons.append(f"'{word}' conflicts with {mood_name}")
            for word in genuine_kw.get(mood_key, []):
                if word in prompt_lower:
                    score += 0.05
                    reasons.append(f"'{word}' aligns with {mood_name}")

    score = max(0.0, min(1.0, score))
    filtered = score < 0.3

    # Log every check
    _log_filter_result(thought_id or "unknown", score, reasons, mood_name, filtered)

    explanation = f"{mood_name} mood | Score: {score:.2f}"
    if reasons:
        explanation += f" | {'; '.join(reasons[:3])}"

    return score, explanation


# ---------------------------------------------------------------------------
# Tracking — called during normal operation
# ---------------------------------------------------------------------------

def track_entry(mood: str, thought_id: str, summary: str, energy: str, vibe: str,
                output_text: str = ""):
    """
    Record a genuineness data point. Called by log_result.sh after each action.
    """
    data = load_genuineness_data()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "mood": mood,
        "thought_id": thought_id,
        "category": categorize_thought(thought_id),
        "energy": energy,
        "vibe": vibe,
        "summary_length": len(summary.split()),
    }
    data["entries"].append(entry)
    
    # Track style if output text provided
    if output_text:
        style_sample = {
            "timestamp": datetime.now().isoformat(),
            "mood": mood,
            "metrics": analyze_text_style(output_text),
        }
        data["style_samples"].append(style_sample)
    
    save_genuineness_data(data)
    return entry


# ---------------------------------------------------------------------------
# Overall Score
# ---------------------------------------------------------------------------

def compute_genuineness_score() -> dict:
    """Compute overall genuineness score from all dimensions."""
    history = load_history()
    gen_data = load_genuineness_data()
    
    # 1. Action distribution
    distributions = compute_action_distribution(history)
    action_score, action_detail = action_distribution_score(distributions)
    
    # 2. Style analysis
    styles = compute_style_by_mood(gen_data)
    style_score, style_detail = style_divergence_score(styles)
    
    # 3. Self-report calibration
    calibration_score, calibration_detail = compute_calibration(history)
    
    # 4. Surprise index
    surprise_score, surprise_detail = compute_surprise_index(gen_data)
    
    # Weighted average (action distribution matters most)
    weights = {
        "action_distribution": 0.35,
        "output_style": 0.25,
        "self_report_calibration": 0.20,
        "surprise_index": 0.20,
    }
    
    scores = {
        "action_distribution": action_score,
        "output_style": style_score,
        "self_report_calibration": calibration_score,
        "surprise_index": surprise_score,
    }
    
    # Only weight dimensions that have data
    active_weights = {k: v for k, v in weights.items() if scores[k] > 0}
    if active_weights:
        total_weight = sum(active_weights.values())
        overall = sum(scores[k] * active_weights[k] / total_weight for k in active_weights)
    else:
        overall = 0
    
    data_status = "insufficient" if len(history) < 10 else "developing" if len(history) < 50 else "stable"
    
    return {
        "overall_score": round(overall, 1),
        "data_status": data_status,
        "history_entries": len(history),
        "dimensions": {
            "action_distribution": {
                "score": action_score,
                "weight": weights["action_distribution"],
                "detail": action_detail,
                "data": distributions,
            },
            "output_style": {
                "score": style_score,
                "weight": weights["output_style"],
                "detail": style_detail,
            },
            "self_report_calibration": {
                "score": calibration_score,
                "weight": weights["self_report_calibration"],
                "detail": calibration_detail,
            },
            "surprise_index": {
                "score": surprise_score,
                "weight": weights["surprise_index"],
                "detail": surprise_detail,
            },
        },
        "interpretation": interpret_score(overall, data_status),
    }


def interpret_score(score: float, data_status: str) -> str:
    """Human-readable interpretation of genuineness score."""
    if data_status == "insufficient":
        return (
            "⏳ INSUFFICIENT DATA — The system is too new to measure genuineness. "
            "Need at least 10 logged actions across multiple moods. Keep running "
            "and check back in a few days."
        )
    
    if score >= 80:
        return (
            "🟢 HIGH GENUINENESS — Moods are producing measurably different behavior "
            "patterns, output styles, and surprise levels. The mood system appears to "
            "be genuinely influencing agent behavior, not just labeling it."
        )
    elif score >= 50:
        return (
            "🟡 MODERATE GENUINENESS — Some behavioral differences across moods are "
            "detectable, but they're subtle. The mood system is partially influencing "
            "behavior. Consider whether the differences are meaningful or cosmetic."
        )
    elif score >= 20:
        return (
            "🟠 LOW GENUINENESS — Minimal behavioral differences across moods. The "
            "agent does roughly the same things regardless of mood state. The mood "
            "system may be decorative. Investigate which dimensions score lowest."
        )
    else:
        return (
            "🔴 NEGLIGIBLE GENUINENESS — No measurable difference in behavior across "
            "moods. The mood system is almost certainly cosmetic — just changing labels "
            "on identical behavior. Consider redesigning how moods influence action "
            "selection, or accept that the current system is theatrical."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_report(as_json: bool = False):
    """Print full genuineness report."""
    result = compute_genuineness_score()
    
    if as_json:
        print(json.dumps(result, indent=2))
        return
    
    print("=" * 60)
    print("🔍 GENUINENESS REPORT")
    print("=" * 60)
    print()
    print(f"Overall Score: {result['overall_score']}/100")
    print(f"Data Status: {result['data_status']} ({result['history_entries']} entries)")
    print()
    print(result["interpretation"])
    print()
    
    for name, dim in result["dimensions"].items():
        label = name.replace("_", " ").title()
        print(f"--- {label} (weight: {dim['weight']:.0%}) ---")
        print(f"Score: {dim['score']}/100")
        print(dim["detail"])
        print()


def print_distribution(as_json: bool = False):
    """Print action distribution per mood."""
    history = load_history()
    distributions = compute_action_distribution(history)
    
    if as_json:
        print(json.dumps(distributions, indent=2))
        return
    
    if not distributions:
        print("No action data yet.")
        return
    
    print("Action Distribution by Mood:")
    print()
    for mood, dist in sorted(distributions.items()):
        total = dist.pop("_total", 0)
        print(f"  {mood} (n={total}):")
        for cat, pct in sorted(dist.items(), key=lambda x: -x[1]):
            bar = "█" * int(pct / 5)
            print(f"    {cat:12s} {pct:5.1f}% {bar}")
        print()


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    
    command = args[0] if args else "report"
    
    if command == "report":
        print_report(as_json)
    elif command == "score":
        result = compute_genuineness_score()
        if as_json:
            print(json.dumps({"score": result["overall_score"], "status": result["data_status"]}))
        else:
            print(f"Genuineness Score: {result['overall_score']}/100 ({result['data_status']})")
            print(result["interpretation"])
    elif command == "distribution":
        print_distribution(as_json)
    elif command == "style":
        gen_data = load_genuineness_data()
        styles = compute_style_by_mood(gen_data)
        if as_json:
            print(json.dumps(styles, indent=2))
        else:
            score, detail = style_divergence_score(styles)
            print(f"Style Divergence Score: {score}/100")
            print(detail)
    elif command == "calibration":
        history = load_history()
        score, detail = compute_calibration(history)
        if as_json:
            print(json.dumps({"score": score, "detail": detail}))
        else:
            print(f"Calibration Score: {score}/100")
            print(detail)
    elif command == "filter-log":
        # Show recent genuineness filter decisions
        if not GENUINENESS_FILTER_LOG.exists():
            print("No filter log yet.")
            sys.exit(0)
        lines = GENUINENESS_FILTER_LOG.read_text().strip().split("\n")
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 20
        for line in lines[-n:]:
            print(line)
    elif command == "check":
        # Manual check: genuineness.py check <thought_id> <prompt_text>
        if len(args) < 3:
            print("Usage: genuineness.py check <thought_id> <prompt_text>")
            sys.exit(1)
        thought_id = args[1]
        prompt_text = " ".join(args[2:])
        # Load current mood
        mood = {}
        try:
            import json as _json
            with open(DATA_DIR / "today_mood.json") as f:
                mood = _json.load(f)
        except Exception:
            pass
        score, reason = check_genuineness(prompt_text, mood, thought_id=thought_id)
        if as_json:
            print(json.dumps({"thought_id": thought_id, "score": score, "reason": reason,
                              "would_filter": score < 0.3}))
        else:
            status = "🚫 FILTERED" if score < 0.3 else "✅ PASSED"
            print(f"{status} | {thought_id} | score={score:.2f} | {reason}")
    elif command == "track":
        # track <mood> <thought_id> <summary> <energy> <vibe> [output_text]
        if len(args) < 6:
            print("Usage: genuineness.py track <mood> <thought_id> <summary> <energy> <vibe> [output_text]")
            sys.exit(1)
        entry = track_entry(args[1], args[2], args[3], args[4], args[5],
                          args[6] if len(args) > 6 else "")
        if as_json:
            print(json.dumps(entry, indent=2))
        else:
            print(f"Tracked: {entry['mood']}/{entry['category']} ({entry['energy']}/{entry['vibe']})")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
