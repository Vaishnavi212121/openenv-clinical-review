"""
Task Graders for Clinical Trial Review Environment
Each grader produces a score in [0.0, 1.0] using deterministic criteria.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
from difflib import SequenceMatcher

from env.models import ProtocolFlag, FlagCategory, FlagSeverity, TaskResult


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
    """Fuzzy text similarity between two strings."""
    a, b = a.lower().strip(), b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()


def _category_match(flag_category: str, gt_category: str) -> bool:
    """Check if raised flag category matches ground truth (with fuzzy matching)."""
    if flag_category == gt_category:
        return True
    aliases = CATEGORY_ALIASES.get(gt_category, [])
    flag_lower = flag_category.lower()
    return any(alias in flag_lower for alias in aliases)


def _location_match(flag_location: str, gt_location: str) -> bool:
    """Check if the flag was raised in the correct section."""
    return gt_location.lower() in flag_location.lower() or \
           flag_location.lower() in gt_location.lower()


def _description_match(flag_desc: str, gt_desc: str) -> float:
    """Partial credit for description quality (0.0 to 1.0)."""
    # Extract key terms from ground truth
    gt_keywords = set(w.lower() for w in gt_desc.split() if len(w) > 4)
    flag_words = flag_desc.lower()
    
    if not gt_keywords:
        return 0.5
    
    keyword_hits = sum(1 for kw in gt_keywords if kw in flag_words)
    keyword_score = keyword_hits / len(gt_keywords)
    
    similarity = _text_similarity(flag_desc, gt_desc)
    
    return max(keyword_score, similarity * 0.8)


def _match_flag_to_gt(
    flag: ProtocolFlag, 
    ground_truth_issues: List[Dict[str, Any]]
) -> Tuple[str | None, float]:
    """
    Match a raised flag to a ground truth issue.
    Returns (issue_id, match_quality_0_to_1) or (None, 0.0)
    """
    best_match_id = None
    best_score = 0.0

    for gt in ground_truth_issues:
        # Must match location (section)
        if not _location_match(flag.location, gt["location"]):
            continue

        # Category match (required for credit)
        cat_ok = _category_match(flag.category, gt["category"])
        if not cat_ok:
            cat_ok = _category_match(flag.category, gt["category"])
            if not cat_ok:
                continue

        # Description quality gives partial credit
        desc_score = _description_match(flag.description, gt["description"])

        # Severity alignment
        sev_score = 1.0 if flag.severity == gt["severity"] else 0.7

        combined = 0.4 + (desc_score * 0.4) + (sev_score * 0.2)
        if combined > best_score:
            best_score = combined
            best_match_id = gt["issue_id"]

    return best_match_id, best_score


# ─── Base Grader ──────────────────────────────────────────────────────────────

class BaseGrader:
    """Base class for all task graders."""

    def grade(
        self,
        task_id: str,
        flags_raised: List[ProtocolFlag],
        ground_truth_issues: List[Dict[str, Any]],
        steps_used: int,
        max_steps: int,
        sections_reviewed: List[str],
        all_sections: List[str],
        submitted: bool,
    ) -> TaskResult:
        raise NotImplementedError


# ─── Task 1: Easy — Missing Elements Check ────────────────────────────────────

class EasyGrader(BaseGrader):
    """
    Task: Identify all MISSING_ELEMENT issues in a Phase I protocol.
    Scoring:
    - 70% weighted recall of true issues (weighted by severity)
    - 15% precision (penalize false positives)
    - 15% efficiency bonus (finding issues quickly)
    """

    def grade(self, task_id, flags_raised, ground_truth_issues, steps_used, 
              max_steps, sections_reviewed, all_sections, submitted) -> TaskResult:
        
        # Filter to missing_element gt issues
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

        # Weighted recall (critical=1.0, major=0.6, minor=0.25)
        total_weight = sum(SEVERITY_WEIGHTS.get(g["severity"], 0.5) for g in target_issues)
        found_weight = sum(
            SEVERITY_WEIGHTS.get(next(g["severity"] for g in target_issues if g["issue_id"] == mid), 0.5)
            * match_scores[mid]
            for mid in matched_ids
        )
        recall_score = found_weight / total_weight if total_weight > 0 else 0.0

        # Precision
        total_flags = len(flags_raised)
        precision_score = (total_flags - false_positives) / total_flags if total_flags > 0 else 0.0

        # Efficiency
        step_ratio = steps_used / max_steps
        efficiency_bonus = max(0.0, 0.2 * (1.0 - step_ratio)) if submitted else 0.0

        # Coverage bonus (reviewed enough sections)
        coverage = len(sections_reviewed) / len(all_sections)
        coverage_bonus = 0.1 * coverage

        # Final score
        score = 0.70 * recall_score + 0.15 * precision_score + efficiency_bonus + coverage_bonus
        score = min(1.0, max(0.0, score))

        critical_found = sum(1 for mid in matched_ids 
                            if any(g["issue_id"] == mid and g["severity"] == "critical" 
                                  for g in target_issues))
        critical_total = sum(1 for g in target_issues if g["severity"] == "critical")

        return TaskResult(
            task_id=task_id,
            score=round(score, 4),
            true_positives=len(matched_ids),
            false_positives=false_positives,
            false_negatives=len(target_issues) - len(matched_ids),
            critical_issues_found=critical_found,
            critical_issues_total=critical_total,
            steps_used=steps_used,
            max_steps=max_steps,
            efficiency_bonus=efficiency_bonus,
            final_reward=score,
            passed=score >= 0.6,
            breakdown={
                "recall_score": round(recall_score, 4),
                "precision_score": round(precision_score, 4),
                "efficiency_bonus": round(efficiency_bonus, 4),
                "coverage_bonus": round(coverage_bonus, 4),
                "target_issues_count": len(target_issues),
                "matched_issues": list(matched_ids),
            }
        )


# ─── Task 2: Medium — Eligibility & Statistical Conflicts ─────────────────────

class MediumGrader(BaseGrader):
    """
    Task: Find eligibility conflicts AND statistical flaws in a Phase III protocol.
    Scoring:
    - Requires finding both categories to score well
    - Partial credit for each category independently
    - Penalty for false positives (noisier document)
    """

    TARGET_CATEGORIES = {"eligibility_conflict", "statistical_flaw", "missing_element"}

    def grade(self, task_id, flags_raised, ground_truth_issues, steps_used,
              max_steps, sections_reviewed, all_sections, submitted) -> TaskResult:

        target_issues = [g for g in ground_truth_issues 
                        if g["category"] in self.TARGET_CATEGORIES]

        # Score per category
        category_scores = {}
        matched_ids = set()
        false_positives = 0

        for cat in self.TARGET_CATEGORIES:
            cat_gt = [g for g in target_issues if g["category"] == cat]
            if not cat_gt:
                category_scores[cat] = 1.0
                continue

            cat_flags = [f for f in flags_raised if _category_match(f.category, cat)]
            cat_matched = set()

            for flag in cat_flags:
                match_id, quality = _match_flag_to_gt(flag, cat_gt)
                if match_id and match_id not in matched_ids and match_id not in cat_matched:
                    cat_matched.add(match_id)
                    matched_ids.add(match_id)
                elif not match_id:
                    false_positives += 1

            # Weighted recall for this category
            total_w = sum(SEVERITY_WEIGHTS.get(g["severity"], 0.5) for g in cat_gt)
            found_w = sum(
                SEVERITY_WEIGHTS.get(next(g["severity"] for g in cat_gt if g["issue_id"] == mid), 0.5)
                for mid in cat_matched
            )
            category_scores[cat] = found_w / total_w if total_w > 0 else 0.0

        # Require both main categories to have >0 score (task tests multi-category awareness)
        multi_cat_bonus = 0.1 if all(
            category_scores.get(c, 0) > 0 for c in ["eligibility_conflict", "statistical_flaw"]
        ) else 0.0

        # Overall recall
        avg_cat_score = sum(category_scores.values()) / len(category_scores)

        # Precision penalty
        total_flags = len(flags_raised)
        fp_rate = false_positives / total_flags if total_flags > 0 else 0.0
        precision_penalty = 0.15 * fp_rate

        # Efficiency
        step_ratio = steps_used / max_steps
        efficiency_bonus = max(0.0, 0.15 * (1.0 - step_ratio)) if submitted else 0.0

        score = avg_cat_score * 0.75 + multi_cat_bonus + efficiency_bonus - precision_penalty
        score = min(1.0, max(0.0, score))

        critical_found = sum(1 for mid in matched_ids 
                            if any(g["issue_id"] == mid and g["severity"] == "critical" 
                                  for g in target_issues))
        critical_total = sum(1 for g in target_issues if g["severity"] == "critical")

        return TaskResult(
            task_id=task_id,
            score=round(score, 4),
            true_positives=len(matched_ids),
            false_positives=false_positives,
            false_negatives=len(target_issues) - len(matched_ids),
            critical_issues_found=critical_found,
            critical_issues_total=critical_total,
            steps_used=steps_used,
            max_steps=max_steps,
            efficiency_bonus=efficiency_bonus,
            final_reward=score,
            passed=score >= 0.55,
            breakdown={
                "category_scores": {k: round(v, 4) for k, v in category_scores.items()},
                "multi_category_bonus": multi_cat_bonus,
                "precision_penalty": round(precision_penalty, 4),
                "efficiency_bonus": round(efficiency_bonus, 4),
                "avg_category_recall": round(avg_cat_score, 4),
            }
        )


# ─── Task 3: Hard — Full Compliance Audit ─────────────────────────────────────

class HardGrader(BaseGrader):
    """
    Task: Full safety and compliance audit of a complex pediatric adaptive trial.
    All issue categories, all sections. Critical issues carry heavy weight.
    Penalizes: missed criticals, false positives, low coverage, not submitting.
    """

    def grade(self, task_id, flags_raised, ground_truth_issues, steps_used,
              max_steps, sections_reviewed, all_sections, submitted) -> TaskResult:

        matched_ids = set()
        match_scores = {}
        false_positives = 0

        for flag in flags_raised:
            match_id, quality = _match_flag_to_gt(flag, ground_truth_issues)
            if match_id and match_id not in matched_ids:
                matched_ids.add(match_id)
                match_scores[match_id] = quality
            elif not match_id:
                false_positives += 1

        # Weighted recall — critical issues worth 3x
        def issue_weight(issue: Dict[str, Any]) -> float:
            base = SEVERITY_WEIGHTS.get(issue["severity"], 0.5)
            return base * (3.0 if issue["severity"] == "critical" else 1.0)

        total_weight = sum(issue_weight(g) for g in ground_truth_issues)
        found_weight = sum(
            issue_weight(next(g for g in ground_truth_issues if g["issue_id"] == mid))
            * match_scores[mid]
            for mid in matched_ids
        )
        weighted_recall = found_weight / total_weight if total_weight > 0 else 0.0

        # Critical issue penalty — missing a critical is harshly penalized
        critical_gt = [g for g in ground_truth_issues if g["severity"] == "critical"]
        critical_found = sum(1 for mid in matched_ids 
                            if any(g["issue_id"] == mid for g in critical_gt))
        missed_critical_penalty = 0.08 * (len(critical_gt) - critical_found)

        # Coverage requirement (hard task requires reading most sections)
        coverage = len(sections_reviewed) / len(all_sections)
        coverage_score = min(1.0, coverage * 1.2)  # Full credit at ~83% coverage

        # Precision
        total_flags = len(flags_raised)
        fp_rate = false_positives / total_flags if total_flags > 0 else 0.0
        precision_penalty = 0.2 * fp_rate

        # Efficiency
        step_ratio = steps_used / max_steps
        efficiency_bonus = max(0.0, 0.1 * (1.0 - step_ratio)) if submitted else 0.0

        # Not submitting penalty
        submission_penalty = 0.15 if not submitted else 0.0

        score = (
            0.60 * weighted_recall
            + 0.20 * coverage_score
            + efficiency_bonus
            - missed_critical_penalty
            - precision_penalty
            - submission_penalty
        )
        score = min(1.0, max(0.0, score))

        return TaskResult(
            task_id=task_id,
            score=round(score, 4),
            true_positives=len(matched_ids),
            false_positives=false_positives,
            false_negatives=len(ground_truth_issues) - len(matched_ids),
            critical_issues_found=critical_found,
            critical_issues_total=len(critical_gt),
            steps_used=steps_used,
            max_steps=max_steps,
            efficiency_bonus=efficiency_bonus,
            final_reward=score,
            passed=score >= 0.45,
            breakdown={
                "weighted_recall": round(weighted_recall, 4),
                "coverage_score": round(coverage_score, 4),
                "missed_critical_penalty": round(missed_critical_penalty, 4),
                "precision_penalty": round(precision_penalty, 4),
                "efficiency_bonus": round(efficiency_bonus, 4),
                "submission_penalty": submission_penalty,
                "sections_reviewed": sections_reviewed,
                "sections_coverage": f"{len(sections_reviewed)}/{len(all_sections)}",
                "total_gt_issues": len(ground_truth_issues),
            }
        )


# ─── Grader Registry ──────────────────────────────────────────────────────────

GRADERS = {
    "task_easy": EasyGrader(),
    "task_medium": MediumGrader(),
    "task_hard": HardGrader(),
}


def get_grader(task_id: str) -> BaseGrader:
    if task_id not in GRADERS:
        raise ValueError(f"Unknown task_id: {task_id}. Available: {list(GRADERS.keys())}")
    return GRADERS[task_id]
