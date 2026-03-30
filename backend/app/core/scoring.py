import json
import re

# Tier thresholds -- single source of truth (referenced by spec Section 3.0)
TIER_THRESHOLDS = {"S": 75, "A": 50, "B": 35, "C": 1}


def get_tier(score: int) -> str:
    """Return tier letter for a given score."""
    if score >= TIER_THRESHOLDS["S"]:
        return "S"
    elif score >= TIER_THRESHOLDS["A"]:
        return "A"
    elif score >= TIER_THRESHOLDS["B"]:
        return "B"
    elif score >= TIER_THRESHOLDS["C"]:
        return "C"
    return "C"


def load_profile(profile_path: str) -> dict:
    """Load user profile JSON."""
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def keyword_score_job(job: dict, profile: dict) -> int:
    """Score a single job based on keyword matching. Returns 0-100.
    Ported directly from v4 ai_evaluator.py."""
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    desc = (job.get("description") or "").lower()
    reqs = (job.get("requirements") or "").lower()
    skills_field = (job.get("skills") or "").lower()
    benefits = (job.get("benefits") or "").lower()
    location = (job.get("location") or "").lower()
    level = (job.get("level") or "").lower()

    all_text = f"{desc} {reqs} {skills_field} {benefits}"
    title_company = f"{title} {company}"
    score = 0

    # 0. IRRELEVANT TITLE PENALTY (early exit)
    irrelevant_titles = [
        "frontend", "front-end", "react native", "ios dev", "android dev",
        "mobile dev", "flutter", "swift dev", "kotlin dev", "react dev",
        "angular", "vue.js dev", "nextjs",
        "backend", "back-end", "fullstack", "full-stack", "full stack",
        "devops", "sre ", "site reliability", "infrastructure",
        "platform engineer", "cloud engineer", "system admin",
        "network engineer", "security engineer", "penetration tester",
        "ui/ux", "ux designer", "ui designer", "graphic design", "content",
        "marketing", "seo ", "social media", "copywriter",
        "sales", "telesales", "t\u01b0 v\u1ea5n b\u00e1n", "account manager",
        "customer success", "ch\u0103m s\u00f3c kh\u00e1ch", "t\u01b0 v\u1ea5n vi\u00ean",
        "game dev", "game design", "unity dev", "unreal",
        "embedded", "firmware", "hardware",
        "teacher", "gi\u00e1o vi\u00ean", "gia s\u01b0", "gi\u1ea3ng d\u1ea1y",
        "hr ", "nh\u00e2n s\u1ef1", "h\u00e0nh ch\u00ednh", "admin", "receptionist",
        "l\u1ec5 t\u00e2n", "th\u01b0 k\u00fd",
        "manual tester", "manual qa", "qa engineer", "qc engineer",
        "qa automation", "quality assurance", "test engineer",
        "qa manager", "tester",
        "project manager", "scrum master", "delivery manager",
        "product owner", "technical lead", "tech lead",
        "java developer", ".net developer", "php developer",
        "c# developer", "c++ developer", "ruby developer",
        "golang developer", "go developer", "rust developer",
        "nodejs developer", "node.js developer",
        "software engineer", "l\u1eadp tr\u00ecnh vi\u00ean",
    ]
    for kw in irrelevant_titles:
        if kw in title:
            return 0

    # 1. Title Match (max 25)
    title_score = 0
    for tier_name, tier in profile["title_keywords"].items():
        if tier_name.startswith("_"):
            continue
        if not isinstance(tier, dict) or "keywords" not in tier:
            continue
        for kw in tier["keywords"]:
            if kw.lower() in title:
                title_score = max(title_score, tier["score"])
        if title_score > 0:
            break
    score += title_score

    # 2. Skill Match (max 25)
    skill_score = 0
    for lv in ["high_value", "medium_value", "low_value"]:
        group = profile["skill_keywords"][lv]
        for kw in group["keywords"]:
            if kw.lower() in all_text or kw.lower() in skills_field:
                skill_score += group["points_each"]
    score += min(skill_score, 25)

    # 3. Industry Match (max 25)
    industry_score = 0
    for tier_name in ["tier_s_finance", "tier_a_finance_domain", "tier_b_tech"]:
        tier = profile["industry_keywords"][tier_name]
        for kw in tier["keywords"]:
            if kw.lower() in title_company or kw.lower() in all_text:
                industry_score = max(industry_score, tier["points"])
                break
        if industry_score >= 20:
            break
    score += industry_score

    # 4. Work Style (max 15, can go negative)
    style_score = 0
    for kw in profile["work_style"]["positive"]["keywords"]:
        if kw.lower() in all_text:
            style_score += profile["work_style"]["positive"]["points_each"]
    for kw in profile["work_style"]["negative"]["keywords"]:
        if kw.lower() in all_text:
            style_score += profile["work_style"]["negative"]["points_each"]
    score += max(min(style_score, 15), -10)

    # 5. Experience Level (max 10, can go very negative)
    exp_score = 0
    exp_text = f"{title} {reqs} {level}"

    if level:
        year_match = re.search(r'(\d+)\s*[-\u2013]\s*(\d+)', level)
        if year_match:
            min_years = int(year_match.group(1))
        else:
            single_match = re.search(r'(\d+)', level)
            min_years = int(single_match.group(1)) if single_match else 0

        if min_years >= 5:
            exp_score = -25
        elif min_years >= 3:
            exp_score = -15
        elif min_years >= 2:
            exp_score = -5
        elif min_years <= 1:
            exp_score = 10

    if 'gi\u00e1m \u0111\u1ed1c' in title or 'director' in title or 'head of' in title or 'tr\u01b0\u1edfng ph\u00f2ng' in title:
        exp_score = min(exp_score, -20)
    elif 'senior' in title or 'lead' in title or 'principal' in title or 'staff' in title:
        exp_score = min(exp_score, -10)

    if not level and exp_score == 0:
        for level_name in ["ideal", "acceptable", "stretch"]:
            level_cfg = profile["experience_level"][level_name]
            for kw in level_cfg["keywords"]:
                if kw.lower() in exp_text:
                    exp_score = level_cfg["points"]
                    break
            if exp_score != 0:
                break

    score += exp_score

    # 6. Location Bonus (Hanoi +5)
    hanoi_keywords = ["h\u00e0 n\u1ed9i", "ha noi", "hanoi", "c\u1ea7u gi\u1ea5y", "nam t\u1eeb li\u00eam",
                      "thanh xu\u00e2n", "\u0111\u1ed1ng \u0111a", "ho\u00e0n ki\u1ebfm", "ba \u0111\u00ecnh"]
    for kw in hanoi_keywords:
        if kw in location or kw in title:
            score += 5
            break

    # 7. No relevant title keyword -> cap at 15
    if title_score == 0:
        score = min(score, 15)

    return max(0, min(100, score))
