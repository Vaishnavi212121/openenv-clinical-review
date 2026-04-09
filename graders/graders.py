"""
Task Graders for Clinical Trial Review Environment
Each grader produces a score in [0.0, 1.0] using deterministic criteria.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, TYPE_CHECKING
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from models import ProtocolFlag, TaskResult

# ─── Score Clamping Utility ──────────────────────────────────────────────────

def clamp_score(score: float) -> float:
    """
    Ensures score is strictly between 0 and 1 (0 < score < 1).
    Validator requires scores to not be exactly 0.0 or 1.0.
    """
    return max(0.001, min(0.999, score))

# ─── Matching Utilities ────────────────────────────────────────────────────────

CATEGORY_ALIASES = {
    "missing_element": ["missing", "absent", "not provided", "not specified", "incomplete", "omitted"],
    "eligibility_conflict": ["conflict", "eligibility", "inclusion", "exclusion", "ambiguous criteria"],
    "safety_gap": ["safety", "monitoring", "risk", "adverse", "toxicity"],
    "dosing_error": ["dose", "dosing", "pharmacokinetic", "pk"],
    "consent_violation": ["consent", "assent", "informed"],
    "statistical_flaw": ["statistical", "analysis", "sample size", "endpoint", "multiplicity", "power"],
    "regulatory_noncompliance": ["regulatory", "compliance", "fda", "ich", "ema", "guideline"],
}

SEVERITY_WEIGHTS = {
    "critical": 1.0,
    "major": 0.6,
    "minor": 0.25,
}

def _text_similarity(a: str, b: str) -> float:
    a, b = a.lower().strip(), b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()

def _category_match(flag_category: str, gt_category: str) -> bool:
    if flag_category == gt_category:
        return True
    aliases = CATEGORY_ALIASES.get(gt_category, [])
    flag_lower = flag_category.lower()
    return any(alias in flag_lower for alias in aliases)

def _location_match(flag_location: str, gt_location: str) -> bool:
    return gt_location.lower() in flag_location.lower() or \
           flag_location.lower() in gt_location.lower()

def _description_match(flag_desc: str, gt_desc: str) -> float:
    gt_keywords = set(w.lower() for w in gt_desc.split() if len(w) > 4)
    flag_words = flag_desc.lower()
    if not gt_keywords:
        return 0.5
    keyword_hits = sum(1 for kw in gt_keywords if kw in flag_words)
    keyword_score = keyword_hits / len(gt_keywords)
    similarity = _text_similarity(flag_desc, gt_desc)
    return max(keyword_score, similarity * 0.8)

def _match_flag_to_gt(flag: ProtocolFlag, ground_truth_issues: List[Dict[str, Any]]) -> Tuple[str | None, float]:
    best_match_id = None
    best_score = 0.0
    for gt in ground_truth_issues:
        if not _location_match(flag.location, gt["location"]):
            continue
        if not _category_match(flag.category, gt["category"]):
            continue
        desc_score = _description_match(flag.description, gt["description"])
        sev_score = 1.0 if flag.severity == gt["severity"] else 0.7
        combined = 0.4 + (desc_score * 0.4) + (sev_score * 0.2)
        if combined > best_score:
            best_score = combined
            best_match_id = gt["issue_id"]
    return best_match_id, best_score

# ─── Base Grader ──────────────────────────────────────────────────────────────

class BaseGrader:
    def grade(self, **kwargs) -> Any:
        raise NotImplementedError

# ─── Task 1: Easy ─────────────────────────────────────────────────────────────

class EasyGrader(BaseGrader):
    def grade(self, task_id, flags_raised, ground_truth_issues, steps_used, 
              max_steps, sections_reviewed, all_sections, submitted) -> Any:
        from models import TaskResult
        target_issues = [g for g in ground_truth_issues if g["category"] == "missing_element"]
        matched_ids = set()
        match_scores = {}
        false_positives = 0

        for flag in flags_raised:
            match_id, quality = _match_flag_to_gt(flag, target_issues)
            if match_id and match_id not in matched_ids:
                matched_ids.add(match_id)
                match_scores[match_id] = quality
            elif not match_id:
                false_positives += 1

        total_weight = sum(SEVERITY_WEIGHTS.get(g["severity"], 0.5) for g in target_issues)
        found_weight = sum(SEVERITY_WEIGHTS.get(next(g["severity"] for g in target_issues if g["issue_id"] == mid), 0.5) * match_scores[mid] for mid in matched_ids)
        recall_score = found_weight / total_weight if total_weight > 0 else 0.0
        precision_score = (len(flags_raised) - false_positives) / len(flags_raised) if flags_raised else 0.0
        efficiency_bonus = max(0.0, 0.2 * (1.0 - (steps_used / max_steps))) if submitted else 0.0
        coverage_bonus = 0.1 * (len(sections_reviewed) / len(all_sections))

        # FINAL SCORE CLAMPING
        score = clamp_score(0.70 * recall_score + 0.15 * precision_score + efficiency_bonus + coverage_bonus)

        return TaskResult(
            task_id=task_id, score=round(score, 4), true_positives=len(matched_ids),
            false_positives=false_positives, false_negatives=len(target_issues) - len(matched_ids),
            critical_issues_found=sum(1 for mid in matched_ids if any(g["issue_id"] == mid and g["severity"] == "critical" for g in target_issues)),
            critical_issues_total=sum(1 for g in target_issues if g["severity"] == "critical"),
            steps_used=steps_used, max_steps=max_steps, efficiency_bonus=efficiency_bonus,
            final_reward=score, passed=score >= 0.6, breakdown={}
        )

# ─── Task 2: Medium ───────────────────────────────────────────────────────────

class MediumGrader(BaseGrader):
    TARGET_CATEGORIES = {"eligibility_conflict", "statistical_flaw", "missing_element"}
    def grade(self, task_id, flags_raised, ground_truth_issues, steps_used,
              max_steps, sections_reviewed, all_sections, submitted) -> Any:
        from models import TaskResult
        target_issues = [g for g in ground_truth_issues if g["category"] in self.TARGET_CATEGORIES]
        category_scores, matched_ids, false_positives = {}, set(), 0

        for cat in self.TARGET_CATEGORIES:
            cat_gt = [g for g in target_issues if g["category"] == cat]
            if not cat_gt:
                category_scores[cat] = 1.0; continue
            cat_flags = [f for f in flags_raised if _category_match(f.category, cat)]
            cat_matched = set()
            for flag in cat_flags:
                match_id, quality = _match_flag_to_gt(flag, cat_gt)
                if match_id and match_id not in matched_ids:
                    cat_matched.add(match_id); matched_ids.add(match_id)
                elif not match_id: false_positives += 1
            total_w = sum(SEVERITY_WEIGHTS.get(g["severity"], 0.5) for g in cat_gt)
            found_w = sum(SEVERITY_WEIGHTS.get(next(g["severity"] for g in cat_gt if g["issue_id"] == mid), 0.5) for mid in cat_matched)
            category_scores[cat] = found_w / total_w if total_w > 0 else 0.0

        avg_cat_score = sum(category_scores.values()) / len(category_scores)
        multi_cat_bonus = 0.1 if all(category_scores.get(c, 0) > 0 for c in ["eligibility_conflict", "statistical_flaw"]) else 0.0
        precision_penalty = 0.15 * (false_positives / len(flags_raised) if flags_raised else 0.0)
        efficiency_bonus = max(0.0, 0.15 * (1.0 - (steps_used / max_steps))) if submitted else 0.0

        # FINAL SCORE CLAMPING
        score = clamp_score(avg_cat_score * 0.75 + multi_cat_bonus + efficiency_bonus - precision_penalty)

        return TaskResult(
            task_id=task_id, score=round(score, 4), true_positives=len(matched_ids),
            false_positives=false_positives, false_negatives=len(target_issues) - len(matched_ids),
            critical_issues_found=sum(1 for mid in matched_ids if any(g["issue_id"] == mid and g["severity"] == "critical" for g in target_issues)),
            critical_issues_total=sum(1 for g in target_issues if g["severity"] == "critical"),
            steps_used=steps_used, max_steps=max_steps, efficiency_bonus=efficiency_bonus,
            final_reward=score, passed=score >= 0.55, breakdown={}
        )

# ─── Task 3: Hard ─────────────────────────────────────────────────────────────

class HardGrader(BaseGrader):
    def grade(self, task_id, flags_raised, ground_truth_issues, steps_used,
              max_steps, sections_reviewed, all_sections, submitted) -> Any:
        from models import TaskResult
        matched_ids, match_scores, false_positives = set(), {}, 0
        for flag in flags_raised:
            match_id, quality = _match_flag_to_gt(flag, ground_truth_issues)
            if match_id and match_id not in matched_ids:
                matched_ids.add(match_id); match_scores[match_id] = quality
            elif not match_id: false_positives += 1

        def issue_weight(issue: Dict[str, Any]) -> float:
            return SEVERITY_WEIGHTS.get(issue["severity"], 0.5) * (3.0 if issue["severity"] == "critical" else 1.0)

        total_weight = sum(issue_weight(g) for g in ground_truth_issues)
        found_weight = sum(issue_weight(next(g for g in ground_truth_issues if g["issue_id"] == mid)) * match_scores[mid] for mid in matched_ids)
        weighted_recall = found_weight / total_weight if total_weight > 0 else 0.0
        critical_gt = [g for g in ground_truth_issues if g["severity"] == "critical"]
        critical_found = sum(1 for mid in matched_ids if any(g["issue_id"] == mid for g in critical_gt))
        missed_critical_penalty = 0.08 * (len(critical_gt) - critical_found)
        coverage_score = min(1.0, (len(sections_reviewed) / len(all_sections)) * 1.2)
        precision_penalty = 0.2 * (false_positives / len(flags_raised) if flags_raised else 0.0)
        efficiency_bonus = max(0.0, 0.1 * (1.0 - (steps_used/max_steps))) if submitted else 0.0
        submission_penalty = 0.15 if not submitted else 0.0

        # FINAL SCORE CLAMPING
        score = clamp_score(0.60 * weighted_recall + 0.20 * coverage_score + efficiency_bonus - missed_critical_penalty - precision_penalty - submission_penalty)

        return TaskResult(
            task_id=task_id, score=round(score, 4), true_positives=len(matched_ids),
            false_positives=false_positives, false_negatives=len(ground_truth_issues) - len(matched_ids),
            critical_issues_found=critical_found, critical_issues_total=len(critical_gt),
            steps_used=steps_used, max_steps=max_steps, efficiency_bonus=efficiency_bonus,
            final_reward=score, passed=score >= 0.45, breakdown={}
        )

# ─── Grader Registry ──────────────────────────────────────────────────────────

GRADERS = {
    "task_easy": EasyGrader(),
    "task_medium": MediumGrader(),
    "task_hard": HardGrader(),
}

def get_grader(task_id: str) -> BaseGrader:
    if task_id not in GRADERS:
        raise ValueError(f"Unknown task_id: {task_id}")
    return GRADERS[task_id]
