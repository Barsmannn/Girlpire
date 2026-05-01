from __future__ import annotations

import base64
import csv
import html
import io
import json
import math
import os
from pathlib import Path
import textwrap
import traceback
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
load_dotenv()

try:
    from groq import Groq
except Exception:  # pragma: no cover - optional dependency
    Groq = None

try:
    import resend
except Exception:  # pragma: no cover - optional dependency
    resend = None


APP_DIR = Path(__file__).resolve().parent
EMAILS_FILE = APP_DIR / "emails.json"
GUIDE_PDF_APP_PATH = APP_DIR / "assets" / "Onlyfans App Guide.pdf"
GUIDE_PDF_PART_1_PATH = APP_DIR / "assets" / "OnlyFans Beginner's Guide - Part 1.pdf"
GUIDE_PDF_PART_2_PATH = APP_DIR / "assets" / "OnlyFans Beginner's Guide - Part 2.pdf"
BRAND_LOGO_WORDMARK_PATH = APP_DIR / "assets" / "girlpire-logo-glow-symbol.png"
BRAND_LOGO_SYMBOL_PATH = APP_DIR / "assets" / "girlpire-logo-glow-symbol.png"
load_dotenv(dotenv_path=APP_DIR / ".env", override=False)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
APP_TITLE = "Girlpire - OnlyFans Success Portal"
DEFAULT_LEMONSQUEEZY_CHECKOUT_URL = (
    "https://girlpire.lemonsqueezy.com/checkout/buy/"
    "cbeec9a3-c280-4b1b-9123-480d112c5ee9"
)
PLATFORM_FEE_RATE = 0.20
ACTIVE_SUBSCRIPTION_STATES = {"active", "on_trial"}
LANGUAGE_OPTIONS = {
    "en": "English",
    "tr": "Turkce",
    "de": "Deutsch",
    "fr": "Francais",
    "es": "Espanol",
    "ru": "Russkiy",
    "nl": "Nederlands",
    "pt": "Portugues",
    "it": "Italiano",
}


@st.cache_data(show_spinner=False)
def get_asset_data_uri(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def get_brand_wordmark_uri() -> str:
    return get_asset_data_uri(str(BRAND_LOGO_WORDMARK_PATH))


def get_brand_symbol_uri() -> str:
    return get_asset_data_uri(str(BRAND_LOGO_SYMBOL_PATH))
TRANSLATIONS = {
    "en": {
        "brand": "Girlpire",
        "hero_title": "Calculate Your Global Potential",
        "hero_subtitle": "Business-focused creator growth platform",
        "dashboard_workspace": "VIP Workspace",
        "dashboard_top_title": "Financial Dashboard",
        "dashboard_welcome": "Welcome back, {name}",
        "dashboard_workspace_body": "A premium revenue command center for creators and agencies focused on pricing, retention and scalable monthly growth.",
        "dashboard_focus_chip": "Focus of the month",
        "dashboard_sync_chip": "Live revenue view",
        "dashboard_search_placeholder": "Tap here to search",
        "dashboard_nav_dashboard": "Dashboard",
        "dashboard_nav_documents": "Documents",
        "dashboard_nav_payments": "Payments",
        "dashboard_nav_calendar": "Calendar",
        "dashboard_nav_profile": "Profile",
        "dashboard_nav_darkmode": "Darkmode",
        "dashboard_nav_settings": "Settings",
        "dashboard_nav_logout": "Logout",
        "dashboard_nav_strategy": "Strategy Engine",
        "dashboard_nav_tracking": "Progress Tracking",
        "dashboard_nav_assets": "VIP Assets",
        "dashboard_nav_membership": "Membership Status",
        "dashboard_vip_badge": "VIP Active",
        "dashboard_membership_since": "VIP since",
        "dashboard_membership_expires": "Access through",
        "dashboard_membership_locked": "Unlock VIP to access the guide library and private planning tools.",
        "dashboard_guides_title": "Guide Library",
        "dashboard_chart_selector": "Chart view",
        "dashboard_chart_gross": "Gross income trend",
        "dashboard_chart_net": "Net income trend",
        "dashboard_chart_target": "Target progress trend",
        "dashboard_cart_toggle": "Membership",
        "dashboard_bell_label": "VIP",
        "dashboard_membership_tip": "Use this panel to confirm your active VIP access window.",
        "dashboard_card_growth": "Growth Signal",
        "dashboard_card_margin": "Margin Quality",
        "dashboard_card_arppu": "Revenue Per Fan",
        "dashboard_card_focus": "Current Priority",
        "dashboard_chart_title": "Monthly Performance Map",
        "dashboard_chart_body": "Use this workspace to identify where revenue is leaking, what to optimize next and how close you are to your next monthly target.",
        "vip_nav_section": "VIP Sections",
        "vip_nav_dashboard": "Dashboard",
        "vip_nav_strategy": "Strategy",
        "vip_nav_tracking": "Tracking",
        "vip_nav_guide": "Guide",
        "vip_nav_advanced": "Advanced",
        "vip_nav_calculator": "Calculator",
        "vip_nav_scenarios": "Scenarios",
        "vip_sidebar_status": "VIP Active",
        "language": "Language",
        "logged_in_as": "Logged in as",
        "logout": "Logout",
        "free_title": "Estimate Your OnlyFans Income",
        "free_desc": "Use the public calculator to model monthly and yearly income before moving into VIP strategy.",
        "follower_count": "Follower Count",
        "monthly_sub_price": "Monthly Sub Price ($)",
        "expected_tips_ppv": "Expected Tips / PPV ($)",
        "target_monthly_income_input": "Target Monthly Income ($)",
        "calculate_money_engine": "Calculate",
        "analyzing_potential": "Analyzing your earning potential...",
        "gross_income": "Gross Income",
        "platform_fee": "Platform Fee",
        "net_income": "Net Income",
        "yearly_net_income": "Yearly Net Income",
        "estimate_note": "These results are estimates for planning and positioning only.",
        "revenue_per_fan": "Revenue Per Fan",
        "revenue_per_fan_value": "{amount} per fan",
        "arppu_low": "Your revenue per fan is low. Most growth comes from increasing fan value, not just followers.",
        "arppu_mid": "You have average monetization. There is room to improve PPV and tips.",
        "arppu_high": "You have strong monetization. Focus on scaling traffic and retention.",
        "money_gap_title": "You are leaving approximately {amount}/month on the table.",
        "money_gap_body": "With better pricing, PPV strategy and retention, many creators increase revenue by 50%+.",
        "target_engine_title": "Target Engine",
        "target_engine_body": "To reach {target}/month you need approximately {fans} paying fans.",
        "target_engine_warning": "Your current model relies too much on volume. Increasing revenue per fan is critical.",
        "potential_stage_early": "You are in the early stage. Focus on conversion and basic monetization.",
        "potential_stage_mid": "You have a base. Optimization will unlock significant growth.",
        "potential_stage_high": "You are in scaling phase. Focus on retention and margin.",
        "urgency_line": "Most creators never optimize their revenue model. Small changes can significantly increase income.",
        "cta_title": "Turn your estimate into a conversion plan",
        "cta_desc": "Use Google login to save the strategy flow to your account and match future VIP access to the same email.",
        "get_ai_strategy": "Get My Girlpire Strategy",
        "unlock_vip_guide": "Unlock Girlpire VIP",
        "cta_first_growth": "Build My Growth Strategy",
        "cta_optimize_revenue": "Optimize My Revenue Strategy",
        "cta_scale_business": "Scale My Creator Business",
        "cta_email_return": "View My Updated Strategy",
        "preview_benefit_strategy": "See the highest-leverage pricing and revenue moves for your current stage.",
        "preview_benefit_plan": "Follow a structured 30-day action plan instead of guessing week to week.",
        "preview_benefit_bible": "Use the business guide to tighten positioning, offers, and tracking.",
        "preview_benefit_pricing": "Identify where pricing and PPV structure can unlock more value per fan.",
        "preview_benefit_updates": "Stay aligned with monthly strategy updates and optimization ideas.",
        "social_proof_title": "Why creators use this tool",
        "social_proof_card_1": "See your real net income after platform fees",
        "social_proof_card_2": "Understand how much revenue you may be missing",
        "social_proof_card_3": "Find whether your problem is pricing, PPV or traffic",
        "social_proof_card_4": "Build a strategy before paying for ads or agencies",
        "email_welcome_title": "Welcome back",
        "email_ready_line": "Your new Girlpire strategy is ready.",
        "email_money_line": "You may be leaving money on the table.",
        "email_login_prompt": "Continue with Google to access your strategy",
        "email_paywall_prompt": "Your updated Girlpire strategy is ready. Unlock VIP to access it.",
        "email_paid_prompt": "Your new Girlpire strategy is ready below.",
        "upgrade_flow_title": "Girlpire strategy update ready",
        "upgrade_login_prompt": "Continue with Google to unlock your strategy",
        "upgrade_paywall_prompt": "Your Girlpire strategy is ready. Complete your VIP access.",
        "upgrade_paid_prompt": "Your Girlpire VIP strategy is ready below.",
        "login_gate_title": "Continue to Unlock Your Strategy",
        "login_gate_desc": "Log in with Google to continue to the VIP decision step and sync access with your future membership.",
        "continue_google": "Continue with Google",
        "login_preview_label": "VIP Preview",
        "login_preview_body": "Premium growth planning for creators and agencies that want clearer pricing, better retention and a more scalable revenue system.",
        "google_setup_missing": "Google login is not configured yet.",
        "google_setup_hint": "Add Google OIDC values to .streamlit/secrets.toml to enable native Streamlit login.",
        "paywall_title": "Unlock Girlpire VIP & Monthly Updates",
        "paywall_desc": "VIP includes the AI Strategy Consultant, a 30-Day Growth Plan, The Girlpire Creator Bible, and monthly updates.",
        "pricing_anchor_title": "VIP Membership",
        "pricing_anchor_price": "$19/month",
        "pricing_anchor_note": "Less than one failed promo post or one underpriced PPV bundle.",
        "vip_offer_title": "What you get:",
        "vip_offer_item_1": "Exact pricing strategy (+conversion boost)",
        "vip_offer_item_2": "DM scripts that convert followers to buyers",
        "vip_offer_item_3": "30-day content plan",
        "vip_offer_item_4": "Monetization system (step by step)",
        "vip_offer_item_5": "Hidden growth tactics",
        "vip_offer_result_note": "Potential upside depends on execution, positioning, and audience quality.",
        "vip_pricing_message_1": "Clear checkout. No hidden fees.",
        "vip_pricing_message_2": "Access and billing terms are shown before payment.",
        "paywall_urgency": "Limited free analyses available today",
        "paywall_stack_title": "VIP Membership Includes:",
        "vip_feature_strategy": "AI Strategy Consultant",
        "vip_feature_plan": "30-Day Action Plan",
        "vip_feature_bible": "Girlpire Creator Bible",
        "vip_feature_pricing": "Pricing Optimization",
        "vip_feature_ppv": "PPV & Tips Revenue Plan",
        "vip_feature_updates": "Monthly Strategy Updates",
        "paywall_stack_note": "Built for creators who want a business-focused growth plan, not generic advice.",
        "start_vip_membership": "🚀 Unlock Full Strategy Now",
        "risk_reversal": "Cancel anytime. Your strategy remains accessible while your membership is active.",
        "loss_aversion_copy": "If your current revenue model is under-optimized, waiting another month can cost more than the VIP membership.",
        "faq_title": "FAQ",
        "faq_q1": "Do I need to show my identity?",
        "faq_a1": "No. The guide is focused on anonymous positioning and business strategy.",
        "faq_q2": "Is this only a calculator?",
        "faq_a2": "No. The free calculator estimates potential. VIP unlocks strategy, guide and monthly optimization.",
        "faq_q3": "Can I cancel anytime?",
        "faq_a3": "Yes. Subscription management is handled through LemonSqueezy.",
        "faq_q4": "Does the AI replace my judgment?",
        "faq_a4": "No. It gives a structured business strategy based on your inputs.",
        "faq_q5": "Is my payment handled securely?",
        "faq_a5": "Payments are handled through LemonSqueezy. Girlpire does not store card details.",
        "unlock_vip_strategy": "🚀 Unlock Full Strategy Now",
        "trust_checkout_line1": "Secure checkout powered by LemonSqueezy.",
        "trust_checkout_line2": "No card information is stored by Girlpire.",
        "admin_email_tools_title": "Girlpire Admin",
        "admin_email_tools_desc": "Use Resend to send manual monthly reminders without a database.",
        "vip_active": "Girlpire VIP Active",
        "vip_unlocked_message": "Your VIP strategy is unlocked",
        "vip_upgrade_message": "Upgrade to Girlpire VIP to unlock your strategy",
        "pay_with_crypto": "💰 Unlock with Crypto",
        "pay_with_card": "🚀 Unlock Full Strategy Now",
        "card_disabled_notice": "Card checkout is temporarily unavailable. Contact us via DM to unlock access.",
        "open_crypto_payment": "Open Crypto Payment",
        "crypto_payment_ready": "Your crypto payment page is ready below.",
        "crypto_step_title": "Step 2: Open Your Crypto Checkout",
        "crypto_step_body": "This checkout flow is mobile and desktop friendly. Tap the button below to continue to the NowPayments payment page.",
        "crypto_payment_manual_hint": "If the payment page did not open automatically, use the button or direct link below.",
        "crypto_direct_link": "Direct payment link",
        "crypto_payment_failed": "Crypto payment failed",
        "crypto_payment_unavailable": "Add NOWPAYMENTS_API_KEY or nowpayments.api_key to Streamlit secrets to enable crypto payments.",
        "crypto_disabled_notice": "Crypto checkout is temporarily unavailable. Contact us via DM to unlock access.",
        "add_myself_vip": "Add myself to VIP",
        "vip_add_success": "You are now VIP",
        "total_users_metric": "Total Users",
        "vip_users_metric": "VIP Users",
        "all_users_title": "All Users",
        "new_users_title": "New Users (7 days)",
        "vip_users_title": "VIP Users",
        "member_name": "Name",
        "member_email": "Email",
        "member_since": "Created At",
        "name_missing": "-",
        "download_all_users": "Download All Members CSV",
        "download_vip_users": "Download VIP Members CSV",
        "grant_vip_title": "Grant VIP Access",
        "grant_vip_desc": "Give one month of VIP access to any email address.",
        "grant_vip_email": "VIP email",
        "grant_vip_name": "Name (optional)",
        "grant_vip_button": "Grant 1-Month VIP",
        "grant_vip_success": "VIP access was granted to {email} for 30 days.",
        "grant_vip_failed": "VIP access could not be granted. Check the email and try again.",
        "no_users_saved": "No users saved yet.",
        "no_new_users": "No new users in the last 7 days.",
        "no_vip_users": "No VIP users yet.",
        "saved_email_count": "Saved Emails",
        "send_test_email": "Send Test Email",
        "send_to_all_users": "Send To All Users",
        "resend_missing_key": "RESEND_API_KEY is missing. Add it to your environment or .env file to send emails.",
        "resend_package_missing": "The resend package is not available yet. Install the project requirements to enable email sending.",
        "email_send_success": "Email sent successfully.",
        "email_send_failed": "Email could not be sent right now.",
        "email_no_user": "No logged-in email is available for the test message.",
        "email_bulk_success": "Sent {sent} emails. Failed: {failed}.",
        "email_bulk_sent_count": "Emails sent to {count} users.",
        "emails_empty": "No saved users found in emails.json yet.",
        "email_tools_future_ready": "This system can later be replaced with a real scheduler or webhook system.",
        "monthly_email_subject": "Your Girlpire Strategy is Ready",
        "monthly_email_heading": "Girlpire Strategy Update",
        "monthly_email_body": "You may be leaving money on the table. Your updated strategy is waiting for you.",
        "monthly_email_button": "Unlock Girlpire VIP",
        "email_test_fallback_used": "No logged-in email found. Sending the test email to the fallback address instead.",
        "checkout_missing": "Add lemonsqueezy.checkout_url to secrets to enable the checkout button.",
        "payment_notice": "VIP is unlocked only after a real payment is synced into your paid user list or a verified LemonSqueezy subscription record is found.",
        "vip_sync_notice": "Crypto payments unlock automatically after the confirmed webhook reaches Girlpire. If you just paid, refresh this page in a few seconds.",
        "vip_refresh_checkout_notice": "If you just completed card checkout, tap refresh below to sync your VIP access.",
        "refresh_vip_access": "I Already Paid - Refresh VIP Access",
        "vip_refresh_success": "VIP access was found and refreshed.",
        "vip_refresh_pending": "No verified VIP access was found yet. If you paid just now, wait a moment and try again.",
        "vip_title": "VIP Dashboard",
        "vip_desc": "This area is unlocked only for verified subscribers and uses your current calculator values as context.",
        "strategy_dashboard_title": "Your Creator Strategy Dashboard",
        "monthly_strategy_cycle_title": "Monthly Strategy Cycle",
        "new_month_detected": "New month detected. Time to refresh your strategy.",
        "generate_new_monthly_strategy": "Generate New Monthly Strategy",
        "focus_of_month": "Focus of the Month",
        "focus_low": "Conversion & monetization",
        "focus_mid": "Optimization",
        "focus_high": "Scaling & retention",
        "welcome_back": "Welcome back. Let's see what changed since your last strategy.",
        "current_net_income": "Current Net Income",
        "target_income_metric": "Target Income",
        "gap_to_target": "Gap",
        "score_explanation_weak": "Your model has at least one weak engine. Improve monetization quality before pushing harder on scale.",
        "score_explanation_average": "The business has a workable base, but one or two revenue levers are under-optimized.",
        "score_explanation_good": "The model is healthy. Focus on tightening weak spots and executing consistently.",
        "score_explanation_strong": "Your monetization engine is strong. Protect margin and scale carefully.",
        "strategy_consultant": "AI Strategy Consultant",
        "daily_time": "Daily Available Time (hours)",
        "target_income": "Target Income ($)",
        "experience_level": "Experience Level",
        "main_challenge": "Main Challenge",
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
        "traffic": "Traffic",
        "conversion": "Conversion",
        "pricing": "Pricing",
        "retention": "Retention",
        "consistency": "Consistency",
        "generate_strategy": "Generate VIP Strategy",
        "strategy_generate_hint": "Generate your strategy to unlock immediate fixes, revenue optimization, and the 30-day plan.",
        "quick_strategy_title": "Smart Strategy Engine",
        "quick_strategy_desc": "Get a fast rule-based strategy report using your growth, engagement, pricing, and posting inputs.",
        "quick_strategy_followers": "Followers",
        "quick_strategy_engagement": "Engagement %",
        "quick_strategy_price": "Subscription Price ($)",
        "quick_strategy_posts": "Posts per week",
        "analyze_my_strategy": "Analyze My Strategy",
        "strategy_report_title": "Strategy Report",
        "quick_strategy_level_early": "You are in early stage. Focus on growth, not monetization.",
        "quick_strategy_level_mid": "You have growth potential but an underutilized audience.",
        "quick_strategy_level_high": "You have a monetizable audience. Focus on scaling.",
        "quick_strategy_engagement_low": "Your engagement is low. Use stronger hooks and sharper captions to increase reaction.",
        "quick_strategy_engagement_mid": "Engagement is average. Improve consistency and story usage.",
        "quick_strategy_engagement_high": "Strong engagement. You can push premium offers harder.",
        "quick_strategy_price_high": "You are overpriced for your current audience size. Reduce price to improve conversion.",
        "quick_strategy_price_low": "You are underpricing. Increase price gradually while improving perceived value.",
        "quick_strategy_price_ok": "Your pricing is acceptable for your current level.",
        "quick_strategy_content_low": "You are posting too little. Increase content frequency.",
        "quick_strategy_content_high": "You are posting too much. Focus on quality instead of quantity.",
        "quick_strategy_content_ok": "Your posting frequency is in a healthy range.",
        "creator_score_title": "Creator Score",
        "creator_score_underperforming": "Your account is underperforming",
        "creator_score_untapped": "You have untapped potential",
        "creator_score_strong": "Strong account, ready to scale",
        "quick_strategy_loss_title": "You are losing approx {amount}/month",
        "quick_strategy_potential_title": "Potential Growth",
        "quick_strategy_current_label": "Current",
        "quick_strategy_optimized_label": "Optimized",
        "quick_strategy_current": "Current: {amount}/month",
        "quick_strategy_optimized": "Optimized: {amount}/month",
        "quick_strategy_locked": "Unlock full strategy to improve conversion, monetization, and retention",
        "quick_strategy_vip_includes": "VIP includes:",
        "quick_strategy_vip_item_1": "Full monetization plan",
        "quick_strategy_vip_item_2": "DM scripts",
        "quick_strategy_vip_item_3": "Content strategy",
        "quick_strategy_vip_item_4": "Scaling system",
        "quick_strategy_urgency": "Free strategy previews are limited so VIP members can get the full planning workflow.",
        "quick_strategy_social_proof": "Built for creators who want to diagnose pricing, content, and monetization issues before spending on traffic.",
        "quick_strategy_psychology_line": "This gap usually comes from pricing, positioning, or weak conversion mechanics.",
        "mentor_analysis_title": "Strategy Analysis",
        "mentor_problems_title": "Key Problems",
        "mentor_opportunities_title": "Opportunities",
        "mentor_next_title": "What You Should Do Next",
        "mentor_summary": "Based on your data, you are currently working with **{followers} followers**, **{engagement}% engagement**, a **{price}** subscription, and **{posts} posts per week**.",
        "mentor_authority_1": "Creators at your level often earn materially more when pricing, conversion, and consistency are optimized.",
        "mentor_authority_2": "This pattern is common among underperforming accounts that try to scale before tightening the core offer.",
        "mentor_biggest_mistake_label": "Your biggest mistake is",
        "mentor_biggest_mistake_low": "weak engagement and low hook strength",
        "mentor_biggest_mistake_mid": "average engagement without enough conversion pressure",
        "mentor_biggest_mistake_high": "not monetizing strong audience signals aggressively enough",
        "mentor_problem_growth_early": "You are currently too early-stage to lean on monetization alone. Your audience still needs stronger top-of-funnel growth.",
        "mentor_problem_growth_mid": "You have audience potential, but you are underutilizing the attention you already have.",
        "mentor_problem_growth_high": "You have a monetizable audience. The issue is no longer attention alone, it is execution and monetization depth.",
        "mentor_problem_engagement_low": "You have {followers} followers but only {engagement}% engagement, which is below optimal. Your content hooks are not pulling enough reaction.",
        "mentor_problem_engagement_mid": "Your engagement is serviceable, but not strong enough to maximize premium conversion yet.",
        "mentor_problem_engagement_high": "Your engagement is already strong, which means better monetization is available if the offer gets sharper.",
        "mentor_problem_price_high": "Your current price is high relative to your audience size, which likely hurts conversion more than you realize.",
        "mentor_problem_price_low": "Your current price is leaving money on the table. Underpricing can make the offer look weaker, not just cheaper.",
        "mentor_problem_price_ok": "Pricing is not your biggest issue right now. The bigger opportunity is conversion quality and follow-up structure.",
        "mentor_problem_posts_low": "Your posting rhythm is too light. The market will not reward inconsistency.",
        "mentor_problem_posts_high": "You are posting a lot, but the next gain will come from sharper positioning, not simply more volume.",
        "mentor_problem_posts_ok": "Your content frequency is acceptable. Improvement now comes from tighter monetization mechanics.",
        "mentor_opportunity_growth": "Based on your data, the biggest upside comes from improving value per follower before chasing more traffic.",
        "mentor_opportunity_offer": "With a clearer offer and stronger follow-up, your current audience can convert better than it is converting now.",
        "mentor_opportunity_consistency": "A more consistent weekly content and selling cadence would make your revenue less random and more repeatable.",
        "mentor_step_1": "Step 1: Fix the main bottleneck first instead of changing everything at once.",
        "mentor_step_2": "Step 2: Tighten your pricing, hooks, and conversion flow so more of your existing audience moves toward purchase.",
        "mentor_step_3": "Step 3: Run the same content and monetization rhythm for 2-4 weeks before judging the result.",
        "groq_fallback_missing": "Groq is not configured. Showing the built-in rule-based strategy consultant instead.",
        "groq_fallback_failed": "Groq could not respond right now. Showing the built-in rule-based strategy consultant instead.",
        "immediate_fix_title": "Immediate Fix (Next 7 Days)",
        "revenue_optimization_title": "Revenue Optimization",
        "growth_focus_section": "Growth Focus",
        "biggest_bottleneck_title": "Biggest Bottleneck",
        "three_point_strategy": "3-Point Strategy",
        "thirty_day_plan": "30-Day Plan",
        "monetization_advice": "Monetization Advice",
        "pricing_advice": "Pricing Advice",
        "weekly_plan_title": "30-Day Action Plan",
        "week1_title": "Week 1 -> Setup & Fixes",
        "week2_title": "Week 2 -> Monetization Push",
        "week3_title": "Week 3 -> Optimization",
        "week4_title": "Week 4 -> Scaling",
        "track_progress_title": "Track Your Progress",
        "your_progress_title": "Your Progress",
        "last_month_revenue": "Last Month Revenue",
        "current_subscribers": "Current Subscribers",
        "current_revenue_input": "Current Revenue",
        "new_subscribers_gained": "New Subscribers Gained",
        "subscriber_change": "Subscriber Change",
        "revenue_growth": "Revenue Growth %",
        "subscriber_growth": "Growth %",
        "progress_to_target": "Progress to Target",
        "tracking_growth_note": "Use these monthly tracking inputs to measure whether the strategy is moving the business forward.",
        "progress_positive": "You're improving. Keep pushing current strategy.",
        "progress_negative": "Performance dropped. Adjust your strategy.",
        "progress_mixed": "Some signals improved while others weakened. Review the weak spots before scaling.",
        "save_monthly_update": "Save Monthly Update",
        "history_title": "Monthly Snapshot History",
        "history_empty": "Save your first monthly update to start building history.",
        "month": "Month",
        "revenue": "Revenue",
        "subscribers": "Subscribers",
        "what_improved": "What improved",
        "what_declined": "What declined",
        "what_to_fix_next": "What to fix next",
        "nothing_improved": "No major improvements recorded yet.",
        "nothing_declined": "No major declines detected.",
        "fix_next_conversion": "Tighten the offer and conversion path before chasing more reach.",
        "fix_next_traffic": "Add more qualified traffic only after your strongest offer is ready to scale.",
        "fix_next_retention": "Protect current buyers with better follow-up and reactivation before expanding.",
        "consistency_badge": "Consistency Badge",
        "badge_none": "Not Started",
        "badge_starter": "Starter",
        "badge_active": "Active",
        "badge_consistent": "Consistent",
        "badge_elite": "Elite",
        "previous_strategy_title": "Previous Strategy",
        "previous_strategy_summary": "Previous strategy snapshot",
        "previous_score": "Previous score",
        "previous_bottleneck": "Previous bottleneck",
        "previous_focus": "Previous focus",
        "what_changed_title": "What Changed",
        "no_changes_yet": "No major strategic changes from the last snapshot yet.",
        "download_strategy_report": "Download My Strategy Report",
        "bottleneck_fan_value": "Revenue per fan is too low for the current target.",
        "bottleneck_margin": "Profit margin is too thin to scale safely.",
        "bottleneck_traffic": "Top-of-funnel traffic is limiting growth.",
        "bottleneck_conversion": "The current offer is not converting enough value from the audience you already have.",
        "bottleneck_retention": "Retention is leaking value before growth compounds.",
        "bottleneck_system": "Execution consistency is holding the business back.",
        "growth_focus_traffic": "Traffic should be the priority. The business needs more qualified top-of-funnel visitors.",
        "growth_focus_conversion": "Conversion should be the priority. More visitors will not help until the offer converts better.",
        "growth_focus_retention": "Retention should be the priority. Protect current buyers and reduce leakage before scaling.",
        "fix_price_audit": "Audit your current offer stack and test one stronger pricing anchor this week.",
        "fix_ppv_launch": "Launch one repeatable PPV bundle with a clear deadline and track the take rate.",
        "fix_tip_goal": "Set one public tip goal and one clear upsell path for your highest-intent fans.",
        "fix_offer_refresh": "Refresh the offer framing so premium value is clearer before the visitor reaches checkout.",
        "fix_conversion_path": "Simplify the conversion path so each visitor sees one main reason to subscribe now.",
        "fix_retention_check": "Review recent buyer drop-off and add one reactivation message for quiet subscribers.",
        "fix_tracking_review": "Create a simple weekly scoreboard for price, PPV, tip revenue, and churn signals.",
        "revenue_price_low": "Pricing: run one 7-day test with a stronger anchor and avoid permanent discounting.",
        "revenue_price_hold": "Pricing: keep the current price but make the premium reason more obvious on your page and offers.",
        "revenue_ppv_low": "PPV: build one weekly PPV bundle so extra revenue becomes predictable instead of random.",
        "revenue_ppv_high": "PPV: tighten your best-performing bundle and remove low-response offers that create noise.",
        "revenue_tips": "Tips: attach each tip request to a visible goal or reward so fans know what action to take.",
        "week1_step1": "Audit your page promise, pricing logic, and top offer.",
        "week1_step2": "Define one main conversion message and remove weaker competing messages.",
        "week1_step3": "Set up a simple weekly scorecard for revenue, subscribers, and churn signals.",
        "week2_step1": "Launch one repeatable PPV bundle with a deadline.",
        "week2_step2": "Add one tip goal or upgrade path that feels easy to understand.",
        "week2_step3": "Message your existing audience with one clear premium offer.",
        "week3_step1": "Review take rate, conversion, and net income instead of only gross revenue.",
        "week3_step2": "Keep the strongest offer and cut at least one low-return task.",
        "week3_step3": "Improve the buyer journey where drop-off is highest.",
        "week4_step1": "Double down on the highest-performing offer from the month.",
        "week4_step2": "Reinvest carefully into the one channel that produced qualified demand.",
        "week4_step3_traffic": "Scale only the traffic source that converts into paying fans consistently.",
        "week4_step3_conversion": "Scale only after the page promise and subscription conversion rate improve.",
        "week4_step3_retention": "Scale only after retention and repeat buyer behavior stabilize.",
        "change_score_up": "Your strategy score improved by {points} points.",
        "change_score_down": "Your strategy score dropped by {points} points.",
        "change_bottleneck": "Main bottleneck changed from '{previous}' to '{current}'.",
        "change_focus": "Growth focus shifted from '{previous}' to '{current}'.",
        "vip_guide_title": "The Girlpire Creator Bible",
        "vip_guide_desc": "Download the private business guide for positioning, pricing, monetization, and weekly tracking.",
        "download_guide": "Download Guide",
        "download_guide_pdf": "Download VIP PDF Guide",
        "download_guide_pdf_app": "Download App Guide",
        "download_guide_pdf_part_1": "Download Part 1 Guide",
        "download_guide_pdf_part_2": "Download Part 2 Guide",
        "guide_library_title": "VIP Guide Library",
        "guide_app_title": "Onlyfans App Guide",
        "guide_part_1_title": "OnlyFans Beginner's Guide - Part 1",
        "guide_part_2_title": "OnlyFans Beginner's Guide - Part 2",
        "guide_locked_title": "Guide Access Locked",
        "guide_locked_body": "Buy Girlpire VIP to access and download this private PDF guide.",
        "guide_missing_file": "The VIP PDF guide is not available yet.",
        "guide_app_missing_file": "The app guide is not available yet.",
        "guide_part_1_missing_file": "Part 1 is not available yet.",
        "guide_part_2_missing_file": "Part 2 is not available yet.",
        "advanced_metrics": "Advanced Metrics",
        "profit_breakdown": "Profit Breakdown",
        "scenario_analysis": "Scenario Analysis",
        "strategy_score": "Strategy Score",
        "conservative": "Conservative",
        "base_case": "Base",
        "aggressive": "Aggressive",
        "status_weak": "Weak",
        "status_average": "Average",
        "status_good": "Good",
        "status_strong": "Strong",
        "footer": "Girlpire - OnlyFans Success Portal | Business-focused creator growth platform",
    },
    "tr": {
        "brand": "Girlpire",
        "hero_title": "Global Potansiyelinizi Hesaplayin",
        "hero_subtitle": "Is odakli uretici buyume platformu",
        "dashboard_workspace": "VIP Calisma Alani",
        "dashboard_top_title": "Finans Paneli",
        "dashboard_welcome": "Tekrar hos geldin, {name}",
        "dashboard_workspace_body": "Fiyatlama, retention ve olceklenebilir aylik buyumeye odaklanan ureticiler ve ajanslar icin premium gelir kontrol merkezi.",
        "dashboard_focus_chip": "Ayin odagi",
        "dashboard_sync_chip": "Canli gelir gorunumu",
        "dashboard_search_placeholder": "Aramak icin buraya dokun",
        "dashboard_nav_dashboard": "Dashboard",
        "dashboard_nav_documents": "Documents",
        "dashboard_nav_payments": "Payments",
        "dashboard_nav_calendar": "Calendar",
        "dashboard_nav_profile": "Profile",
        "dashboard_nav_darkmode": "Darkmode",
        "dashboard_nav_settings": "Settings",
        "dashboard_nav_logout": "Logout",
        "dashboard_nav_strategy": "Strateji Motoru",
        "dashboard_nav_tracking": "Ilerleme Takibi",
        "dashboard_nav_assets": "VIP Varliklari",
        "dashboard_nav_membership": "Uyelik Durumu",
        "dashboard_vip_badge": "VIP Aktif",
        "dashboard_membership_since": "VIP baslangici",
        "dashboard_membership_expires": "Erisim bitisi",
        "dashboard_membership_locked": "Rehber kutuphanesi ve ozel planlama araclari icin VIP kilidini acin.",
        "dashboard_guides_title": "Rehber Kutuphanesi",
        "dashboard_chart_selector": "Grafik gorunumu",
        "dashboard_chart_gross": "Brut gelir trendi",
        "dashboard_chart_net": "Net gelir trendi",
        "dashboard_chart_target": "Hedef ilerleme trendi",
        "dashboard_cart_toggle": "Uyelik",
        "dashboard_bell_label": "VIP",
        "dashboard_membership_tip": "Bu paneli aktif VIP erisim araliginizi dogrulamak icin kullanin.",
        "dashboard_card_growth": "Buyume Sinyali",
        "dashboard_card_margin": "Marj Kalitesi",
        "dashboard_card_arppu": "Fan Basina Gelir",
        "dashboard_card_focus": "Mevcut Oncelik",
        "dashboard_chart_title": "Aylik Performans Haritasi",
        "dashboard_chart_body": "Bu alani gelirin nerede sizdigini, sirada neyin optimize edilmesi gerektigini ve bir sonraki aylik hedefe ne kadar yakin oldugunu gormek icin kullan.",
        "vip_nav_section": "VIP Bolumleri",
        "vip_nav_dashboard": "Dashboard",
        "vip_nav_strategy": "Strateji",
        "vip_nav_tracking": "Takip",
        "vip_nav_guide": "Rehber",
        "vip_nav_advanced": "Gelismis",
        "vip_nav_calculator": "Hesaplayici",
        "vip_nav_scenarios": "Senaryolar",
        "vip_sidebar_status": "VIP Aktif",
        "language": "Dil",
        "logged_in_as": "Giris yapan kullanici",
        "logout": "Cikis Yap",
        "free_title": "OnlyFans Gelirinizi Tahmin Edin",
        "free_desc": "VIP stratejiye gecmeden once aylik ve yillik gelir tahmini icin acik hesaplayiciyi kullanin.",
        "follower_count": "Takipci Sayisi",
        "monthly_sub_price": "Aylik Abonelik Ucreti ($)",
        "expected_tips_ppv": "Beklenen Bahsis / PPV ($)",
        "target_monthly_income_input": "Hedef Aylik Gelir ($)",
        "calculate_money_engine": "Hesapla",
        "analyzing_potential": "Kazanc potansiyeliniz analiz ediliyor...",
        "gross_income": "Brut Gelir",
        "platform_fee": "Platform Komisyonu",
        "net_income": "Net Gelir",
        "yearly_net_income": "Yillik Net Gelir",
        "estimate_note": "Sonuclar yalnizca planlama ve konumlama icin tahmini degerlerdir.",
        "revenue_per_fan": "Fan Basina Gelir",
        "revenue_per_fan_value": "Fan basina {amount}",
        "arppu_low": "Fan basina geliriniz dusuk. Buyumenin cogu sadece takipciden degil, fan degerini artirmaktan gelir.",
        "arppu_mid": "Ortalama monetizasyonunuz var. PPV ve bahsisi gelistirmek icin alan bulunuyor.",
        "arppu_high": "Guclu monetizasyonunuz var. Trafik ve elde tutmayi buyutmeye odaklanin.",
        "money_gap_title": "Ayda yaklasik {amount} masada birakiyorsunuz.",
        "money_gap_body": "Daha iyi fiyatlama, PPV stratejisi ve elde tutma ile bircok uretici geliri %50+ artirir.",
        "target_engine_title": "Hedef Motoru",
        "target_engine_body": "{target}/ay hedefine ulasmak icin yaklasik {fans} odeme yapan fana ihtiyaciniz var.",
        "target_engine_warning": "Mevcut modeliniz hacme fazla bagli. Fan basi geliri artirmak kritik.",
        "potential_stage_early": "Erken asamadasiniz. Donusum ve temel monetizasyona odaklanin.",
        "potential_stage_mid": "Bir temeliniz var. Optimizasyon ciddi buyume acabilir.",
        "potential_stage_high": "Olcekleme asamasindasiniz. Elde tutma ve marja odaklanin.",
        "urgency_line": "Cogu uretici gelir modelini hic optimize etmez. Kucuk degisiklikler geliri belirgin sekilde artirabilir.",
        "cta_title": "Tahmininizi donusum planina cevirin",
        "cta_desc": "Strateji akisini hesabiniza baglamak ve gelecekteki VIP erisimini ayni e-posta ile eslestirmek icin Google girisi kullanin.",
        "get_ai_strategy": "Girlpire Stratejimi Al",
        "unlock_vip_guide": "Girlpire VIPi Ac",
        "cta_first_growth": "Buyume Stratejimi Kur",
        "cta_optimize_revenue": "Gelir Stratejimi Optimize Et",
        "cta_scale_business": "Uretici Isimi Buyut",
        "cta_email_return": "Guncel Stratejimi Gor",
        "preview_benefit_strategy": "Mevcut seviyeniz icin en yuksek etkili fiyatlama ve gelir hamlelerini gorun.",
        "preview_benefit_plan": "Haftadan haftaya tahmin etmek yerine yapilandirilmis 30 gunluk plani izleyin.",
        "preview_benefit_bible": "Konumlama, teklifler ve takip sistemini sikilastirmak icin is rehberini kullanin.",
        "preview_benefit_pricing": "Fiyatlama ve PPV kurgusunun fan basi degeri nerede artirabilecegini gorun.",
        "preview_benefit_updates": "Aylik strateji guncellemeleri ve optimizasyon fikirleri ile hizayi koruyun.",
        "social_proof_title": "Ureticiler neden bu araci kullaniyor",
        "social_proof_card_1": "Platform komisyonundan sonraki gercek net gelirinizi gorun",
        "social_proof_card_2": "Ne kadar geliri kaciriyor olabileceginizi anlayin",
        "social_proof_card_3": "Sorununuzun fiyatlama, PPV ya da trafik olup olmadigini gorun",
        "social_proof_card_4": "Reklam veya ajansa para vermeden once strateji kurun",
        "email_welcome_title": "Tekrar hos geldiniz",
        "email_ready_line": "Yeni Girlpire stratejiniz hazir.",
        "email_money_line": "Masada para birakiyor olabilirsiniz.",
        "email_login_prompt": "Stratejinize erismek icin Google ile devam edin",
        "email_paywall_prompt": "Guncellenmis Girlpire stratejiniz hazir. Erismek icin VIP kilidini acin.",
        "email_paid_prompt": "Yeni Girlpire stratejiniz asagida sizi bekliyor.",
        "upgrade_flow_title": "Girlpire strateji guncellemesi hazir",
        "upgrade_login_prompt": "Stratejinizi acmak icin Google ile devam edin",
        "upgrade_paywall_prompt": "Girlpire stratejiniz hazir. VIP erisiminizi tamamlayin.",
        "upgrade_paid_prompt": "Girlpire VIP stratejiniz asagida sizi bekliyor.",
        "login_gate_title": "Stratejinizi Acmak Icin Devam Edin",
        "login_gate_desc": "VIP karar adimina devam etmek ve gelecekteki uyeligi ayni hesapla eslemek icin Google ile giris yapin.",
        "continue_google": "Google ile Devam Et",
        "login_preview_label": "VIP On Izleme",
        "login_preview_body": "Daha net fiyatlama, daha guclu retention ve daha olceklenebilir gelir sistemi isteyen ureticiler ve ajanslar icin premium buyume plani.",
        "google_setup_missing": "Google girisi henuz yapilandirilmamis.",
        "google_setup_hint": "Yerel Streamlit girisini etkinlestirmek icin .streamlit/secrets.toml dosyasina Google OIDC degerlerini ekleyin.",
        "paywall_title": "Girlpire VIP ve Aylik Guncellemeleri Ac",
        "paywall_desc": "VIP icinde AI Strategy Consultant, 30-Day Growth Plan, The Girlpire Creator Bible ve aylik guncellemeler bulunur.",
        "pricing_anchor_title": "VIP Uyelik",
        "pricing_anchor_price": "$19/ay",
        "pricing_anchor_note": "Bir basarisiz promosyon paylasimindan veya dusuk fiyatli bir PPV paketinden daha az.",
        "vip_offer_title": "Neler Alacaksiniz:",
        "vip_offer_item_1": "Net fiyatlama stratejisi (+donusum artisi)",
        "vip_offer_item_2": "Takipcileri aliciya ceviren DM scriptleri",
        "vip_offer_item_3": "30 gunluk icerik plani",
        "vip_offer_item_4": "Adim adim monetizasyon sistemi",
        "vip_offer_item_5": "Gizli buyume taktikleri",
        "vip_offer_result_note": "Potansiyel artis uygulama kalitesi, konumlama ve kitle yapisina gore degisir.",
        "vip_pricing_message_1": "Net checkout. Gizli ucret yok.",
        "vip_pricing_message_2": "Erisim ve odeme kosullari odemeden once gosterilir.",
        "paywall_urgency": "Bugun sinirli sayida ucretsiz analiz mevcut",
        "paywall_stack_title": "VIP Uyelik Icerigi:",
        "vip_feature_strategy": "AI Strategy Consultant",
        "vip_feature_plan": "30-Day Action Plan",
        "vip_feature_bible": "Girlpire Creator Bible",
        "vip_feature_pricing": "Fiyatlama Optimizasyonu",
        "vip_feature_ppv": "PPV ve Bahsis Gelir Plani",
        "vip_feature_updates": "Aylik Strateji Guncellemeleri",
        "paywall_stack_note": "Genel tavsiye degil, is odakli buyume plani isteyen ureticiler icin tasarlandi.",
        "start_vip_membership": "🚀 Tam Stratejinin Kilidini Ac",
        "risk_reversal": "Isteginiz zaman iptal edin. Uyelik aktif oldugu surece stratejiniz erisilebilir kalir.",
        "loss_aversion_copy": "Mevcut gelir modeliniz yeterince optimize degilse, bir ay daha beklemek VIP uyelikten daha pahaliya mal olabilir.",
        "faq_title": "SSS",
        "faq_q1": "Kimligimi gostermem gerekiyor mu?",
        "faq_a1": "Hayir. Rehber anonim konumlama ve is stratejisine odaklanir.",
        "faq_q2": "Bu sadece bir hesaplayici mi?",
        "faq_a2": "Hayir. Ucretsiz hesaplayici potansiyeli tahmin eder. VIP ise strateji, rehber ve aylik optimizasyonu acar.",
        "faq_q3": "Istedigim zaman iptal edebilir miyim?",
        "faq_a3": "Evet. Abonelik yonetimi LemonSqueezy uzerinden yapilir.",
        "faq_q4": "Yapay zeka benim yerime karar verir mi?",
        "faq_a4": "Hayir. Girdilerinize gore yapilandirilmis bir is stratejisi sunar.",
        "faq_q5": "Odemem guvenli sekilde mi isleniyor?",
        "faq_a5": "Odemeler LemonSqueezy tarafindan islenir. Girlpire kart bilgisi saklamaz.",
        "unlock_vip_strategy": "🚀 Tam Stratejinin Kilidini Ac",
        "trust_checkout_line1": "Guvenli odeme LemonSqueezy tarafindan saglanir.",
        "trust_checkout_line2": "Girlpire kart bilgisi saklamaz.",
        "admin_email_tools_title": "Girlpire Admin",
        "admin_email_tools_desc": "Veritabani kullanmadan manuel aylik hatirlatmalar gondermek icin Resend kullanin.",
        "vip_active": "Girlpire VIP Aktif",
        "vip_unlocked_message": "VIP stratejinizin kilidi acildi",
        "vip_upgrade_message": "Stratejinizi acmak icin Girlpire VIP'e gecin",
        "pay_with_card": "🚀 Tam Stratejinin Kilidini Ac",
        "card_disabled_notice": "Kart odemesi simdilik kapali. Erisim acmak icin DM uzerinden bizimle iletisime gecin.",
        "pay_with_crypto": "💰 Kripto ile Kilidi Ac",
        "open_crypto_payment": "Kripto Odemesini Ac",
        "crypto_payment_ready": "Kripto odeme sayfaniz asagida hazir.",
        "crypto_step_title": "Adim 2: Kripto Odeme Sayfasini Ac",
        "crypto_step_body": "Bu odeme akisi mobil ve masaustu uyumludur. NowPayments odeme sayfasina gecmek icin asagidaki butona dokunun.",
        "crypto_payment_manual_hint": "Odeme sayfasi otomatik acilmadiysa, asagidaki butonu veya dogrudan linki kullanin.",
        "crypto_direct_link": "Dogrudan odeme linki",
        "crypto_payment_failed": "Kripto odemesi basarisiz oldu",
        "crypto_payment_unavailable": "Kripto odemelerini etkinlestirmek icin Streamlit secrets icine NOWPAYMENTS_API_KEY veya nowpayments.api_key ekleyin.",
        "crypto_disabled_notice": "Kripto odemesi simdilik kapali. Erisim acmak icin DM uzerinden bizimle iletisime gecin.",
        "add_myself_vip": "Kendimi VIP Yap",
        "vip_add_success": "Artik VIP'siniz",
        "total_users_metric": "Toplam Kullanici",
        "vip_users_metric": "VIP Kullanici",
        "all_users_title": "Tum Kullanicilar",
        "new_users_title": "Yeni Kullanicilar (7 gun)",
        "vip_users_title": "VIP Kullanicilar",
        "member_name": "Isim",
        "member_email": "E-posta",
        "member_since": "Kayit Tarihi",
        "name_missing": "-",
        "download_all_users": "Tum Uyeleri CSV Indir",
        "download_vip_users": "VIP Uyeleri CSV Indir",
        "grant_vip_title": "VIP Erisimi Ver",
        "grant_vip_desc": "Istediginiz e-posta adresine 1 aylik VIP erisimi verin.",
        "grant_vip_email": "VIP e-posta",
        "grant_vip_name": "Isim (opsiyonel)",
        "grant_vip_button": "1 Aylik VIP Ver",
        "grant_vip_success": "{email} icin 30 gunluk VIP erisimi verildi.",
        "grant_vip_failed": "VIP erisimi verilemedi. E-postayi kontrol edip tekrar deneyin.",
        "no_users_saved": "Henuz kayitli kullanici yok.",
        "no_new_users": "Son 7 gunde yeni kullanici yok.",
        "no_vip_users": "Henuz VIP kullanici yok.",
        "saved_email_count": "Kayitli E-postalar",
        "send_test_email": "Test E-postasi Gonder",
        "send_to_all_users": "Tum Kullanicilara Gonder",
        "resend_missing_key": "RESEND_API_KEY eksik. E-posta gondermek icin ortam degiskenine veya .env dosyaniza ekleyin.",
        "resend_package_missing": "resend paketi henuz kullanilabilir degil. E-posta gonderimini acmak icin proje bagimliliklarini yukleyin.",
        "email_send_success": "E-posta basariyla gonderildi.",
        "email_send_failed": "E-posta su anda gonderilemedi.",
        "email_no_user": "Test mesaji icin kullanilabilir giris yapmis bir e-posta yok.",
        "email_bulk_success": "{sent} e-posta gonderildi. Basarisiz: {failed}.",
        "email_bulk_sent_count": "E-postalar {count} kullaniciya gonderildi.",
        "emails_empty": "emails.json icinde henuz kayitli kullanici yok.",
        "email_tools_future_ready": "Bu sistem daha sonra gercek bir zamanlayici veya webhook sistemi ile degistirilebilir.",
        "monthly_email_subject": "Girlpire Stratejiniz Hazir",
        "monthly_email_heading": "Girlpire Strategy Update",
        "monthly_email_body": "Masada para birakiyor olabilirsiniz. Guncellenmis stratejiniz sizi bekliyor.",
        "monthly_email_button": "Girlpire VIPi Ac",
        "email_test_fallback_used": "Giris yapmis e-posta bulunamadi. Test e-postasi yerine yedek adrese gonderiliyor.",
        "checkout_missing": "Odeme butonunu etkinlestirmek icin secrets icine lemonsqueezy.checkout_url ekleyin.",
        "payment_notice": "VIP yalnizca gercek odeme paid user listenize senkronlandiginda veya dogrulanmis LemonSqueezy abonelik kaydi bulundugunda acilir.",
        "vip_sync_notice": "Kripto odemeleri, onaylanmis webhook Girlpire'a ulastiginda otomatik acilir. Az once odeme yaptiysaniz, bu sayfayi birkac saniye sonra yenileyin.",
        "vip_refresh_checkout_notice": "Kart odemesini yeni tamamladiysaniz, VIP erisiminizi senkronlamak icin asagidaki yenile butonunu kullanin.",
        "refresh_vip_access": "Odeme Yaptim - VIP Erisimini Yenile",
        "vip_refresh_success": "VIP erisimi bulundu ve yenilendi.",
        "vip_refresh_pending": "Henuz dogrulanmis VIP erisimi bulunamadi. Az once odeme yaptiysaniz biraz bekleyip tekrar deneyin.",
        "vip_title": "VIP Paneli",
        "vip_desc": "Bu alan yalnizca dogrulanmis aboneler icin acilir ve mevcut hesaplayici degerlerinizi baglam olarak kullanir.",
        "strategy_dashboard_title": "Uretici Strateji Paneliniz",
        "monthly_strategy_cycle_title": "Aylik Strateji Dongusu",
        "new_month_detected": "Yeni ay algilandi. Stratejinizi yenileme zamani.",
        "generate_new_monthly_strategy": "Yeni Aylik Strateji Uret",
        "focus_of_month": "Ayin Odagi",
        "focus_low": "Donusum ve monetizasyon",
        "focus_mid": "Optimizasyon",
        "focus_high": "Olcekleme ve elde tutma",
        "welcome_back": "Tekrar hos geldiniz. Son stratejinizden beri nelerin degistigine bakalim.",
        "current_net_income": "Mevcut Net Gelir",
        "target_income_metric": "Hedef Gelir",
        "gap_to_target": "Fark",
        "score_explanation_weak": "Modelinizde en az bir zayif motor var. Olcegi buyutmadan once monetizasyon kalitesini guclendirin.",
        "score_explanation_average": "Isletmenin kullanilabilir bir temeli var ancak bir veya iki gelir kolu yeterince optimize degil.",
        "score_explanation_good": "Model saglikli calisiyor. Zayif noktalar uzerinde calisin ve duzenli uygulamaya odaklanin.",
        "score_explanation_strong": "Monetizasyon motorunuz guclu. Marji koruyun ve dikkatli olceklendirin.",
        "strategy_consultant": "Yapay Zeka Strateji Danismani",
        "daily_time": "Gunluk Musait Zaman (saat)",
        "target_income": "Hedef Gelir ($)",
        "experience_level": "Deneyim Seviyesi",
        "main_challenge": "Ana Zorluk",
        "beginner": "Baslangic",
        "intermediate": "Orta",
        "advanced": "Ileri",
        "traffic": "Trafik",
        "conversion": "Donusum",
        "pricing": "Fiyatlama",
        "retention": "Elde Tutma",
        "consistency": "Tutarlilik",
        "generate_strategy": "VIP Strateji Uret",
        "strategy_generate_hint": "Anlik duzeltmeleri, gelir optimizasyonunu ve 30 gunluk plani acmak icin stratejinizi uretin.",
        "quick_strategy_title": "Akilli Strateji Motoru",
        "quick_strategy_desc": "Buyume, etkilesim, fiyat ve icerik ritminize gore hizli bir kural tabanli strateji raporu alin.",
        "quick_strategy_followers": "Takipci",
        "quick_strategy_engagement": "Etkilesim %",
        "quick_strategy_price": "Abonelik Fiyati ($)",
        "quick_strategy_posts": "Haftalik Gonderi",
        "analyze_my_strategy": "Stratejimi Analiz Et",
        "strategy_report_title": "Strateji Raporu",
        "quick_strategy_level_early": "Erken asamadasiniz. Monetizasyondan once buyumeye odaklanin.",
        "quick_strategy_level_mid": "Buyume potansiyeliniz var ancak kitleniz yeterince kullanilmiyor.",
        "quick_strategy_level_high": "Monetize edilebilir bir kitleniz var. Olceklendirmeye odaklanin.",
        "quick_strategy_engagement_low": "Etkilesiminiz dusuk. Tepkiyi artirmak icin daha guclu hook'lar ve daha keskin caption'lar kullanin.",
        "quick_strategy_engagement_mid": "Etkilesim ortalama. Tutarliligi ve story kullanimini iyilestirin.",
        "quick_strategy_engagement_high": "Etkilesim guclu. Premium teklifleri daha agresif sekilde one cikarabilirsiniz.",
        "quick_strategy_price_high": "Mevcut kitle buyuklugunuze gore fazla pahalisiniz. Donusumu artirmak icin fiyati dusurun.",
        "quick_strategy_price_low": "Dusuk fiyatliyorsunuz. Algilanan degeri guclendirirken fiyati kademeli yukseltin.",
        "quick_strategy_price_ok": "Fiyat seviyeniz mevcut seviyeniz icin uygun.",
        "quick_strategy_content_low": "Cok az paylasim yapiyorsunuz. Icerik frekansini artirin.",
        "quick_strategy_content_high": "Cok fazla paylasim yapiyorsunuz. Nicelik yerine kaliteye odaklanin.",
        "quick_strategy_content_ok": "Paylasim frekansiniz saglikli aralikta.",
        "creator_score_title": "Creator Score",
        "creator_score_underperforming": "Hesabiniz beklenen performansin altinda",
        "creator_score_untapped": "Henuz kullanilmayan buyume potansiyeliniz var",
        "creator_score_strong": "Hesap guclu, olceklendirmeye hazir",
        "quick_strategy_loss_title": "Yaklasik {amount}/ay kaciriyorsunuz",
        "quick_strategy_potential_title": "Potansiyel Buyume",
        "quick_strategy_current_label": "Mevcut",
        "quick_strategy_optimized_label": "Optimize Edilmis",
        "quick_strategy_current": "Mevcut: {amount}/ay",
        "quick_strategy_optimized": "Optimize Edilmis: {amount}/ay",
        "quick_strategy_locked": "Donusum, monetizasyon ve retention'i guclendirmek icin tam stratejinin kilidini acin",
        "quick_strategy_vip_includes": "VIP icinde sunlar var:",
        "quick_strategy_vip_item_1": "Tam monetizasyon plani",
        "quick_strategy_vip_item_2": "DM scriptleri",
        "quick_strategy_vip_item_3": "Icerik stratejisi",
        "quick_strategy_vip_item_4": "Olcekleme sistemi",
        "quick_strategy_urgency": "VIP uyeler tam planlama akisini alabilsin diye ucretsiz strateji onizlemeleri sinirlidir.",
        "quick_strategy_social_proof": "Trafik satin almadan once fiyatlama, icerik ve monetizasyon sorunlarini teshis etmek isteyen ureticiler icin tasarlandi.",
        "quick_strategy_psychology_line": "Bu fark genelde fiyatlama, konumlama veya zayif donusum mekaniklerinden gelir.",
        "mentor_analysis_title": "Strateji Analizi",
        "mentor_problems_title": "Temel Sorunlar",
        "mentor_opportunities_title": "Firsatlar",
        "mentor_next_title": "Sirada Ne Yapmalisiniz",
        "mentor_summary": "Verilerinize gore su anda **{followers} takipci**, **%{engagement} etkilesim**, **{price}** abonelik fiyati ve haftada **{posts} paylasim** ile ilerliyorsunuz.",
        "mentor_authority_1": "Sizin seviyenizdeki ureticiler fiyatlama, donusum ve tutarlilik optimize edildiginde genelde belirgin sekilde daha fazla kazanir.",
        "mentor_authority_2": "Bu desen, temel teklifini guclendirmeden olceklendirmeye calisan dusuk performansli hesaplarda cok yaygindir.",
        "mentor_biggest_mistake_label": "En buyuk hataniz",
        "mentor_biggest_mistake_low": "zayif etkilesim ve yetersiz hook gucu",
        "mentor_biggest_mistake_mid": "yeterli donusum baskisi olmayan ortalama etkilesim",
        "mentor_biggest_mistake_high": "guclu kitle sinyallerini yeterince agresif monetize etmemek",
        "mentor_problem_growth_early": "Monetizasyona tek basina yaslanmak icin cok erken asamadasiniz. Kitlenin once daha guclu buyume sinyali gormesi gerekiyor.",
        "mentor_problem_growth_mid": "Kitlenizde potansiyel var ancak mevcut ilgiyi yeterince iyi kullanmiyorsunuz.",
        "mentor_problem_growth_high": "Monetize edilebilir bir kitleniz var. Sorun artik sadece dikkat cekmek degil, uygulama ve monetizasyon derinligi.",
        "mentor_problem_engagement_low": "{followers} takipciniz var ama etkilesiminiz sadece %{engagement}; bu optimumun altinda. Icerik hook'lariniz yeterince reaksiyon cekmiyor.",
        "mentor_problem_engagement_mid": "Etkilesiminiz fena degil ancak premium donusumu maksimuma cikarmak icin hala yetersiz.",
        "mentor_problem_engagement_high": "Etkilesiminiz guclu. Bu, teklifinizi keskinlestirdiginizde daha iyi monetizasyon alinabilecegi anlamina gelir.",
        "mentor_problem_price_high": "Mevcut fiyat seviyeniz kitle buyuklugunuze gore yuksek; bu donusumu fark ettiginizden daha fazla baskiliyor olabilir.",
        "mentor_problem_price_low": "Mevcut fiyatiniz masada para birakiyor. Dusuk fiyat, sadece daha ucuz degil daha zayif algi da yaratabilir.",
        "mentor_problem_price_ok": "Su anda en buyuk sorun fiyat degil. Daha buyuk firsat donusum kalitesi ve takip yapisinda.",
        "mentor_problem_posts_low": "Paylasim ritminiz fazla zayif. Pazar tutarsizligi odullendirmez.",
        "mentor_problem_posts_high": "Cok paylasim yapiyorsunuz ama bir sonraki buyume adimi daha fazla hacim degil, daha keskin konumlama.",
        "mentor_problem_posts_ok": "Icerik frekansiniz kabul edilebilir. Buradan sonraki gelisim daha sıkı monetizasyon mekaniklerinden gelir.",
        "mentor_opportunity_growth": "Verilerinize gore en buyuk firsat, daha fazla trafik kovalamadan once takipci basi degeri artirmakta.",
        "mentor_opportunity_offer": "Teklif ve takip akisi netlestiginde mevcut kitleniz bugunkunden daha iyi donusebilir.",
        "mentor_opportunity_consistency": "Daha tutarli haftalik icerik ve satis ritmi geliri daha az rastgele, daha cok tekrar edilebilir hale getirir.",
        "mentor_step_1": "Adim 1: Her seyi bir anda degistirmek yerine once ana darbogazi duzeltin.",
        "mentor_step_2": "Adim 2: Mevcut kitlenizin satin alma ihtimalini artirmak icin fiyatlama, hook ve donusum akislarini sikilastirin.",
        "mentor_step_3": "Adim 3: Sonucu yargilamadan once ayni icerik ve monetizasyon ritmini 2-4 hafta koruyun.",
        "groq_fallback_missing": "Groq yapilandirilmamis. Yerlesik kural tabanli strateji danismani gosteriliyor.",
        "groq_fallback_failed": "Groq su anda yanit veremedi. Yerlesik kural tabanli strateji danismani gosteriliyor.",
        "immediate_fix_title": "Anlik Duzeltme (Sonraki 7 Gun)",
        "revenue_optimization_title": "Gelir Optimizasyonu",
        "growth_focus_section": "Buyume Odagi",
        "biggest_bottleneck_title": "En Buyuk Darbogaz",
        "three_point_strategy": "3 Maddelik Strateji",
        "thirty_day_plan": "30 Gunluk Plan",
        "monetization_advice": "Gelir Artirma Tavsiyesi",
        "pricing_advice": "Fiyatlama Tavsiyesi",
        "weekly_plan_title": "30 Gunluk Aksiyon Plani",
        "week1_title": "Hafta 1 -> Kurulum ve Duzeltmeler",
        "week2_title": "Hafta 2 -> Monetizasyon Itisi",
        "week3_title": "Hafta 3 -> Optimizasyon",
        "week4_title": "Hafta 4 -> Olcekleme",
        "track_progress_title": "Ilerlemenizi Takip Edin",
        "your_progress_title": "Ilerlemeniz",
        "last_month_revenue": "Gecen Ay Geliri",
        "current_subscribers": "Mevcut Abone Sayisi",
        "current_revenue_input": "Mevcut Gelir",
        "new_subscribers_gained": "Kazanilan Yeni Abone",
        "subscriber_change": "Abone Degisimi",
        "revenue_growth": "Gelir Buyume %",
        "subscriber_growth": "Buyume %",
        "progress_to_target": "Hedefe Ilerleme",
        "tracking_growth_note": "Stratejinin isi ileri tasiyip tasimadigini olcmek icin bu aylik takip girdilerini kullanin.",
        "progress_positive": "Ilerliyorsunuz. Mevcut stratejiyi surdurun.",
        "progress_negative": "Performans dustu. Stratejinizi ayarlayin.",
        "progress_mixed": "Bazi sinyaller iyilesti, bazilari zayifladi. Olceklemeden once zayif alanlari duzeltin.",
        "save_monthly_update": "Aylik Guncellemeyi Kaydet",
        "history_title": "Aylik Snapshot Gecmisi",
        "history_empty": "Gecmisi baslatmak icin ilk aylik guncellemenizi kaydedin.",
        "month": "Ay",
        "revenue": "Gelir",
        "subscribers": "Aboneler",
        "what_improved": "Ne Iyilesti",
        "what_declined": "Ne Geriledi",
        "what_to_fix_next": "Sirada Ne Duzeltilmeli",
        "nothing_improved": "Henuz buyuk bir iyilesme kaydedilmedi.",
        "nothing_declined": "Belirgin bir gerileme tespit edilmedi.",
        "fix_next_conversion": "Daha fazla erisime gitmeden once teklifinizi ve donusum yolunu guclendirin.",
        "fix_next_traffic": "En guclu teklifiniz olceklendirmeye hazir olduktan sonra daha nitelikli trafik ekleyin.",
        "fix_next_retention": "Genislemeden once takip ve geri kazanimi iyilestirerek mevcut alicilari koruyun.",
        "consistency_badge": "Tutarlilik Rozeti",
        "badge_none": "Baslamadi",
        "badge_starter": "Baslangic",
        "badge_active": "Aktif",
        "badge_consistent": "Tutarli",
        "badge_elite": "Elit",
        "previous_strategy_title": "Onceki Strateji",
        "previous_strategy_summary": "Onceki strateji ozeti",
        "previous_score": "Onceki skor",
        "previous_bottleneck": "Onceki darbogaz",
        "previous_focus": "Onceki odak",
        "what_changed_title": "Ne Degisti",
        "no_changes_yet": "Simdilik onceki goruntuye gore buyuk stratejik degisiklik yok.",
        "download_strategy_report": "Strateji Raporumu Indir",
        "bottleneck_fan_value": "Mevcut hedef icin fan basi gelir cok dusuk.",
        "bottleneck_margin": "Kar marji guvenli olcekleme icin fazla ince.",
        "bottleneck_traffic": "Ust huni trafigi buyumeyi sinirliyor.",
        "bottleneck_conversion": "Mevcut teklif, var olan kitleden yeterli degeri donusturemiyor.",
        "bottleneck_retention": "Elde tutma, buyume bilesiklesmeden once deger kaciriyor.",
        "bottleneck_system": "Uygulama tutarliligi isi geri tutuyor.",
        "growth_focus_traffic": "Odak trafik olmali. Isletmenin daha nitelikli ust huni ziyaretcisine ihtiyaci var.",
        "growth_focus_conversion": "Odak donusum olmali. Teklif daha iyi donusmeden daha fazla ziyaretci yardim etmez.",
        "growth_focus_retention": "Odak elde tutma olmali. Olceklemeden once mevcut musteri degerini koruyun ve kaybi azaltin.",
        "fix_price_audit": "Bu hafta mevcut teklif yapinizi inceleyin ve daha guclu tek bir fiyat ankraji test edin.",
        "fix_ppv_launch": "Net son teslim tarihi olan tekrarlanabilir bir PPV paketi baslatin ve alim oranini takip edin.",
        "fix_tip_goal": "Yuksek niyetli fanlar icin bir acik bahsis hedefi ve tek bir net upsell yolu belirleyin.",
        "fix_offer_refresh": "Ziyaretci odemeye gelmeden once premium degeri daha netlestirecek sekilde teklif anlatimini yenileyin.",
        "fix_conversion_path": "Her ziyaretcinin simdi abone olmak icin tek bir ana neden gormesi icin donusum yolunu sadelestirin.",
        "fix_retention_check": "Son alici kaybini inceleyin ve sessiz aboneler icin bir geri kazanim mesaji ekleyin.",
        "fix_tracking_review": "Fiyat, PPV, bahsis geliri ve churn sinyalleri icin basit bir haftalik tablo kurun.",
        "revenue_price_low": "Fiyatlama: daha guclu bir ankrajla 7 gunluk tek bir test yapin ve kalici indirimden kacinin.",
        "revenue_price_hold": "Fiyatlama: mevcut fiyati koruyun ama premium nedeni sayfanizda ve tekliflerinizde daha gorunur yapin.",
        "revenue_ppv_low": "PPV: ek gelirin rastgele degil duzenli hale gelmesi icin haftalik tek bir PPV paketi kurun.",
        "revenue_ppv_high": "PPV: en iyi calisan paketinizi sikilastirin ve gurultu yaratan dusuk donusumlu teklifleri kaldirin.",
        "revenue_tips": "Bahsis: her bahsis talebini gorunur bir hedefe veya odule baglayin ki fan ne yapacagini bilsin.",
        "week1_step1": "Sayfa vaadinizi, fiyatlama mantiginizi ve ana teklifinizi denetleyin.",
        "week1_step2": "Tek bir ana donusum mesaji belirleyin ve daha zayif mesajlari kaldirin.",
        "week1_step3": "Gelir, abone ve churn sinyalleri icin basit bir haftalik skor tablosu kurun.",
        "week2_step1": "Son tarihli tekrarlanabilir tek bir PPV paketi baslatin.",
        "week2_step2": "Anlasilmasi kolay bir bahsis hedefi veya yukseltilmis teklif yolu ekleyin.",
        "week2_step3": "Mevcut kitlenize tek bir net premium teklif gonderin.",
        "week3_step1": "Sadece brut gelire degil, alim orani, donusum ve net gelire bakin.",
        "week3_step2": "En guclu teklifi koruyun ve en az bir dusuk getirili isi kesin.",
        "week3_step3": "Kaybin en yuksek oldugu satin alma yolunu iyilestirin.",
        "week4_step1": "Ay icinde en iyi sonuc veren teklifi iki kat guclendirin.",
        "week4_step2": "Sadece nitelikli talep getiren tek kanala dikkatli sekilde yeniden yatirim yapin.",
        "week4_step3_traffic": "Sadece odeme yapan fana duzenli donusen trafik kaynagini olceklendirin.",
        "week4_step3_conversion": "Sayfa vaadi ve abonelik donusumu iyilesmeden olceklendirmeyin.",
        "week4_step3_retention": "Elde tutma ve tekrar satin alma davranisi oturmadan olceklendirmeyin.",
        "change_score_up": "Strateji skorunuz {points} puan iyilesti.",
        "change_score_down": "Strateji skorunuz {points} puan dustu.",
        "change_bottleneck": "Ana darbogaz '{previous}' seviyesinden '{current}' seviyesine degisti.",
        "change_focus": "Buyume odagi '{previous}' seviyesinden '{current}' seviyesine kaydi.",
        "vip_guide_title": "The Girlpire Creator Bible",
        "vip_guide_desc": "Konumlama, fiyatlama, gelir artirma ve haftalik takip icin ozel is rehberini indirin.",
        "download_guide": "Rehberi Indir",
        "download_guide_pdf": "VIP PDF Rehberini Indir",
        "download_guide_pdf_app": "App Rehberini Indir",
        "download_guide_pdf_part_1": "1. Bolum Rehberini Indir",
        "download_guide_pdf_part_2": "2. Bolum Rehberini Indir",
        "guide_library_title": "VIP Rehber Kutuphanesi",
        "guide_app_title": "Onlyfans App Guide",
        "guide_part_1_title": "OnlyFans Beginner's Guide - Part 1",
        "guide_part_2_title": "OnlyFans Beginner's Guide - Part 2",
        "guide_locked_title": "Rehber Erisimi Kilitli",
        "guide_locked_body": "Bu ozel PDF rehbere erismek ve indirmek icin Girlpire VIP satin alin.",
        "guide_missing_file": "VIP PDF rehberi henuz kullanilabilir degil.",
        "guide_app_missing_file": "App rehberi henuz kullanilabilir degil.",
        "guide_part_1_missing_file": "1. bolum henuz kullanilabilir degil.",
        "guide_part_2_missing_file": "2. bolum henuz kullanilabilir degil.",
        "advanced_metrics": "Gelismis Metrikler",
        "profit_breakdown": "Kar Dagilimi",
        "scenario_analysis": "Senaryo Analizi",
        "strategy_score": "Strateji Skoru",
        "conservative": "Temkinli",
        "base_case": "Baz",
        "aggressive": "Agresif",
        "status_weak": "Zayif",
        "status_average": "Orta",
        "status_good": "Iyi",
        "status_strong": "Guclu",
        "footer": "Girlpire - OnlyFans Success Portal | Is odakli uretici buyume platformu",
    },
}


st.set_page_config(page_title=APP_TITLE, layout="wide")

# Girlpire Admin Access (MVP Level)
# Access is limited to the verified Google account email.
# Replace with proper role-based authentication in production.


def init_state() -> None:
    st.session_state.setdefault("language", "en")
    st.session_state.setdefault("clicked_cta", False)
    st.session_state.setdefault("premium_unlocked", False)
    st.session_state.setdefault("from_email", False)
    st.session_state.setdefault("upgrade_flow", False)
    st.session_state.setdefault("strategy_result", None)
    st.session_state.setdefault("previous_strategy_result", None)
    st.session_state.setdefault("money_engine_result", None)
    st.session_state.setdefault("strategy_cycle_month", "")
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("progress_update_count", 0)
    st.session_state.setdefault("last_visit_date", "")


def t(key: str) -> str:
    language = st.session_state.get("language", "en")
    return (
        TRANSLATIONS.get(language, {}).get(key)
        or TRANSLATIONS["en"].get(key)
        or key
    )


def sync_language_from_query_params() -> None:
    params = getattr(st, "query_params", None)
    if params is None:
        return

    raw_language = params.get("lang", "")
    if isinstance(raw_language, (list, tuple)):
        raw_language = raw_language[0] if raw_language else ""
    selected_language = str(raw_language).strip().lower()
    if selected_language in LANGUAGE_OPTIONS:
        st.session_state["language"] = selected_language


def render_language_selector(widget_key: str) -> None:
    current_language = str(st.session_state.get("language", "en")).strip().lower()
    if current_language not in LANGUAGE_OPTIONS:
        current_language = "en"
        st.session_state["language"] = current_language

    selected_language = st.selectbox(
        t("language"),
        options=list(LANGUAGE_OPTIONS.keys()),
        index=list(LANGUAGE_OPTIONS.keys()).index(current_language),
        format_func=lambda code: LANGUAGE_OPTIONS[code],
        key=widget_key,
        label_visibility="collapsed",
    )

    if selected_language != current_language:
        st.session_state["language"] = selected_language
        params = getattr(st, "query_params", None)
        if params is not None:
            params["lang"] = selected_language
        st.rerun()


def secret_get(*keys: str, default=None):
    current = st.secrets
    try:
        for key in keys:
            current = current[key]
        return current
    except Exception:
        return default


def admin_mode_enabled() -> bool:
    try:
        return bool(st.secrets.get("app", {}).get("admin_mode", False))
    except Exception:
        return False


def auth_is_supported() -> bool:
    return all(hasattr(st, attr) for attr in ("login", "logout", "user"))


def has_real_secret_value(value: object) -> bool:
    normalized = str(value or "").strip()
    if not normalized:
        return False
    placeholders = (
        "CHANGE_THIS_",
        "CHANGE_ME_",
        "PASTE_",
        "YOUR_",
        "GOOGLE_CLIENT_ID_HERE",
        "GOOGLE_CLIENT_SECRET_HERE",
    )
    return not any(token in normalized for token in placeholders)


def auth_is_configured() -> bool:
    required = (
        secret_get("auth", "redirect_uri"),
        secret_get("auth", "cookie_secret"),
        secret_get("auth", "google", "client_id"),
        secret_get("auth", "google", "client_secret"),
        secret_get("auth", "google", "server_metadata_url"),
    )
    return all(has_real_secret_value(value) for value in required)


def google_login_ready() -> bool:
    try:
        return bool(
            has_real_secret_value(st.secrets["auth"]["google"]["client_id"])
            and has_real_secret_value(st.secrets["auth"]["google"]["client_secret"])
        )
    except Exception:
        return False


def is_logged_in() -> bool:
    if not auth_is_supported():
        return False
    user = getattr(st, "user", None)
    return bool(getattr(user, "is_logged_in", False))


def get_user_claim(claim: str, default: str = "") -> str:
    user = getattr(st, "user", None)
    if user is None:
        return default
    try:
        value = user[claim]
        return value if value is not None else default
    except Exception:
        value = getattr(user, claim, default)
        return value if value is not None else default


def get_current_user_email() -> str:
    return str(get_user_claim("email", "")).strip().lower()


def get_current_user_name() -> str:
    return " ".join(str(get_user_claim("name", "")).strip().split())


def get_admin_email() -> str:
    return str(secret_get("admin_email", default="eyupozbey77@gmail.com") or "").strip().lower()


def is_admin_user(user_email: str | None) -> bool:
    normalized_email = str(user_email or "").strip().lower()
    admin_email = get_admin_email()
    return bool(normalized_email and admin_email and normalized_email == admin_email)


def detect_email_traffic() -> None:
    params = getattr(st, "query_params", None)
    if params is None:
        return

    try:
        source = params.get("from", "")
    except Exception:
        source = ""

    if isinstance(source, (list, tuple)):
        source = source[0] if source else ""

    if str(source).strip().lower() == "email":
        st.session_state["from_email"] = True

    try:
        action = params.get("action", "")
    except Exception:
        action = ""

    if isinstance(action, (list, tuple)):
        action = action[0] if action else ""

    if str(action).strip().lower() == "upgrade":
        st.session_state["upgrade_flow"] = True


def is_from_email() -> bool:
    return bool(st.session_state.get("from_email", False))


def is_upgrade_flow() -> bool:
    return bool(st.session_state.get("upgrade_flow", False))


def today_iso_date() -> str:
    return datetime.now().date().isoformat()


def normalize_email_list(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    normalized_items: list[str] = []
    seen: set[str] = set()
    for item in items:
        email = str(item).strip().lower()
        if email and email not in seen:
            normalized_items.append(email)
            seen.add(email)
    return normalized_items


def normalize_vip_memberships(items: object) -> dict[str, dict[str, str]]:
    if not isinstance(items, dict):
        return {}

    normalized: dict[str, dict[str, str]] = {}
    for raw_email, raw_value in items.items():
        email = str(raw_email).strip().lower()
        if not email:
            continue

        if isinstance(raw_value, dict):
            started_at = str(raw_value.get("started_at", today_iso_date())).strip()
            expires_at = str(raw_value.get("expires_at", "")).strip()
        else:
            started_at = today_iso_date()
            expires_at = ""

        try:
            started_date = datetime.fromisoformat(started_at).date()
        except ValueError:
            started_date = datetime.now().date()

        if expires_at:
            try:
                expires_date = datetime.fromisoformat(expires_at).date()
            except ValueError:
                expires_date = started_date + timedelta(days=30)
        else:
            expires_date = started_date + timedelta(days=30)

        normalized[email] = {
            "started_at": started_date.isoformat(),
            "expires_at": expires_date.isoformat(),
        }

    return normalized


def normalize_user_records(items: object) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []

    normalized_records: list[dict[str, str]] = []
    seen: set[str] = set()
    default_created_at = today_iso_date()
    for item in items:
        if isinstance(item, dict):
            email = str(item.get("email", "")).strip().lower()
            name = " ".join(str(item.get("name", "")).strip().split())
            created_at = str(item.get("created_at", default_created_at)).strip()
        else:
            email = str(item).strip().lower()
            name = ""
            created_at = default_created_at
        if not email or email in seen:
            continue
        try:
            created_at = datetime.fromisoformat(created_at).date().isoformat()
        except ValueError:
            created_at = default_created_at
        normalized_records.append(
            {
                "name": name,
                "email": email,
                "created_at": created_at,
            }
        )
        seen.add(email)
    return normalized_records


def ensure_emails_file() -> bool:
    default_data = {"users": [], "paid_users": [], "vip_memberships": {}}
    if EMAILS_FILE.exists():
        return True
    try:
        EMAILS_FILE.write_text(
            json.dumps(default_data, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def ensure_email_store() -> dict[str, object]:
    default_data = {"users": [], "paid_users": [], "vip_memberships": {}}
    if not ensure_emails_file():
        return default_data

    try:
        data = json.loads(EMAILS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_data

    return {
        "users": normalize_user_records(data.get("users", [])),
        "paid_users": normalize_email_list(data.get("paid_users", [])),
        "vip_memberships": normalize_vip_memberships(data.get("vip_memberships", {})),
    }


def write_email_store(data: dict[str, object]) -> bool:
    payload = {
        "users": normalize_user_records(data.get("users", [])),
        "paid_users": normalize_email_list(data.get("paid_users", [])),
        "vip_memberships": normalize_vip_memberships(data.get("vip_memberships", {})),
    }
    try:
        EMAILS_FILE.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return True
    except OSError:
        return False


def _derive_membership_details(
    email_store: dict[str, object], normalized_email: str
) -> dict[str, str]:
    if not normalized_email:
        return {"started_at": "", "expires_at": ""}

    paid_users = set(email_store.get("paid_users", []))
    vip_memberships = dict(email_store.get("vip_memberships", {}))
    membership = vip_memberships.get(normalized_email)

    if not membership and normalized_email not in paid_users:
        return {"started_at": "", "expires_at": ""}

    if isinstance(membership, dict):
        started_at = str(membership.get("started_at", "")).strip()
        expires_at = str(membership.get("expires_at", "")).strip()
        if started_at and expires_at:
            return {"started_at": started_at, "expires_at": expires_at}

    users = list(email_store.get("users", []))
    for user_record in users:
        if str(user_record.get("email", "")).strip().lower() != normalized_email:
            continue
        started_at = str(user_record.get("created_at", today_iso_date())).strip()
        try:
            started_date = datetime.fromisoformat(started_at).date()
        except ValueError:
            started_date = datetime.now().date()
        return {
            "started_at": started_date.isoformat(),
            "expires_at": (started_date + timedelta(days=30)).isoformat(),
        }

    return {"started_at": "", "expires_at": ""}


def vip_membership_is_active(
    email_store: dict[str, object], email: str, *, reference_date: datetime | None = None
) -> bool:
    normalized_email = str(email or "").strip().lower()
    membership = _derive_membership_details(email_store, normalized_email)
    expires_at = str(membership.get("expires_at", "")).strip()
    if not expires_at:
        return False

    try:
        expires_date = datetime.fromisoformat(expires_at).date()
    except ValueError:
        return False

    today_date = (reference_date or datetime.now()).date()
    return expires_date >= today_date


def prune_expired_paid_users(email_store: dict[str, object]) -> dict[str, object]:
    paid_users = list(email_store.get("paid_users", []))
    active_paid_users = [
        email for email in paid_users if vip_membership_is_active(email_store, email)
    ]
    if active_paid_users == paid_users:
        return email_store

    updated_store = {
        "users": list(email_store.get("users", [])),
        "paid_users": active_paid_users,
        "vip_memberships": dict(email_store.get("vip_memberships", {})),
    }
    write_email_store(updated_store)
    return updated_store


def upsert_user_record(users: list[dict[str, str]], email: str, name: str = "") -> tuple[list[dict[str, str]], bool]:
    normalized_email = str(email).strip().lower()
    normalized_name = " ".join(str(name).strip().split())
    if not normalized_email:
        return users, False

    updated_users = list(users)
    for index, user_record in enumerate(updated_users):
        record_email = str(user_record.get("email", "")).strip().lower()
        if record_email != normalized_email:
            continue
        current_name = " ".join(str(user_record.get("name", "")).strip().split())
        if normalized_name and normalized_name != current_name:
            updated_record = dict(user_record)
            updated_record["name"] = normalized_name
            updated_users[index] = updated_record
            return updated_users, True
        return updated_users, False

    updated_users.append(
        {
            "name": normalized_name,
            "email": normalized_email,
            "created_at": today_iso_date(),
        }
    )
    return updated_users, True


def save_user_email(email: str, name: str = "") -> bool:
    normalized_email = str(email).strip().lower()
    if not normalized_email:
        return False

    email_store = ensure_email_store()
    users = list(email_store.get("users", []))
    users, changed = upsert_user_record(users, normalized_email, name)
    if not changed:
        return False

    return write_email_store(
        {
            "users": users,
            "paid_users": email_store.get("paid_users", []),
            "vip_memberships": email_store.get("vip_memberships", {}),
        }
    )


def load_paid_users() -> list[str]:
    email_store = prune_expired_paid_users(ensure_email_store())
    return list(email_store.get("paid_users", []))


def add_paid_user(email: str, name: str = "") -> bool:
    normalized_email = str(email).strip().lower()
    if not normalized_email:
        return False

    email_store = ensure_email_store()
    paid_users = list(email_store.get("paid_users", []))
    vip_memberships = dict(email_store.get("vip_memberships", {}))
    if normalized_email in paid_users:
        users = list(email_store.get("users", []))
        users, _ = upsert_user_record(users, normalized_email, name)
        start_date = datetime.now().date()
        vip_memberships[normalized_email] = {
            "started_at": start_date.isoformat(),
            "expires_at": (start_date + timedelta(days=30)).isoformat(),
        }
        return write_email_store(
            {"users": users, "paid_users": paid_users, "vip_memberships": vip_memberships}
        )

    paid_users.append(normalized_email)
    users = list(email_store.get("users", []))
    users, _ = upsert_user_record(users, normalized_email, name)
    start_date = datetime.now().date()
    vip_memberships[normalized_email] = {
        "started_at": start_date.isoformat(),
        "expires_at": (start_date + timedelta(days=30)).isoformat(),
    }
    return write_email_store(
        {"users": users, "paid_users": paid_users, "vip_memberships": vip_memberships}
    )


def grant_vip_membership(email: str, name: str = "", days: int = 30) -> bool:
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return False

    try:
        duration_days = max(int(days), 1)
    except (TypeError, ValueError):
        duration_days = 30

    email_store = ensure_email_store()
    paid_users = list(email_store.get("paid_users", []))
    users = list(email_store.get("users", []))
    vip_memberships = dict(email_store.get("vip_memberships", {}))

    if normalized_email not in paid_users:
        paid_users.append(normalized_email)

    users, _ = upsert_user_record(users, normalized_email, name)
    start_date = datetime.now().date()
    vip_memberships[normalized_email] = {
        "started_at": start_date.isoformat(),
        "expires_at": (start_date + timedelta(days=duration_days)).isoformat(),
    }
    return write_email_store(
        {"users": users, "paid_users": paid_users, "vip_memberships": vip_memberships}
    )


def get_vip_membership_details(email: str) -> dict[str, str]:
    normalized_email = str(email).strip().lower()
    if not normalized_email:
        return {"started_at": "", "expires_at": ""}

    email_store = ensure_email_store()
    return _derive_membership_details(email_store, normalized_email)


def build_admin_member_rows(user_records: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for user_record in user_records:
        rows.append(
            {
                t("member_name"): str(user_record.get("name", "")).strip() or t("name_missing"),
                t("member_email"): str(user_record.get("email", "")).strip().lower(),
                t("member_since"): str(user_record.get("created_at", "")).strip(),
            }
        )
    return rows


def build_vip_member_records(
    user_records: list[dict[str, str]], paid_users: list[str]
) -> list[dict[str, str]]:
    user_map = {
        str(user_record.get("email", "")).strip().lower(): user_record
        for user_record in user_records
    }
    vip_records: list[dict[str, str]] = []
    for paid_email in paid_users:
        normalized_email = str(paid_email).strip().lower()
        user_record = dict(user_map.get(normalized_email, {}))
        if not user_record:
            user_record = {
                "name": "",
                "email": normalized_email,
                "created_at": "",
            }
        vip_records.append(user_record)
    return vip_records


def build_members_csv(user_records: list[dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([t("member_name"), t("member_email"), t("member_since")])
    for row in build_admin_member_rows(user_records):
        writer.writerow([row[t("member_name")], row[t("member_email")], row[t("member_since")]])
    return output.getvalue()


def get_app_url() -> str:
    return str(
        secret_get(
            "app",
            "app_url",
            default=os.environ.get("APP_URL", "http://localhost:8501"),
        )
        or "http://localhost:8501"
    ).strip()


def build_email_return_url(action: str = "") -> str:
    base_url = get_app_url() or "http://localhost:8501"
    split_url = urlsplit(base_url)
    params = dict(parse_qsl(split_url.query, keep_blank_values=True))
    params["from"] = "email"
    if action:
        params["action"] = action
    query = urlencode(params, doseq=True)
    return urlunsplit(
        (
            split_url.scheme or "http",
            split_url.netloc or "localhost:8501",
            split_url.path or "/",
            query,
            split_url.fragment,
        )
    )


def build_app_url_with_params(**params: str | None) -> str:
    base_url = get_app_url() or "http://localhost:8501"
    split_url = urlsplit(base_url)
    query_params = dict(parse_qsl(split_url.query, keep_blank_values=True))
    current_language = str(st.session_state.get("language", "en")).strip().lower()
    if current_language in LANGUAGE_OPTIONS:
        query_params["lang"] = current_language
    for key, value in params.items():
        if value is None:
            query_params.pop(key, None)
        else:
            query_params[key] = str(value)
    query = urlencode(query_params, doseq=True)
    return urlunsplit(
        (
            split_url.scheme or "http",
            split_url.netloc or "localhost:8501",
            split_url.path or "/",
            query,
            "vip-content",
        )
    )


def get_vip_section_options() -> dict[str, str]:
    return {
        "dashboard": t("vip_nav_dashboard"),
        "calculator": t("vip_nav_calculator"),
        "strategy": t("vip_nav_strategy"),
        "tracking": t("vip_nav_tracking"),
        "scenarios": t("vip_nav_scenarios"),
        "guide": t("vip_nav_guide"),
        "advanced": t("vip_nav_advanced"),
    }


def sync_vip_section_from_query_params() -> str:
    options = get_vip_section_options()
    params = getattr(st, "query_params", None)
    selected = str(st.session_state.get("vip_section", "dashboard"))

    if params is not None:
        raw_section = params.get("vip_section", "")
        if isinstance(raw_section, (list, tuple)):
            raw_section = raw_section[0] if raw_section else ""
        normalized = str(raw_section).strip().lower()
        if normalized in options:
            selected = normalized

        raw_action = params.get("vip_action", "")
        if isinstance(raw_action, (list, tuple)):
            raw_action = raw_action[0] if raw_action else ""
        if str(raw_action).strip().lower() == "logout" and is_logged_in():
            st.logout()

    if selected not in options:
        selected = "dashboard"

    st.session_state["vip_section"] = selected
    return selected


def get_resend_api_key() -> str:
    return str(RESEND_API_KEY or "").strip()


def get_test_email_fallback() -> str:
    return "delivered@resend.dev"


def build_monthly_email_content() -> str:
    app_url = html.escape(build_email_return_url("upgrade"), quote=True)
    return f"""
<h2>Girlpire Strategy Update</h2>
<p>Your new strategy is ready.</p>
<p>You may be leaving money on the table.</p>

<a href="{app_url}"
style="
display:inline-block;
padding:12px 20px;
background-color:#d4af37;
color:black;
text-decoration:none;
border-radius:6px;
font-weight:bold;
">
{html.escape(t("monthly_email_button"))}
</a>
    """


def send_email(to_email: str, subject: str, content: str) -> tuple[bool, str]:
    if resend is None:
        return False, t("resend_package_missing")

    api_key = get_resend_api_key()
    if not api_key:
        return False, t("resend_missing_key")

    try:
        resend.api_key = api_key
        resend.Emails.send(
            {
                "from": "Girlpire <onboarding@resend.dev>",
                "to": [to_email],
                "subject": subject,
                "html": content,
            }
        )
        return True, t("email_send_success")
    except Exception as exc:
        return False, f"{t('email_send_failed')} {exc}"


def send_to_all_users() -> tuple[int, int]:
    # This system can later be replaced with a real scheduler or webhook system.
    email_store = ensure_email_store()
    users = email_store.get("users", [])
    if not users:
        return 0, 0

    subject = t("monthly_email_subject")
    content = build_monthly_email_content()
    sent = 0
    failed = 0
    for user_record in users:
        user_email = str(user_record.get("email", "")).strip().lower()
        if not user_email:
            failed += 1
            continue
        success, _ = send_email(user_email, subject, content)
        if success:
            sent += 1
        else:
            failed += 1
    return sent, failed


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_compact_currency(value: float) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"${value / 1_000_000:.1f}m"
    if absolute >= 1_000:
        return f"${value / 1_000:.1f}k"
    return f"${value:,.0f}"


def clamp_percentage(value: float) -> int:
    return max(0, min(int(round(value)), 100))


def render_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --wolf-bg: #0b0f19;
            --wolf-surface: #121827;
            --wolf-surface-soft: #182032;
            --wolf-primary: #9f7aea;
            --wolf-accent: #f472b6;
            --wolf-text: #e6eaf2;
            --wolf-muted: #a3afc3;
            --wolf-border: rgba(159, 122, 234, 0.26);
            --wolf-shadow: 0 26px 90px rgba(3, 6, 15, 0.45);
        }

        html, body, [class*="css"] {
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(159, 122, 234, 0.20), transparent 34%),
                radial-gradient(circle at top right, rgba(244, 114, 182, 0.10), transparent 28%),
                linear-gradient(180deg, #0b0f19 0%, #0e1320 48%, #0a0f1a 100%);
            color: var(--wolf-text);
        }

        [data-testid="stHeader"] {
            background: rgba(11, 15, 25, 0.72);
            border-bottom: 1px solid rgba(159, 122, 234, 0.14);
        }

        [data-testid="stSidebar"] {
            background: rgba(10, 14, 24, 0.96);
            border-right: 1px solid rgba(159, 122, 234, 0.12);
        }

        [data-testid="stAppViewContainer"] {
            background: transparent;
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4 {
            color: var(--wolf-text);
            letter-spacing: -0.03em;
            font-weight: 800;
        }

        p, label, .stCaption, .stMarkdown, .st-emotion-cache-10trblm {
            color: var(--wolf-text);
        }

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(159, 122, 234, 0.40),
                transparent
            );
            margin: 1.4rem 0;
        }

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button,
        .stLinkButton > a {
            width: 100%;
            min-height: 3.2rem;
            border-radius: 18px;
            border: 1px solid rgba(221, 203, 255, 0.36);
            background: linear-gradient(135deg, #9f7aea 0%, #b794f4 52%, #f472b6 100%);
            color: #0b0f19 !important;
            font-weight: 800;
            box-shadow: 0 18px 44px rgba(159, 122, 234, 0.28);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            text-decoration: none !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover {
            transform: translateY(-1px);
            box-shadow: 0 24px 52px rgba(159, 122, 234, 0.34);
            border-color: rgba(255, 225, 248, 0.52);
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus,
        .stDownloadButton > button:focus,
        .stLinkButton > a:focus {
            box-shadow:
                0 0 0 1px rgba(255, 255, 255, 0.04),
                0 0 0 4px rgba(159, 122, 234, 0.20),
                0 18px 44px rgba(159, 122, 234, 0.28);
        }

        .stFormSubmitButton > button {
            color: #0b0f19 !important;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            min-height: 3.15rem;
            border-radius: 18px;
            background: rgba(10, 14, 24, 0.92);
            border: 1px solid rgba(159, 122, 234, 0.22);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }

        div[data-baseweb="select"] input,
        div[data-baseweb="input"] input {
            color: var(--wolf-text) !important;
        }

        [data-testid="stForm"],
        .wolf-hero,
        .wolf-card,
        .wolf-metric,
        .wolf-userbox,
        .wolf-email-banner {
            border-radius: 28px;
            border: 1px solid var(--wolf-border);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(16, 22, 38, 0.94)),
                linear-gradient(135deg, rgba(159, 122, 234, 0.08), rgba(244, 114, 182, 0.03));
            box-shadow: var(--wolf-shadow);
            animation: wolfFadeUp 0.45s ease both;
        }

        .wolf-shell {
            padding-bottom: 2rem;
        }

        [data-testid="stForm"] {
            padding: 1.05rem 1rem 0.3rem;
            margin: 0.9rem 0 1.2rem;
        }

        .wolf-hero {
            padding: clamp(1.35rem, 4vw, 2.4rem);
        }

        .wolf-logo-lockup {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .wolf-logo-lockup-compact {
            gap: 0.8rem;
        }

        .wolf-logo-wordmark {
            width: min(100%, 168px);
            height: auto;
            display: block;
            filter: drop-shadow(0 18px 40px rgba(3, 6, 15, 0.36));
            border-radius: 30px;
        }

        .wolf-logo-wordmark-sm {
            width: min(100%, 66px);
        }

        .wolf-logo-symbol-badge {
            width: 76px;
            height: 76px;
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .wolf-logo-symbol {
            width: 100%;
            height: 100%;
            object-fit: contain;
            border-radius: 24px;
            box-shadow: 0 18px 48px rgba(3, 6, 15, 0.28);
        }

        .wolf-brand-stack {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
            align-items: flex-start;
        }

        .wolf-brand-stack-center {
            align-items: flex-start;
        }

        .wolf-brand-title-lg {
            color: var(--wolf-text);
            font-size: clamp(2rem, 5vw, 3.25rem);
            line-height: 0.94;
            letter-spacing: 0.18em;
            font-weight: 300;
            text-transform: lowercase;
        }

        .wolf-brand-title-sm {
            color: var(--wolf-text);
            font-size: 1.28rem;
            line-height: 1;
            letter-spacing: 0.14em;
            font-weight: 300;
            text-transform: lowercase;
        }

        .wolf-brand-tagline {
            color: #f7b2c6;
            font-size: 0.8rem;
            letter-spacing: 0.38em;
            text-transform: uppercase;
            opacity: 0.9;
        }

        .wolf-brand-tagline-sm {
            font-size: 0.62rem;
            letter-spacing: 0.28em;
        }

        .wolf-card,
        .wolf-userbox {
            padding: 1.1rem;
            margin-bottom: 1rem;
        }

        .wolf-vip-sidebar-shell {
            min-height: calc(100vh - 12rem);
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .wolf-vip-sidebar-profile {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 0.45rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(159, 122, 234, 0.18);
        }

        .wolf-vip-sidebar-brand {
            margin-bottom: 0.4rem;
        }

        .wolf-vip-sidebar-name {
            color: var(--wolf-text);
            font-weight: 800;
            font-size: 1rem;
        }

        .wolf-vip-sidebar-email {
            color: var(--wolf-muted);
            font-size: 0.82rem;
            word-break: break-word;
        }

        .wolf-vip-sidebar-chip {
            margin-top: 0.15rem;
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            background: rgba(159, 122, 234, 0.16);
            border: 1px solid rgba(159, 122, 234, 0.26);
            color: #f2eaff;
            font-size: 0.76rem;
            font-weight: 700;
        }

        .wolf-vip-sidebar-nav,
        .wolf-vip-sidebar-bottom {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }

        .wolf-vip-sidebar-bottom {
            margin-top: auto;
        }

        .wolf-vip-nav-item {
            display: block;
            width: 100%;
            border-radius: 16px;
            padding: 0.9rem 1rem;
            text-decoration: none;
            color: var(--wolf-muted);
            background: rgba(16, 23, 38, 0.68);
            border: 1px solid transparent;
            font-weight: 700;
            transition: 0.2s ease;
        }

        .wolf-vip-nav-item:hover {
            color: var(--wolf-text);
            border-color: rgba(159, 122, 234, 0.28);
            background: rgba(28, 36, 58, 0.88);
        }

        .wolf-vip-nav-active {
            color: #f4edff;
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.34), rgba(168, 85, 247, 0.20));
            border-color: rgba(159, 122, 234, 0.40);
            box-shadow: inset 3px 0 0 #9f7aea;
        }

        .wolf-vip-nav-logout {
            color: #ff7f95;
        }

        .wolf-email-banner {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at top right, rgba(244, 114, 182, 0.20), transparent 34%),
                linear-gradient(180deg, rgba(159, 122, 234, 0.13), rgba(16, 22, 38, 0.95));
            padding: 1.2rem 1.2rem 1.1rem;
            margin: 0.35rem 0 1rem;
        }

        .wolf-email-highlight {
            color: #f6c8e4;
            font-weight: 700;
            margin-top: 0.65rem;
        }

        .wolf-dashboard-brandbar {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            min-height: 3rem;
        }

        .wolf-dashboard-brand-meta {
            display: flex;
            flex-direction: column;
            gap: 0.18rem;
        }

        .wolf-dashboard-brand-title {
            color: var(--wolf-text);
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .wolf-dashboard-brand-subtitle {
            color: var(--wolf-muted);
            font-size: 0.78rem;
        }

        .wolf-banner-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            min-height: 3.2rem;
            border-radius: 18px;
            border: 1px solid rgba(221, 203, 255, 0.36);
            background: linear-gradient(135deg, #9f7aea 0%, #b794f4 52%, #f472b6 100%);
            color: #0b0f19 !important;
            font-weight: 800;
            text-decoration: none !important;
            box-shadow: 0 18px 44px rgba(159, 122, 234, 0.28);
            margin: 0.2rem 0 0.5rem;
        }

        .wolf-metric {
            padding: 1.15rem;
            margin-bottom: 1rem;
            min-height: 164px;
        }

        .wolf-brand {
            display: inline-flex;
            align-items: center;
            padding: 0.48rem 0.82rem;
            border-radius: 999px;
            border: 1px solid var(--wolf-border);
            background: rgba(159, 122, 234, 0.12);
            color: #d7c8ff;
            font-size: 0.8rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .wolf-panel-label {
            margin-bottom: 0.45rem;
            color: var(--wolf-muted);
            font-size: 0.76rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .wolf-title {
            margin: 0.95rem 0 0.5rem;
            font-size: clamp(2.2rem, 6vw, 4rem);
            line-height: 0.98;
            color: var(--wolf-text);
            max-width: 12ch;
        }

        .wolf-subtitle,
        .wolf-muted {
            color: var(--wolf-muted);
            line-height: 1.7;
        }

        .wolf-subtitle {
            max-width: 54ch;
            font-size: clamp(0.98rem, 2.4vw, 1.08rem);
        }

        .wolf-card h3,
        .wolf-inline-title {
            margin: 0 0 0.55rem;
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--wolf-text);
        }

        .wolf-metric-label {
            font-size: 0.84rem;
            color: var(--wolf-muted);
            text-transform: uppercase;
            letter-spacing: 0.09em;
            margin-bottom: 0.8rem;
            font-weight: 700;
        }

        .wolf-metric-value {
            font-size: clamp(1.7rem, 5vw, 2.55rem);
            color: var(--wolf-text);
            font-weight: 800;
            line-height: 1.1;
        }

        .wolf-metric-note {
            margin-top: 0.75rem;
            color: #d8c9ff;
            font-size: 0.88rem;
        }

        .wolf-list {
            margin: 0;
            padding-left: 1.05rem;
            line-height: 1.8;
            color: var(--wolf-text);
        }

        .wolf-list li + li {
            margin-top: 0.42rem;
        }

        .wolf-user-meta {
            display: flex;
            align-items: center;
            gap: 0.95rem;
            margin-bottom: 1rem;
        }

        .wolf-avatar,
        .wolf-avatar-img {
            width: 64px;
            height: 64px;
            border-radius: 20px;
            flex-shrink: 0;
        }

        .wolf-avatar {
            border: 1px solid var(--wolf-border);
            background: linear-gradient(135deg, rgba(159, 122, 234, 0.24), rgba(244, 114, 182, 0.18));
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--wolf-text);
            font-size: 1rem;
            font-weight: 800;
        }

        .wolf-avatar-img {
            object-fit: cover;
            border: 1px solid rgba(255, 255, 255, 0.10);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.24);
        }

        .wolf-user-name {
            color: var(--wolf-text);
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.2;
        }

        .wolf-user-email {
            color: var(--wolf-muted);
            font-size: 0.92rem;
            margin-top: 0.25rem;
            word-break: break-word;
        }

        .wolf-login-hero {
            margin-top: clamp(1.6rem, 5vw, 3.8rem);
        }

        .wolf-login-copy {
            max-width: 44rem;
        }

        .wolf-login-grid {
            margin-top: 1rem;
        }

        .wolf-login-side-label {
            margin: 0.2rem 0 0.8rem;
            color: #d7c8ff;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }

        .wolf-login-side-copy {
            margin: 0 0 1rem;
            color: var(--wolf-muted);
            line-height: 1.7;
        }

        .wolf-login-cta-wrap {
            margin-top: 1rem;
            max-width: 26rem;
        }

        .wolf-footer {
            padding: 1rem 0 1.5rem;
            text-align: center;
            color: var(--wolf-muted);
            font-size: 0.88rem;
        }

        .wolf-preview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 0.95rem;
            margin-top: 1rem;
        }

        .wolf-preview-card {
            border-radius: 24px;
            border: 1px solid var(--wolf-border);
            padding: 1.05rem;
            background: linear-gradient(180deg, rgba(159, 122, 234, 0.08), rgba(255, 255, 255, 0.02));
            box-shadow: 0 18px 42px rgba(6, 9, 19, 0.28);
            min-height: 156px;
            animation: wolfFadeUp 0.5s ease both;
        }

        .wolf-preview-lock {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 14px;
            background: rgba(159, 122, 234, 0.16);
            color: #f3d1eb;
            font-size: 1rem;
            margin-bottom: 0.75rem;
        }

        .wolf-preview-title {
            color: var(--wolf-text);
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .wolf-dashboard-shell {
            margin: 0.4rem 0 1.25rem;
        }

        .wolf-dashboard-frame {
            padding: 1rem;
            border-radius: 32px;
            border: 1px solid rgba(159, 122, 234, 0.18);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(8, 12, 22, 0.98)),
                radial-gradient(circle at top center, rgba(159, 122, 234, 0.12), transparent 34%);
            box-shadow:
                inset 1px 1px 0 rgba(255, 255, 255, 0.03),
                inset -14px -14px 34px rgba(3, 6, 14, 0.55),
                0 28px 70px rgba(3, 6, 15, 0.46);
            margin-bottom: 1.25rem;
        }

        .wolf-dashboard-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            padding: 0.95rem 1.15rem;
            border-radius: 24px;
            background: #101621;
            border: 1px solid rgba(255, 255, 255, 0.04);
            margin-bottom: 1rem;
        }

        .wolf-dashboard-topbar-title {
            color: var(--wolf-text);
            font-size: 1.05rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
        }

        .wolf-dashboard-topbar-meta {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: var(--wolf-muted);
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .wolf-dashboard-topbar-badge {
            padding: 0.36rem 0.58rem;
            border-radius: 12px;
            border: 1px solid rgba(96, 165, 250, 0.28);
            color: #b7d4ff;
            background: rgba(96, 165, 250, 0.08);
            font-weight: 700;
        }

        .wolf-dashboard-hero,
        .wolf-dashboard-side,
        .wolf-dashboard-profile,
        .wolf-dashboard-chart,
        .wolf-dashboard-kpi {
            border-radius: 28px;
            border: 1px solid rgba(159, 122, 234, 0.22);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(13, 18, 30, 0.97)),
                linear-gradient(135deg, rgba(159, 122, 234, 0.16), rgba(244, 114, 182, 0.06));
            box-shadow:
                inset 1px 1px 0 rgba(255, 255, 255, 0.04),
                inset -10px -10px 30px rgba(4, 7, 14, 0.55),
                0 24px 60px rgba(2, 5, 12, 0.45);
        }

        .wolf-dashboard-side {
            padding: 1rem;
            min-height: 100%;
        }

        .wolf-dashboard-sidebar-profile {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding-bottom: 1rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .wolf-dashboard-sidebar-avatar,
        .wolf-dashboard-sidebar-avatar-img {
            width: 52px;
            height: 52px;
            border-radius: 999px;
            flex-shrink: 0;
        }

        .wolf-dashboard-sidebar-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(159, 122, 234, 0.26), rgba(244, 114, 182, 0.22));
            color: var(--wolf-text);
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 0.95rem;
            font-weight: 800;
        }

        .wolf-dashboard-sidebar-avatar-img {
            object-fit: cover;
            border: 1px solid rgba(255, 255, 255, 0.10);
        }

        .wolf-dashboard-sidebar-name {
            color: var(--wolf-text);
            font-size: 0.92rem;
            font-weight: 800;
        }

        .wolf-dashboard-sidebar-role {
            color: var(--wolf-muted);
            font-size: 0.8rem;
            margin-top: 0.2rem;
        }

        .wolf-dashboard-profile {
            padding: 1rem;
            min-height: 100%;
        }

        .wolf-dashboard-side .wolf-inline-title {
            margin-bottom: 0.8rem;
        }

        .wolf-dashboard-nav {
            display: grid;
            gap: 0.65rem;
            margin-top: 0.9rem;
        }

        .wolf-dashboard-nav-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.9rem 0.95rem;
            border-radius: 18px;
            border: 1px solid rgba(159, 122, 234, 0.14);
            background: rgba(255, 255, 255, 0.02);
            color: var(--wolf-text);
            font-weight: 600;
        }

        .wolf-dashboard-nav-item.is-active {
            background: rgba(255, 255, 255, 0.07);
            border-color: rgba(255, 255, 255, 0.08);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
        }

        .wolf-dashboard-nav-item.is-utility {
            color: var(--wolf-muted);
            background: transparent;
        }

        .wolf-dashboard-nav-group {
            display: grid;
            gap: 0.65rem;
        }

        .wolf-dashboard-nav-divider {
            height: 1px;
            margin: 0.95rem 0;
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.08), transparent);
        }

        .wolf-dashboard-nav-dot {
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: linear-gradient(135deg, #9f7aea, #f472b6);
            box-shadow: 0 0 18px rgba(244, 114, 182, 0.42);
            flex-shrink: 0;
        }

        .wolf-dashboard-side-promo {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(159, 122, 234, 0.14);
        }

        .wolf-dashboard-side-promo-title {
            color: var(--wolf-text);
            font-size: 0.95rem;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }

        .wolf-dashboard-side-promo-copy {
            color: var(--wolf-muted);
            font-size: 0.9rem;
            line-height: 1.65;
            margin: 0;
        }

        .wolf-dashboard-hero {
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
            margin-bottom: 1rem;
        }

        .wolf-dashboard-hero::after {
            content: "";
            position: absolute;
            inset: auto -10% -35% auto;
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(244, 114, 182, 0.28), transparent 62%);
            opacity: 0.9;
        }

        .wolf-dashboard-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin-bottom: 0.9rem;
        }

        .wolf-dashboard-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.5rem 0.82rem;
            border-radius: 999px;
            border: 1px solid rgba(159, 122, 234, 0.18);
            background: rgba(255, 255, 255, 0.04);
            color: #ddd5ff;
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .wolf-dashboard-hero-title {
            position: relative;
            z-index: 1;
            margin: 0 0 0.45rem;
            font-size: clamp(1.7rem, 4vw, 2.5rem);
            line-height: 1.05;
            color: var(--wolf-text);
            font-weight: 800;
        }

        .wolf-dashboard-hero-body {
            position: relative;
            z-index: 1;
            margin: 0;
            max-width: 54ch;
            color: var(--wolf-muted);
            line-height: 1.75;
        }

        .wolf-dashboard-searchbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.9rem 1rem;
            border-radius: 22px;
            background: #151c29;
            border: 1px solid rgba(255, 255, 255, 0.04);
            margin-bottom: 1rem;
        }

        .wolf-dashboard-searchbar-copy {
            color: var(--wolf-muted);
            font-size: 0.92rem;
        }

        .wolf-dashboard-search-actions {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
        }

        .wolf-dashboard-search-action {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(159, 122, 234, 0.14);
            border: 1px solid rgba(159, 122, 234, 0.16);
            color: #f3d1eb;
            font-size: 1rem;
        }

        .wolf-dashboard-kpi-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 0 0 1rem;
        }

        .wolf-dashboard-kpi {
            padding: 1rem;
            min-height: 154px;
        }

        .wolf-dashboard-kpi.is-purple {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(12, 17, 30, 0.97)),
                linear-gradient(135deg, rgba(135, 92, 255, 0.36), rgba(135, 92, 255, 0.06));
        }

        .wolf-dashboard-kpi.is-pink {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(12, 17, 30, 0.97)),
                linear-gradient(135deg, rgba(244, 114, 182, 0.28), rgba(159, 122, 234, 0.06));
        }

        .wolf-dashboard-kpi.is-blue {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(12, 17, 30, 0.97)),
                linear-gradient(135deg, rgba(96, 165, 250, 0.22), rgba(159, 122, 234, 0.04));
        }

        .wolf-dashboard-kpi-label {
            color: #c9d2e4;
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .wolf-dashboard-kpi-value {
            color: var(--wolf-text);
            font-size: clamp(1.55rem, 4vw, 2.25rem);
            font-weight: 800;
            line-height: 1.05;
        }

        .wolf-dashboard-kpi-note {
            margin-top: 0.8rem;
            color: #d8c9ff;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .wolf-dashboard-kpi-inline {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem;
        }

        .wolf-dashboard-ring {
            --progress: 78%;
            width: 62px;
            height: 62px;
            border-radius: 999px;
            position: relative;
            background: conic-gradient(#f472b6 0 var(--progress), rgba(255, 255, 255, 0.08) var(--progress) 100%);
            flex-shrink: 0;
        }

        .wolf-dashboard-ring::before {
            content: "";
            position: absolute;
            inset: 8px;
            border-radius: 999px;
            background: #121827;
            box-shadow: inset 0 0 14px rgba(0, 0, 0, 0.35);
        }

        .wolf-dashboard-ring span {
            position: absolute;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--wolf-text);
            font-size: 0.8rem;
            font-weight: 800;
            z-index: 1;
        }

        .wolf-dashboard-chart {
            padding: 1.15rem;
            margin-bottom: 1rem;
        }

        .wolf-dashboard-chart-header {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 1rem;
        }

        .wolf-dashboard-chart-title {
            margin: 0 0 0.35rem;
            color: var(--wolf-text);
            font-size: 1.05rem;
            font-weight: 800;
        }

        .wolf-dashboard-chart-copy {
            margin: 0;
            color: var(--wolf-muted);
            max-width: 56ch;
            line-height: 1.7;
        }

        .wolf-dashboard-pills {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.3rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(159, 122, 234, 0.18);
        }

        .wolf-dashboard-pill {
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            color: var(--wolf-muted);
            font-size: 0.8rem;
            font-weight: 700;
        }

        .wolf-dashboard-pill.is-active {
            background: linear-gradient(135deg, rgba(159, 122, 234, 0.8), rgba(244, 114, 182, 0.7));
            color: #0b0f19;
        }

        .wolf-dashboard-visual {
            position: relative;
            height: 220px;
            border-radius: 24px;
            background:
                radial-gradient(circle at 50% 68%, rgba(159, 122, 234, 0.18), transparent 34%),
                linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(5, 8, 15, 0.28));
            overflow: hidden;
        }

        .wolf-dashboard-visual::before {
            content: "";
            position: absolute;
            inset: 18px 18px 18px 18px;
            background:
                linear-gradient(transparent 24%, rgba(255, 255, 255, 0.05) 25%, transparent 26%),
                linear-gradient(90deg, transparent 24%, rgba(255, 255, 255, 0.05) 25%, transparent 26%);
            background-size: 100% 52px, 84px 100%;
            opacity: 0.5;
        }

        .wolf-dashboard-line {
            position: absolute;
            inset: auto 8% 22% 8%;
            height: 58%;
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(159, 122, 234, 0.16), rgba(159, 122, 234, 0.02));
            clip-path: polygon(0% 72%, 10% 82%, 22% 42%, 34% 58%, 45% 32%, 58% 48%, 71% 26%, 83% 38%, 100% 12%, 100% 100%, 0% 100%);
            border: 1px solid rgba(159, 122, 234, 0.16);
        }

        .wolf-dashboard-line::after {
            content: "";
            position: absolute;
            inset: 0;
            clip-path: polygon(0% 72%, 10% 82%, 22% 42%, 34% 58%, 45% 32%, 58% 48%, 71% 26%, 83% 38%, 100% 12%);
            border-top: 3px solid #a855f7;
            filter: drop-shadow(0 0 18px rgba(168, 85, 247, 0.65));
        }

        .wolf-dashboard-bottom-row {
            display: grid;
            grid-template-columns: 1.35fr 1fr;
            gap: 1rem;
            margin-bottom: 0.3rem;
        }

        .wolf-dashboard-mini-panel {
            border-radius: 24px;
            border: 1px solid rgba(159, 122, 234, 0.2);
            padding: 1rem;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(12, 17, 30, 0.96)),
                linear-gradient(135deg, rgba(159, 122, 234, 0.14), rgba(244, 114, 182, 0.04));
            box-shadow:
                inset 1px 1px 0 rgba(255, 255, 255, 0.04),
                inset -10px -10px 30px rgba(4, 7, 14, 0.55);
        }

        .wolf-dashboard-profile-top {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .wolf-dashboard-profile-avatar,
        .wolf-dashboard-profile-avatar-img {
            width: 78px;
            height: 78px;
            border-radius: 999px;
            margin-bottom: 0.8rem;
        }

        .wolf-dashboard-profile-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(159, 122, 234, 0.26), rgba(244, 114, 182, 0.22));
            color: var(--wolf-text);
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 1.25rem;
            font-weight: 800;
        }

        .wolf-dashboard-profile-avatar-img {
            object-fit: cover;
            border: 1px solid rgba(255, 255, 255, 0.10);
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.3);
        }

        .wolf-dashboard-profile-name {
            color: var(--wolf-text);
            font-size: 1rem;
            font-weight: 800;
        }

        .wolf-dashboard-profile-role {
            color: var(--wolf-muted);
            font-size: 0.84rem;
            margin-top: 0.25rem;
        }

        .wolf-dashboard-profile-actions {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.7rem;
            margin: 1rem 0;
        }

        .wolf-dashboard-profile-action {
            min-height: 46px;
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(159, 122, 234, 0.14);
            border: 1px solid rgba(159, 122, 234, 0.16);
            color: #f3d1eb;
            font-size: 1rem;
        }

        .wolf-dashboard-profile-section {
            margin-top: 0.95rem;
            padding-top: 0.95rem;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        .wolf-dashboard-profile-label {
            color: #ddd5ff;
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .wolf-dashboard-profile-copy {
            color: var(--wolf-muted);
            line-height: 1.65;
            font-size: 0.9rem;
            margin: 0;
        }

        .wolf-dashboard-billing {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(159, 122, 234, 0.14);
        }

        .wolf-dashboard-billing-title {
            color: var(--wolf-muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }

        .wolf-dashboard-billing-value {
            color: var(--wolf-text);
            font-size: 1.65rem;
            font-weight: 800;
        }

        .wolf-dashboard-billing-note {
            color: #d8c9ff;
            font-size: 0.88rem;
            margin-top: 0.45rem;
        }

        .wolf-mini-list {
            margin: 0.2rem 0 0;
            padding-left: 1rem;
            color: var(--wolf-text);
            line-height: 1.8;
        }

        .wolf-mini-list li + li {
            margin-top: 0.35rem;
        }

        .wolf-guide-card {
            min-height: 176px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        [data-testid="stAlert"] {
            border-radius: 20px;
            border: 1px solid rgba(159, 122, 234, 0.20);
            background: rgba(14, 20, 34, 0.90);
            box-shadow: 0 16px 38px rgba(3, 6, 15, 0.22);
        }

        [data-testid="stAlert"] p {
            color: var(--wolf-text);
        }

        [data-testid="stExpander"] {
            border-radius: 22px;
            border: 1px solid var(--wolf-border);
            background: rgba(15, 21, 36, 0.84);
            overflow: hidden;
        }

        [data-testid="stExpander"] details summary {
            padding: 0.25rem 0.3rem;
        }

        [data-testid="stDataFrame"] {
            border-radius: 22px;
            border: 1px solid var(--wolf-border);
            overflow: hidden;
            box-shadow: 0 16px 38px rgba(3, 6, 15, 0.22);
        }

        [data-testid="stMetric"] {
            border-radius: 24px;
            border: 1px solid var(--wolf-border);
            background: rgba(15, 21, 36, 0.88);
            padding: 0.85rem 1rem;
        }

        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: var(--wolf-muted) !important;
        }

        @keyframes wolfFadeUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 900px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 0.75rem;
            }

            .wolf-hero,
            .wolf-card,
            .wolf-userbox,
            .wolf-metric,
            .wolf-email-banner,
            [data-testid="stForm"] {
                border-radius: 22px;
            }

            .wolf-title {
                max-width: none;
                font-size: clamp(2rem, 9vw, 2.8rem);
            }

            .wolf-logo-wordmark {
                width: min(100%, 132px);
            }

            .wolf-logo-wordmark-sm {
                width: min(100%, 58px);
            }

            .wolf-brand-title-lg {
                font-size: clamp(1.7rem, 7vw, 2.4rem);
                letter-spacing: 0.14em;
            }

            .wolf-brand-tagline {
                letter-spacing: 0.26em;
                font-size: 0.7rem;
            }

            .wolf-preview-grid {
                grid-template-columns: 1fr;
            }

            .wolf-dashboard-kpi-grid,
            .wolf-dashboard-bottom-row {
                grid-template-columns: 1fr;
            }

            .wolf-dashboard-chart-header {
                flex-direction: column;
            }

            .wolf-dashboard-topbar,
            .wolf-dashboard-searchbar {
                flex-direction: column;
                align-items: flex-start;
            }

            .wolf-dashboard-search-actions,
            .wolf-dashboard-topbar-meta {
                width: 100%;
            }

            .wolf-user-meta {
                align-items: flex-start;
            }

            .stButton > button,
            .stFormSubmitButton > button,
            .stDownloadButton > button,
            .stLinkButton > a {
                min-height: 3.1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_wordmark(compact: bool = False) -> None:
    logo_html = get_brand_symbol_html("compact" if compact else "hero")
    title_class = "wolf-brand-title-sm" if compact else "wolf-brand-title-lg"
    tagline_class = "wolf-brand-tagline wolf-brand-tagline-sm" if compact else "wolf-brand-tagline"
    lockup_class = "wolf-logo-lockup wolf-logo-lockup-compact" if compact else "wolf-logo-lockup"
    st.markdown(
        f"""
        <div class="{lockup_class}">
            {logo_html}
            <div class="wolf-brand-stack wolf-brand-stack-center">
                <div class="{title_class}">{html.escape(t("brand"))}</div>
                <div class="{tagline_class}">CREATE. GROW. EARN.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_brand_symbol_html(size: str = "default") -> str:
    symbol_uri = get_brand_symbol_uri()
    size_class = {
        "hero": "",
        "compact": " wolf-logo-wordmark-sm",
        "default": "",
    }.get(size, "")
    if not symbol_uri:
        return '<div class="wolf-logo-symbol-badge"><div class="wolf-avatar">GP</div></div>'
    return (
        '<div class="wolf-logo-symbol-badge">'
        f'<img class="wolf-logo-wordmark{size_class} wolf-logo-symbol" src="{symbol_uri}" alt="{html.escape(t("brand"))}" />'
        "</div>"
    )


def render_header() -> None:
    left, right = st.columns([2.1, 1.0], gap="large")
    with left:
        brand_block = (
            f"""
            <div class="wolf-logo-lockup wolf-logo-lockup-compact">
                {get_brand_symbol_html("compact")}
                <div class="wolf-brand-stack">
                    <div class="wolf-brand-title-sm">{html.escape(t("brand"))}</div>
                </div>
            </div>
            """
        )
        st.markdown(
            f"""
            <section class="wolf-hero">
                {brand_block}
                <h1 class="wolf-title">{html.escape(t("hero_title"))}</h1>
                <p class="wolf-subtitle">{html.escape(t("hero_subtitle"))}</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<div class="wolf-panel-label">{html.escape(t("language"))}</div>',
            unsafe_allow_html=True,
        )
        render_language_selector("header_language_selector")
        if is_logged_in():
            render_user_menu()


def render_user_menu() -> None:
    name = get_user_claim("name", "Creator")
    email = get_current_user_email() or "unknown@example.com"
    picture = get_user_claim("picture", "")
    initials = "".join(part[:1] for part in name.split()[:2]).upper() or "GP"

    avatar_html = (
        f'<img class="wolf-avatar-img" src="{html.escape(picture, quote=True)}" alt="{html.escape(name)}" />'
        if picture
        else f'<div class="wolf-avatar">{html.escape(initials)}</div>'
    )
    st.markdown(
        f"""
        <div class="wolf-userbox">
            <div class="wolf-panel-label">{html.escape(t("logged_in_as"))}</div>
            <div class="wolf-user-meta">
                {avatar_html}
                <div>
                    <div class="wolf-user-name">{html.escape(name)}</div>
                    <div class="wolf-user-email">{html.escape(email)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button(t("logout"), use_container_width=True, on_click=st.logout)


# To enable Google login:
# 1. Go to Google Cloud Console
# 2. Create OAuth client
# 3. Add redirect URI:
#    http://localhost:8501/oauth2callback
# 4. Paste client_id and client_secret into secrets.toml
def render_google_login_screen() -> None:
    preview_items = [
        (t("vip_feature_strategy"), t("preview_benefit_strategy")),
        (t("vip_feature_plan"), t("preview_benefit_plan")),
        (t("vip_feature_pricing"), t("preview_benefit_pricing")),
    ]
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown(
            f"""
            <section class="wolf-hero wolf-login-hero">
                <div class="wolf-logo-lockup">
                    {get_brand_symbol_html("hero")}
                    <div class="wolf-brand-stack">
                        <div class="wolf-brand-title-lg">{html.escape(t("brand"))}</div>
                        <div class="wolf-brand-tagline">CREATE. GROW. EARN.</div>
                    </div>
                </div>
                <div class="wolf-login-copy">
                    <h1 class="wolf-title">{html.escape(t("hero_title"))}</h1>
                    <p class="wolf-subtitle">{html.escape(t("hero_subtitle"))}</p>
                    <p class="wolf-muted">{html.escape(t("login_gate_desc"))}</p>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="wolf-login-cta-wrap">', unsafe_allow_html=True)
        st.button(
            t("continue_google"),
            on_click=lambda: st.login("google"),
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown(
            f"""
            <div class="wolf-login-grid">
                <div class="wolf-login-side-label">{html.escape(t("login_preview_label"))}</div>
                <p class="wolf-login-side-copy">
                    {html.escape(t("login_preview_body"))}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for title, body in preview_items:
            render_note_card(title, body)


def render_logged_in_status() -> None:
    return


def render_metric_card(title: str, value: str, note: str = "") -> None:
    note_html = (
        f'<div class="wolf-metric-note">{html.escape(note)}</div>' if note else ""
    )
    st.markdown(
        f"""
        <div class="wolf-metric">
            <div class="wolf-metric-label">{html.escape(title)}</div>
            <div class="wolf-metric-value">{html.escape(value)}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_note_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="wolf-card">
            <div class="wolf-inline-title">{html.escape(title)}</div>
            <p class="wolf-muted">{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_guide_library_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="wolf-card wolf-guide-card">
            <div class="wolf-inline-title">{html.escape(title)}</div>
            <p class="wolf-muted">{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_list_card(title: str, lines: list[str]) -> None:
    items = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
    st.markdown(
        f"""
        <div class="wolf-card">
            <div class="wolf-inline-title">{html.escape(title)}</div>
            <ul class="wolf-list">{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_personalized_cta_text(net_income: float) -> str:
    if is_from_email() or is_upgrade_flow():
        return t("cta_email_return")
    if net_income < 1000:
        return t("cta_first_growth")
    if net_income <= 5000:
        return t("cta_optimize_revenue")
    return t("cta_scale_business")


def get_potential_stage_message(net_income: float) -> str:
    if net_income < 1000:
        return t("potential_stage_early")
    if net_income <= 5000:
        return t("potential_stage_mid")
    return t("potential_stage_high")


def get_arppu_insight(arppu: float) -> str:
    if arppu < 5:
        return t("arppu_low")
    if arppu <= 15:
        return t("arppu_mid")
    return t("arppu_high")


def build_money_engine_result(
    follower_count: int,
    monthly_sub_price: float,
    expected_tips_ppv: float,
    target_income: float,
) -> dict[str, float | int | str]:
    financials = calculate_financials(
        follower_count,
        monthly_sub_price,
        expected_tips_ppv,
    )
    arppu = financials["gross_income"] / follower_count if follower_count > 0 else 0.0
    gap = financials["net_income"] * 0.50
    extra_per_fan = expected_tips_ppv / follower_count if follower_count > 0 else 0.0
    per_fan_model = monthly_sub_price * 0.8 + extra_per_fan
    required_subscribers = (
        math.ceil(target_income / per_fan_model)
        if target_income > 0 and per_fan_model > 0
        else 0
    )
    return {
        **financials,
        "follower_count": follower_count,
        "monthly_sub_price": monthly_sub_price,
        "expected_tips_ppv": expected_tips_ppv,
        "target_income": target_income,
        "arppu": arppu,
        "arppu_insight": get_arppu_insight(arppu),
        "money_gap": gap,
        "required_subscribers": required_subscribers,
        "stage_message": get_potential_stage_message(financials["net_income"]),
        "show_target_warning": int(
            follower_count > 0 and required_subscribers > follower_count * 2
        ),
    }


def render_vip_preview_cards() -> None:
    preview_items = [
        (t("vip_feature_strategy"), t("preview_benefit_strategy")),
        (t("vip_feature_plan"), t("preview_benefit_plan")),
        (t("vip_feature_bible"), t("preview_benefit_bible")),
        (t("vip_feature_pricing"), t("preview_benefit_pricing")),
        (t("vip_feature_updates"), t("preview_benefit_updates")),
    ]
    cards_html = "".join(
        f"""
        <div class="wolf-preview-card">
            <div class="wolf-preview-lock">&#128274;</div>
            <div class="wolf-preview-title">{html.escape(title)}</div>
            <div class="wolf-muted">{html.escape(body)}</div>
        </div>
        """
        for title, body in preview_items
    )
    st.markdown(
        f'<div class="wolf-preview-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def render_social_proof_section() -> None:
    proof_items = [
        t("social_proof_card_1"),
        t("social_proof_card_2"),
        t("social_proof_card_3"),
        t("social_proof_card_4"),
    ]
    cards_html = "".join(
        f"""
        <div class="wolf-preview-card">
            <div class="wolf-preview-lock">&#10022;</div>
            <div class="wolf-preview-title">{html.escape(item)}</div>
        </div>
        """
        for item in proof_items
    )
    st.markdown(f"### {t('social_proof_title')}")
    st.markdown(
        f'<div class="wolf-preview-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def render_email_return_banner(logged_in: bool, paid: bool, email: str) -> None:
    if not (is_from_email() or is_upgrade_flow()):
        return

    banner_title = t("upgrade_flow_title") if is_upgrade_flow() else t("email_welcome_title")
    st.markdown(
        f"""
        <section class="wolf-email-banner">
            <div class="wolf-brand">{html.escape(t("brand"))}</div>
            <h2 class="wolf-title" style="font-size:clamp(1.6rem, 5vw, 2.5rem); margin-top:0.85rem;">{html.escape(banner_title)}</h2>
            <p class="wolf-subtitle" style="margin:0;">{html.escape(t("email_ready_line"))}</p>
            <p class="wolf-email-highlight">{html.escape(t("email_money_line"))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not logged_in:
        st.caption(t("upgrade_login_prompt") if is_upgrade_flow() else t("email_login_prompt"))
        login_disabled = not (auth_is_supported() and auth_is_configured())
        if st.button(
            t("continue_google"),
            use_container_width=True,
            key="email_banner_login",
            type="primary",
            disabled=login_disabled,
        ):
            st.session_state["clicked_cta"] = True
            st.login("google")
        if not auth_is_supported():
            st.warning("This Streamlit build does not expose st.login / st.user / st.logout.")
        elif not auth_is_configured():
            st.warning(t("google_setup_missing"))
            st.info(t("google_setup_hint"))
        return

    if paid:
        st.caption(t("upgrade_paid_prompt") if is_upgrade_flow() else t("email_paid_prompt"))
        st.markdown(
            f'<a class="wolf-banner-link" href="#vip-section">{html.escape(t("cta_email_return"))}</a>',
            unsafe_allow_html=True,
        )
        return

    st.caption(t("upgrade_paywall_prompt") if is_upgrade_flow() else t("email_paywall_prompt"))
    render_checkout_button(
        build_checkout_url(email),
        t("start_vip_membership") if is_upgrade_flow() else t("unlock_vip_strategy"),
        button_key="email_banner_unlock_disabled",
        show_supporting_text=False,
    )


def render_checkout_button(
    checkout_url: str,
    label: str,
    *,
    button_key: str,
    show_supporting_text: bool = False,
) -> None:
    if card_checkout_enabled() and checkout_url:
        st.link_button(label, checkout_url, use_container_width=True)
    else:
        st.button(label, disabled=True, use_container_width=True, key=button_key)
        st.caption(t("card_disabled_notice"))
    if show_supporting_text:
        st.caption(t("risk_reversal"))
        st.caption(t("trust_checkout_line1"))
        st.caption(t("trust_checkout_line2"))


def render_paywall_faq() -> None:
    st.markdown(f"### {t('faq_title')}")
    faq_items = [
        ("faq_q1", "faq_a1"),
        ("faq_q2", "faq_a2"),
        ("faq_q3", "faq_a3"),
        ("faq_q4", "faq_a4"),
        ("faq_q5", "faq_a5"),
    ]
    for question_key, answer_key in faq_items:
        with st.expander(t(question_key)):
            st.write(t(answer_key))


def calculate_financials(
    follower_count: int, monthly_sub_price: float, expected_tips_ppv: float
) -> dict[str, float]:
    gross_income = follower_count * monthly_sub_price + expected_tips_ppv
    platform_fee = gross_income * PLATFORM_FEE_RATE
    net_income = gross_income - platform_fee
    return {
        "gross_income": gross_income,
        "platform_fee": platform_fee,
        "net_income": net_income,
        "yearly_net_income": net_income * 12,
        "subscription_revenue": follower_count * monthly_sub_price,
    }


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def subscription_record_is_valid(record: dict) -> bool:
    attributes = record.get("attributes", {})
    status = str(attributes.get("status", "")).strip().lower()
    if status in ACTIVE_SUBSCRIPTION_STATES:
        return True
    if status == "cancelled":
        ends_at = parse_iso_datetime(str(attributes.get("ends_at", "")))
        if ends_at and ends_at > datetime.now(timezone.utc):
            return True
    return False


def _fetch_lemonsqueezy_subscriptions(email: str) -> list[dict]:
    api_key = str(secret_get("lemonsqueezy", "api_key", default="") or "").strip()
    if not api_key or not email:
        return []

    base_params = {"filter[user_email]": email, "page[size]": 20}
    store_id = str(secret_get("lemonsqueezy", "store_id", default="") or "").strip()
    variant_id = str(secret_get("lemonsqueezy", "variant_id", default="") or "").strip()

    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {api_key}",
    }

    def request_with_params(params: dict[str, str]) -> list[dict]:
        try:
            response = requests.get(
                "https://api.lemonsqueezy.com/v1/subscriptions",
                params=params,
                headers=headers,
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return []
        return payload.get("data", []) or []

    filtered_params = dict(base_params)
    if store_id:
        filtered_params["filter[store_id]"] = store_id
    if variant_id:
        filtered_params["filter[variant_id]"] = variant_id

    records = request_with_params(filtered_params)
    if records:
        return records

    if filtered_params != base_params:
        return request_with_params(base_params)
    return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_lemonsqueezy_subscriptions(email: str) -> list[dict]:
    return _fetch_lemonsqueezy_subscriptions(email)


def check_lemonsqueezy_status(email: str, *, force_refresh: bool = False) -> bool:
    if not email:
        return False

    try:
        if force_refresh:
            fetch_lemonsqueezy_subscriptions.clear()
            records = _fetch_lemonsqueezy_subscriptions(email)
        else:
            records = fetch_lemonsqueezy_subscriptions(email)
    except Exception:
        return False

    is_active = any(subscription_record_is_valid(record) for record in records)
    if is_active:
        add_paid_user(email)
    return is_active


def check_subscription_status(email: str, *, force_refresh: bool = False) -> bool:
    if not email:
        return False

    if email.lower() in set(load_paid_users()):
        return True

    if check_lemonsqueezy_status(email, force_refresh=force_refresh):
        return True

    if not crypto_checkout_enabled():
        return False

    return sync_paid_user_from_remote(email)


def build_checkout_url(email: str) -> str:
    checkout_url = str(
        secret_get(
            "lemonsqueezy",
            "checkout_url",
            default=DEFAULT_LEMONSQUEEZY_CHECKOUT_URL,
        )
        or DEFAULT_LEMONSQUEEZY_CHECKOUT_URL
    ).strip()
    if not checkout_url:
        return ""

    split_url = urlsplit(checkout_url)
    params = dict(parse_qsl(split_url.query, keep_blank_values=True))
    if email:
        params["checkout[email]"] = email
        params["checkout[custom][google_email]"] = email
        params["checkout[custom][portal]"] = "girlpire-vip"
    query = urlencode(params, doseq=True)
    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            query,
            split_url.fragment,
        )
    )


def get_nowpayments_api_key() -> str:
    candidate_values = (
        secret_get("NOWPAYMENTS_API_KEY", default=""),
        secret_get("nowpayments", "api_key", default=""),
        os.environ.get("NOWPAYMENTS_API_KEY", ""),
    )
    for value in candidate_values:
        normalized = str(value or "").strip()
        if normalized:
            return normalized
    return ""


def crypto_checkout_enabled() -> bool:
    candidate_values = (
        secret_get("app", "enable_crypto", default=""),
        secret_get("ENABLE_CRYPTO_CHECKOUT", default=""),
        os.environ.get("ENABLE_CRYPTO_CHECKOUT", ""),
        "false",
    )
    truthy_values = {"1", "true", "yes", "on"}
    for value in candidate_values:
        normalized = str(value or "").strip().lower()
        if normalized:
            return normalized in truthy_values
    return False


def card_checkout_enabled() -> bool:
    candidate_values = (
        secret_get("app", "enable_card_checkout", default=""),
        secret_get("ENABLE_CARD_CHECKOUT", default=""),
        os.environ.get("ENABLE_CARD_CHECKOUT", ""),
        "false",
    )
    truthy_values = {"1", "true", "yes", "on"}
    for value in candidate_values:
        normalized = str(value or "").strip().lower()
        if normalized:
            return normalized in truthy_values
    return False


def get_nowpayments_preferred_pay_currency() -> str:
    candidate_values = (
        secret_get("nowpayments", "preferred_pay_currency", default=""),
        secret_get("NOWPAYMENTS_PREFERRED_PAY_CURRENCY", default=""),
        os.environ.get("NOWPAYMENTS_PREFERRED_PAY_CURRENCY", ""),
        "usdttrc20",
    )
    for value in candidate_values:
        normalized = str(value or "").strip().lower()
        if normalized:
            return normalized
    return "usdttrc20"


def get_vip_price_usd() -> float:
    candidate_values = (
        secret_get("pricing", "vip_price_usd", default=""),
        secret_get("VIP_PRICE_USD", default=""),
        os.environ.get("VIP_PRICE_USD", ""),
        19.99,
    )
    for value in candidate_values:
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return round(parsed, 2)
    return 19.99


def get_vip_price_label() -> str:
    price_value = get_vip_price_usd()
    if get_language() == "tr":
        return f"${price_value:,.2f}/ay"
    return f"${price_value:,.2f}/month"


def get_webhook_base_url() -> str:
    return str(
        secret_get(
            "app",
            "webhook_base_url",
            default=os.environ.get("WEBHOOK_BASE_URL", "https://girlpire-webhook.onrender.com"),
        )
        or "https://girlpire-webhook.onrender.com"
    ).strip().rstrip("/")


def get_webhook_sync_secret() -> str:
    return str(
        secret_get(
            "app",
            "webhook_sync_secret",
            default=os.environ.get("WEBHOOK_SYNC_SECRET", ""),
        )
        or ""
    ).strip()


def fetch_remote_vip_status(email: str) -> bool | None:
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        return False

    webhook_base_url = get_webhook_base_url()
    if not webhook_base_url:
        return None

    headers = {}
    sync_secret = get_webhook_sync_secret()
    if sync_secret:
        headers["x-webhook-sync-secret"] = sync_secret

    try:
        response = requests.get(
            f"{webhook_base_url}/vip-status",
            params={"email": normalized_email},
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    return bool(data.get("paid"))


def sync_paid_user_from_remote(email: str) -> bool:
    remote_status = fetch_remote_vip_status(email)
    if remote_status:
        add_paid_user(email)
        return True
    return False


def create_crypto_payment(email: str) -> str:
    api_key = get_nowpayments_api_key()
    if not api_key or not email:
        return ""

    url = "https://api.nowpayments.io/v1/invoice"
    headers = {"x-api-key": api_key}
    base_payload = {
        "price_amount": get_vip_price_usd(),
        "price_currency": "usd",
        "order_id": email,
        "order_description": "Girlpire VIP",
        "success_url": get_app_url() or "https://girlpire.streamlit.app",
    }

    def send_invoice(payload: dict[str, object]) -> str:
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            return ""
        return str(data.get("invoice_url") or "")

    preferred_currency = get_nowpayments_preferred_pay_currency()
    preferred_payload = dict(base_payload)
    if preferred_currency:
        preferred_payload["pay_currency"] = preferred_currency

    preferred_invoice_url = send_invoice(preferred_payload)
    if preferred_invoice_url:
        return preferred_invoice_url

    return send_invoice(base_payload)


def build_current_vip_profile(
    financials: dict[str, float | int | str],
) -> dict[str, float | int | str]:
    default_target = max(
        float(st.session_state.get("target_income_goal", 5000.0)),
        float(financials.get("net_income", 0.0)) * 1.5,
        5000.0,
    )
    return {
        "follower_count": int(st.session_state.get("follower_count", 0)),
        "monthly_sub_price": float(st.session_state.get("monthly_sub_price", 0.0)),
        "expected_tips_ppv": float(st.session_state.get("expected_tips_ppv", 0.0)),
        "daily_time": float(st.session_state.get("vip_daily_time", 2.0)),
        "target_income": float(st.session_state.get("vip_target_income", default_target)),
        "experience_level_code": str(
            st.session_state.get("vip_experience_level", "intermediate")
        ).lower(),
        "main_challenge": str(
            st.session_state.get("vip_main_challenge", "conversion")
        ).lower(),
    }


def get_growth_focus_copy(focus_key: str) -> tuple[str, str]:
    body_map = {
        "traffic": t("growth_focus_traffic"),
        "conversion": t("growth_focus_conversion"),
        "retention": t("growth_focus_retention"),
    }
    return t(focus_key), body_map.get(focus_key, t("growth_focus_conversion"))


def compute_strategy_score(
    financials: dict[str, float | int | str],
    profile: dict[str, float | int | str],
) -> dict[str, float | int | str]:
    follower_count = int(profile["follower_count"])
    gross_income = float(financials["gross_income"])
    net_income = float(financials["net_income"])
    subscription_revenue = float(financials["subscription_revenue"])
    expected_tips_ppv = float(profile["expected_tips_ppv"])
    target_income = float(profile["target_income"])

    arppu = gross_income / follower_count if follower_count > 0 else 0.0
    profit_margin = net_income / gross_income if gross_income > 0 else 0.0
    extra_ratio = expected_tips_ppv / subscription_revenue if subscription_revenue > 0 else 0.0

    if arppu < 5:
        arppu_points = 10
    elif arppu <= 15:
        arppu_points = 20
    else:
        arppu_points = 28

    if profit_margin < 0.35:
        margin_points = 8
    elif profit_margin < 0.55:
        margin_points = 18
    else:
        margin_points = 26

    if follower_count >= 500 and extra_ratio >= 0.20:
        growth_points = 20
    elif follower_count >= 150 or extra_ratio >= 0.12:
        growth_points = 14
    else:
        growth_points = 8

    if net_income <= 0:
        target_points = 4
    elif target_income <= net_income * 1.2:
        target_points = 24
    elif target_income <= net_income * 1.7:
        target_points = 16
    elif target_income <= net_income * 2.5:
        target_points = 10
    else:
        target_points = 4

    score = int(max(0, min(100, arppu_points + margin_points + growth_points + target_points)))
    if score <= 40:
        status = t("status_weak")
        explanation = t("score_explanation_weak")
    elif score <= 70:
        status = t("status_average")
        explanation = t("score_explanation_average")
    elif score <= 85:
        status = t("status_good")
        explanation = t("score_explanation_good")
    else:
        status = t("status_strong")
        explanation = t("score_explanation_strong")

    return {
        "score": score,
        "status": status,
        "explanation": explanation,
        "arppu": arppu,
        "profit_margin": profit_margin,
        "growth_potential": extra_ratio,
        "target_difficulty": target_income / max(net_income, 1.0),
    }


def determine_biggest_bottleneck(
    financials: dict[str, float | int | str],
    profile: dict[str, float | int | str],
) -> str:
    score_details = compute_strategy_score(financials, profile)
    follower_count = int(profile["follower_count"])
    main_challenge = str(profile["main_challenge"])

    if float(score_details["arppu"]) < 5:
        return "bottleneck_fan_value"
    if float(score_details["profit_margin"]) < 0.45:
        return "bottleneck_margin"
    if follower_count < 150 or main_challenge == "traffic":
        return "bottleneck_traffic"
    if main_challenge in {"conversion", "pricing"} or float(score_details["arppu"]) < 10:
        return "bottleneck_conversion"
    if main_challenge == "retention":
        return "bottleneck_retention"
    return "bottleneck_system"


def determine_growth_focus(
    financials: dict[str, float | int | str],
    profile: dict[str, float | int | str],
) -> str:
    follower_count = int(profile["follower_count"])
    main_challenge = str(profile["main_challenge"])
    gross_income = float(financials["gross_income"])
    arppu = gross_income / follower_count if follower_count > 0 else 0.0

    if follower_count < 150 or main_challenge == "traffic":
        return "traffic"
    if arppu < 8 or main_challenge in {"conversion", "pricing"}:
        return "conversion"
    return "retention"


def build_immediate_fix_actions(
    financials: dict[str, float | int | str],
    profile: dict[str, float | int | str],
    growth_focus_key: str,
) -> list[str]:
    subscription_revenue = float(financials["subscription_revenue"])
    expected_tips_ppv = float(profile["expected_tips_ppv"])
    monthly_sub_price = float(profile["monthly_sub_price"])

    actions: list[str] = []
    if monthly_sub_price < 7:
        actions.append(t("fix_price_audit"))
    else:
        actions.append(t("fix_offer_refresh"))

    if expected_tips_ppv < subscription_revenue * 0.20:
        actions.append(t("fix_ppv_launch"))
    else:
        actions.append(t("fix_tip_goal"))

    if growth_focus_key == "traffic":
        actions.append(t("fix_tracking_review"))
    elif growth_focus_key == "conversion":
        actions.append(t("fix_conversion_path"))
    else:
        actions.append(t("fix_retention_check"))
    return actions[:3]


def build_revenue_optimization_actions(
    financials: dict[str, float | int | str],
    profile: dict[str, float | int | str],
) -> list[str]:
    subscription_revenue = float(financials["subscription_revenue"])
    expected_tips_ppv = float(profile["expected_tips_ppv"])
    monthly_sub_price = float(profile["monthly_sub_price"])

    pricing_action = t("revenue_price_low") if monthly_sub_price < 7 else t("revenue_price_hold")
    ppv_action = (
        t("revenue_ppv_low")
        if expected_tips_ppv < subscription_revenue * 0.20
        else t("revenue_ppv_high")
    )
    return [pricing_action, ppv_action, t("revenue_tips")]


def build_weekly_plan(growth_focus_key: str) -> list[dict[str, object]]:
    final_step_map = {
        "traffic": t("week4_step3_traffic"),
        "conversion": t("week4_step3_conversion"),
        "retention": t("week4_step3_retention"),
    }
    return [
        {
            "title_key": "week1_title",
            "steps": [t("week1_step1"), t("week1_step2"), t("week1_step3")],
        },
        {
            "title_key": "week2_title",
            "steps": [t("week2_step1"), t("week2_step2"), t("week2_step3")],
        },
        {
            "title_key": "week3_title",
            "steps": [t("week3_step1"), t("week3_step2"), t("week3_step3")],
        },
        {
            "title_key": "week4_title",
            "steps": [t("week4_step1"), t("week4_step2"), final_step_map[growth_focus_key]],
        },
    ]


def clean_bullets(raw_text: str) -> list[str]:
    bullets: list[str] = []
    for line in raw_text.splitlines():
        cleaned = line.strip().lstrip("-*0123456789. ").strip()
        if cleaned:
            bullets.append(cleaned)
    unique: list[str] = []
    for bullet in bullets:
        if bullet not in unique:
            unique.append(bullet)
    return unique[:3]


def generate_groq_strategy(profile: dict[str, float | str | int]) -> tuple[list[str] | None, str | None]:
    api_key = str(secret_get("groq", "api_key", default="") or "").strip()
    if not api_key or Groq is None:
        return None, t("groq_fallback_missing")

    prompt = textwrap.dedent(
        f"""
        You are a business-focused growth strategist for creator subscription businesses.
        Return exactly three concise actions for the next 7 days.
        Keep each action direct, practical, and non-explicit.

        Follower count: {profile['follower_count']}
        Monthly sub price: ${profile['monthly_sub_price']}
        Expected tips and PPV: ${profile['expected_tips_ppv']}
        Daily available time: {profile['daily_time']} hours
        Target income: ${profile['target_income']}
        Experience level: {profile['experience_level_code']}
        Main challenge: {profile['main_challenge']}
        """
    ).strip()

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Produce concise premium business actions only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=220,
        )
        content = completion.choices[0].message.content or ""
        bullets = clean_bullets(content)
        if len(bullets) == 3:
            return bullets, None
    except Exception:
        return None, t("groq_fallback_failed")

    return None, t("groq_fallback_failed")


def describe_strategy_changes(
    previous_result: dict[str, object],
    current_result: dict[str, object],
) -> list[str]:
    changes: list[str] = []
    previous_score = int(previous_result.get("score", 0))
    current_score = int(current_result.get("score", 0))
    score_delta = current_score - previous_score
    if score_delta > 0:
        changes.append(t("change_score_up").format(points=score_delta))
    elif score_delta < 0:
        changes.append(t("change_score_down").format(points=abs(score_delta)))

    previous_bottleneck = str(previous_result.get("bottleneck_key", ""))
    current_bottleneck = str(current_result.get("bottleneck_key", ""))
    if previous_bottleneck and current_bottleneck and previous_bottleneck != current_bottleneck:
        changes.append(
            t("change_bottleneck").format(
                previous=t(previous_bottleneck),
                current=t(current_bottleneck),
            )
        )

    previous_focus = str(previous_result.get("growth_focus_key", ""))
    current_focus = str(current_result.get("growth_focus_key", ""))
    if previous_focus and current_focus and previous_focus != current_focus:
        changes.append(
            t("change_focus").format(
                previous=t(previous_focus),
                current=t(current_focus),
            )
        )

    return changes or [t("no_changes_yet")]


def build_rule_based_strategy(
    profile: dict[str, float | int | str],
    financials: dict[str, float | int | str],
) -> dict[str, object]:
    growth_focus_key = determine_growth_focus(financials, profile)
    focus_label, focus_body = get_growth_focus_copy(growth_focus_key)
    bottleneck_key = determine_biggest_bottleneck(financials, profile)

    return {
        "immediate_fix": build_immediate_fix_actions(financials, profile, growth_focus_key),
        "revenue_optimization": build_revenue_optimization_actions(financials, profile),
        "growth_focus_key": growth_focus_key,
        "growth_focus_label": focus_label,
        "growth_focus_body": focus_body,
        "bottleneck_key": bottleneck_key,
        "biggest_bottleneck": t(bottleneck_key),
        "weekly_plan": build_weekly_plan(growth_focus_key),
    }


def generate_strategy_package(
    profile: dict[str, float | int | str],
    financials: dict[str, float | int | str],
    previous_result: dict[str, object] | None = None,
) -> dict[str, object]:
    score_details = compute_strategy_score(financials, profile)
    package = build_rule_based_strategy(profile, financials)
    package.update(score_details)
    package["profile"] = dict(profile)
    package["current_net_income"] = float(financials["net_income"])
    package["target_income"] = float(profile["target_income"])
    package["gap_value"] = float(profile["target_income"]) - float(financials["net_income"])

    bullets, warning = generate_groq_strategy(profile)
    if bullets:
        package["immediate_fix"] = bullets
    if warning:
        package["warning"] = warning

    if previous_result:
        package["what_changed"] = describe_strategy_changes(previous_result, package)
    else:
        package["what_changed"] = [t("no_changes_yet")]
    return package


def generate_quick_strategy(
    followers: int,
    engagement: float,
    price: float,
    posts_per_week: int,
) -> list[str]:
    strategies: list[str] = []

    if followers < 5000:
        strategies.append(t("quick_strategy_level_early"))
    elif followers < 20000:
        strategies.append(t("quick_strategy_level_mid"))
    else:
        strategies.append(t("quick_strategy_level_high"))

    if engagement < 2:
        strategies.append(t("quick_strategy_engagement_low"))
    elif engagement < 5:
        strategies.append(t("quick_strategy_engagement_mid"))
    else:
        strategies.append(t("quick_strategy_engagement_high"))

    if price > 20 and followers < 10000:
        strategies.append(t("quick_strategy_price_high"))
    elif price < 8:
        strategies.append(t("quick_strategy_price_low"))
    else:
        strategies.append(t("quick_strategy_price_ok"))

    if posts_per_week < 3:
        strategies.append(t("quick_strategy_content_low"))
    elif posts_per_week > 10:
        strategies.append(t("quick_strategy_content_high"))
    else:
        strategies.append(t("quick_strategy_content_ok"))

    return strategies


def build_quick_strategy_report(
    followers: int,
    engagement: float,
    price: float,
    posts_per_week: int,
) -> dict[str, object]:
    growth_message: str
    if followers < 5000:
        growth_message = t("mentor_problem_growth_early")
    elif followers < 20000:
        growth_message = t("mentor_problem_growth_mid")
    else:
        growth_message = t("mentor_problem_growth_high")

    if engagement < 2:
        engagement_message = t("mentor_problem_engagement_low").format(
            followers=f"{followers:,}",
            engagement=f"{engagement:.1f}",
        )
        biggest_mistake = t("mentor_biggest_mistake_low")
    elif engagement < 5:
        engagement_message = t("mentor_problem_engagement_mid")
        biggest_mistake = t("mentor_biggest_mistake_mid")
    else:
        engagement_message = t("mentor_problem_engagement_high")
        biggest_mistake = t("mentor_biggest_mistake_high")

    if price > 20 and followers < 10000:
        price_message = t("mentor_problem_price_high")
    elif price < 8:
        price_message = t("mentor_problem_price_low")
    else:
        price_message = t("mentor_problem_price_ok")

    if posts_per_week < 3:
        posts_message = t("mentor_problem_posts_low")
    elif posts_per_week > 10:
        posts_message = t("mentor_problem_posts_high")
    else:
        posts_message = t("mentor_problem_posts_ok")

    return {
        "summary": t("mentor_summary").format(
            followers=f"{followers:,}",
            engagement=f"{engagement:.1f}",
            price=format_currency(float(price)),
            posts=posts_per_week,
        ),
        "authority": [
            t("mentor_authority_1"),
            t("mentor_authority_2"),
        ],
        "biggest_mistake": biggest_mistake,
        "problems": [
            engagement_message,
            price_message,
            posts_message,
        ],
        "opportunities": [
            growth_message,
            t("mentor_opportunity_growth"),
            t("mentor_opportunity_offer"),
            t("mentor_opportunity_consistency"),
        ],
        "action_plan": [
            t("mentor_step_1"),
            t("mentor_step_2"),
            t("mentor_step_3"),
        ],
    }


def render_quick_strategy_engine(is_paid: bool) -> None:
    st.divider()
    st.markdown(f"### {t('quick_strategy_title')}")
    st.caption(t("quick_strategy_desc"))

    base_followers = max(int(st.session_state.get("follower_count", 1000)), 0)
    base_price = max(float(st.session_state.get("monthly_sub_price", 10.0)), 0.0)

    left, right = st.columns(2)
    with left:
        followers = st.number_input(
            t("quick_strategy_followers"),
            min_value=0,
            value=base_followers if "quick_strategy_followers" not in st.session_state else int(st.session_state["quick_strategy_followers"]),
            step=100,
            key="quick_strategy_followers",
        )
        engagement = st.number_input(
            t("quick_strategy_engagement"),
            min_value=0.0,
            value=float(st.session_state.get("quick_strategy_engagement", 1.5)),
            step=0.1,
            key="quick_strategy_engagement",
        )
    with right:
        price = st.number_input(
            t("quick_strategy_price"),
            min_value=0.0,
            value=base_price if "quick_strategy_price" not in st.session_state else float(st.session_state["quick_strategy_price"]),
            step=1.0,
            key="quick_strategy_price",
        )
        posts_per_week = st.number_input(
            t("quick_strategy_posts"),
            min_value=0,
            value=int(st.session_state.get("quick_strategy_posts", 3)),
            step=1,
            key="quick_strategy_posts",
        )

    score = 0
    if int(followers) > 10000:
        score += 2
    if float(engagement) > 3:
        score += 2
    if float(price) < 15:
        score += 1
    if int(posts_per_week) >= 4:
        score += 1

    estimated_income = float(followers) * 0.02 * float(price)
    potential_income = float(followers) * 0.05 * float(price)
    loss = max(int(potential_income - estimated_income), 0)

    render_metric_card(
        t("creator_score_title"),
        f"{score}/6",
        t("quick_strategy_title"),
    )
    if score < 3:
        st.error(f"🚨 {t('creator_score_underperforming')}")
    elif score < 5:
        st.warning(f"⚠ {t('creator_score_untapped')}")
    else:
        st.success(f"🔥 {t('creator_score_strong')}")

    render_note_card(
        t("quick_strategy_loss_title").format(amount=format_currency(float(loss))),
        t("loss_aversion_copy"),
    )
    st.markdown(f"👉 {t('quick_strategy_psychology_line')}")
    st.markdown(f"### {t('quick_strategy_potential_title')}")
    growth_columns = st.columns(2)
    with growth_columns[0]:
        render_metric_card(
            t("quick_strategy_current_label"),
            format_currency(float(estimated_income)),
            t("quick_strategy_current").format(amount=format_currency(float(estimated_income))),
        )
    with growth_columns[1]:
        render_metric_card(
            t("quick_strategy_optimized_label"),
            format_currency(float(potential_income)),
            t("quick_strategy_optimized").format(amount=format_currency(float(potential_income))),
        )
    st.caption(f"⚠ {t('quick_strategy_urgency')}")
    st.caption(f"💎 {t('quick_strategy_social_proof')}")

    if st.button(t("analyze_my_strategy"), use_container_width=True, key="analyze_my_strategy_button"):
        st.session_state["quick_strategy_result"] = build_quick_strategy_report(
            int(followers),
            float(engagement),
            float(price),
            int(posts_per_week),
        )

    quick_result = st.session_state.get("quick_strategy_result")
    if isinstance(quick_result, list) and quick_result:
        quick_result = build_quick_strategy_report(
            int(followers),
            float(engagement),
            float(price),
            int(posts_per_week),
        )
        st.session_state["quick_strategy_result"] = quick_result

    if isinstance(quick_result, dict):
        problems = [str(item) for item in quick_result.get("problems", []) if str(item).strip()]
        opportunities = [str(item) for item in quick_result.get("opportunities", []) if str(item).strip()]
        action_plan = [str(item) for item in quick_result.get("action_plan", []) if str(item).strip()]

        st.divider()
        st.markdown(f"## 🧠 {t('mentor_analysis_title')}")
        st.markdown(str(quick_result.get("summary", "")))
        authority_lines = quick_result.get("authority", [])
        if isinstance(authority_lines, list):
            for line in authority_lines:
                st.caption(str(line))

        st.divider()
        st.markdown(f"## 🚨 {t('mentor_problems_title')}")
        if problems:
            st.write("• " + problems[0])
        st.markdown(
            f"**{t('mentor_biggest_mistake_label')}:** {str(quick_result.get('biggest_mistake', ''))}"
        )

        if not is_paid:
            st.markdown(f"🔒 {t('quick_strategy_locked')}")
            st.markdown(f"**💎 {t('quick_strategy_vip_includes')}**")
            st.write("• " + t("quick_strategy_vip_item_1"))
            st.write("• " + t("quick_strategy_vip_item_2"))
            st.write("• " + t("quick_strategy_vip_item_3"))
            st.write("• " + t("quick_strategy_vip_item_4"))
        else:
            for item in problems[1:]:
                st.write("• " + item)
            st.divider()
            st.markdown(f"## ✨ {t('mentor_opportunities_title')}")
            for item in opportunities:
                st.write("• " + item)
            st.divider()
            st.markdown(f"## 🚀 {t('mentor_next_title')}")
            for item in action_plan:
                st.write(item)


def build_anonymous_creator_bible() -> str:
    return textwrap.dedent(
        """
        # The Girlpire Creator Bible

        ## Positioning (anonymous vs personal brand)
        Choose one clear identity path. Anonymous brands win with concept, consistency, and mystery. Personal brands win with familiarity, direct trust, and recurring personality-driven hooks.

        ## Pricing ladder
        Build a simple ladder: entry subscription, weekly premium upgrade, and one higher-value offer for your most engaged buyers. Fans spend more when the offer path is obvious.

        ## PPV system
        Treat PPV like a system, not a surprise. Use a weekly drop schedule, clear deadlines, and a small number of easy-to-understand premium tiers.

        ## Retention loops
        Retention grows when you create a loop: tease, drop, follow up, reactivate. Every week should include one retention touchpoint, not only acquisition work.

        ## Content batching system
        Batch core production, promo assets, and upsell planning separately. This reduces decision fatigue and makes weekly execution more consistent.

        ## Mistakes that kill growth
        - Relying on one revenue stream
        - Dropping price before fixing the offer
        - Scaling traffic before conversion improves
        - Ignoring retention while chasing new followers
        - Tracking gross revenue but not net margin
        """
    ).strip()


def build_strategy_report(
    financials: dict[str, float | int | str],
    strategy_result: dict[str, object],
    tracking_stats: dict[str, float],
) -> str:
    weekly_sections = []
    for week in strategy_result["weekly_plan"]:  # type: ignore[index]
        steps = "\n".join(f"- {step}" for step in week["steps"])
        weekly_sections.append(f"{t(week['title_key'])}\n{steps}")

    immediate_fix = "\n".join(
        f"- {item}" for item in strategy_result["immediate_fix"]  # type: ignore[index]
    )
    revenue_optimization = "\n".join(
        f"- {item}" for item in strategy_result["revenue_optimization"]  # type: ignore[index]
    )
    what_changed = "\n".join(
        f"- {item}" for item in strategy_result.get("what_changed", [])  # type: ignore[arg-type]
    )

    return textwrap.dedent(
        f"""
        {t("strategy_dashboard_title")}

        {t("current_net_income")}: {format_currency(float(financials["net_income"]))}
        {t("target_income_metric")}: {format_currency(float(strategy_result["target_income"]))}
        {t("gap_to_target")}: {format_currency(float(strategy_result["gap_value"]))}
        {t("strategy_score")}: {int(strategy_result["score"])}/100 ({strategy_result["status"]})

        {t("biggest_bottleneck_title")}:
        {strategy_result["biggest_bottleneck"]}

        {t("immediate_fix_title")}:
        {immediate_fix}

        {t("revenue_optimization_title")}:
        {revenue_optimization}

        {t("growth_focus_section")}:
        {strategy_result["growth_focus_label"]}: {strategy_result["growth_focus_body"]}

        {t("weekly_plan_title")}:
        {'\n\n'.join(weekly_sections)}

        {t("track_progress_title")}:
        {t("subscriber_growth")}: {tracking_stats["growth_percent"]:.1f}%
        {t("progress_to_target")}: {tracking_stats["progress_percent"]:.1f}%

        {t("what_changed_title")}:
        {what_changed}
        """
    ).strip()


@st.cache_data(show_spinner=False)
def load_pdf_bytes(path: str) -> bytes:
    file_path = Path(path)
    if not file_path.exists():
        return b""
    return file_path.read_bytes()


def build_scenarios(
    follower_count: int, monthly_sub_price: float, expected_tips_ppv: float
) -> dict[str, dict[str, float]]:
    return {
        t("conservative"): calculate_financials(
            max(int(follower_count * 0.8), 0),
            monthly_sub_price,
            expected_tips_ppv * 0.6,
        ),
        t("base_case"): calculate_financials(
            follower_count,
            monthly_sub_price,
            expected_tips_ppv,
        ),
        t("aggressive"): calculate_financials(
            int(follower_count * 1.25),
            monthly_sub_price,
            expected_tips_ppv * 1.5,
        ),
    }


def render_free_calculator() -> dict[str, float | int | str] | None:
    st.subheader(t("free_title"))
    st.caption(t("free_desc"))

    with st.form("money_engine_form"):
        col1, col2 = st.columns(2)
        with col1:
            follower_count = st.number_input(
                t("follower_count"),
                min_value=0,
                value=int(st.session_state.get("follower_count", 0)),
                step=10,
                key="follower_count",
            )
            monthly_sub_price = st.number_input(
                t("monthly_sub_price"),
                min_value=0.0,
                value=float(st.session_state.get("monthly_sub_price", 0.0)),
                step=0.5,
                key="monthly_sub_price",
            )
        with col2:
            expected_tips_ppv = st.number_input(
                t("expected_tips_ppv"),
                min_value=0.0,
                value=float(st.session_state.get("expected_tips_ppv", 0.0)),
                step=25.0,
                key="expected_tips_ppv",
            )
            target_income = st.number_input(
                t("target_monthly_income_input"),
                min_value=0.0,
                value=float(st.session_state.get("target_income_goal", 0.0)),
                step=100.0,
                key="target_income_goal",
            )
        submitted = st.form_submit_button(
            t("calculate_money_engine"),
            use_container_width=True,
        )

    if submitted:
        st.session_state["clicked_cta"] = False
        with st.spinner(t("analyzing_potential")):
            st.session_state["money_engine_result"] = build_money_engine_result(
                int(follower_count),
                float(monthly_sub_price),
                float(expected_tips_ppv),
                float(target_income),
            )

    result = st.session_state.get("money_engine_result")
    if not result:
        return None

    st.caption(t("estimate_note"))
    metrics = [
        (t("gross_income"), format_currency(float(result["gross_income"]))),
        (t("platform_fee"), format_currency(float(result["platform_fee"]))),
        (t("net_income"), format_currency(float(result["net_income"]))),
        (t("yearly_net_income"), format_currency(float(result["yearly_net_income"]))),
    ]
    metric_columns = st.columns(2)
    for index, (label, value) in enumerate(metrics):
        with metric_columns[index % 2]:
            render_metric_card(label, value)

    st.divider()
    engine_columns = st.columns(2)
    with engine_columns[0]:
        render_metric_card(
            t("revenue_per_fan"),
            t("revenue_per_fan_value").format(
                amount=format_currency(float(result["arppu"]))
            ),
            str(result["arppu_insight"]),
        )
    with engine_columns[1]:
        render_metric_card(
            t("target_engine_title"),
            f"{int(result['required_subscribers']):,}",
            t("target_engine_body").format(
                target=format_currency(float(result["target_income"])),
                fans=f"{int(result['required_subscribers']):,}",
            ),
        )

    if int(result["show_target_warning"]):
        render_note_card(
            t("target_engine_title"),
            t("target_engine_warning"),
        )

    st.divider()
    render_note_card(
        t("money_gap_title").format(
            amount=format_currency(float(result["money_gap"]))
        ),
        t("money_gap_body"),
    )
    st.caption(t("loss_aversion_copy"))
    render_note_card(
        t("cta_title"),
        str(result["stage_message"]),
    )
    st.caption(t("urgency_line"))
    st.divider()
    render_social_proof_section()
    return result


def render_cta_section(financials: dict[str, float | int | str]) -> None:
    render_note_card(
        t("cta_title"),
        f"{t('cta_desc')} {t('urgency_line')}",
    )
    left, right = st.columns(2)
    with left:
        if st.button(
            get_personalized_cta_text(float(financials["net_income"])),
            use_container_width=True,
        ):
            st.session_state["clicked_cta"] = True
    with right:
        if st.button(t("unlock_vip_guide"), use_container_width=True):
            st.session_state["clicked_cta"] = True
    render_vip_preview_cards()


def render_login_gate() -> None:
    if is_upgrade_flow():
        login_message = t("upgrade_login_prompt")
    elif is_from_email():
        login_message = t("email_login_prompt")
    else:
        login_message = t("login_gate_desc")
    render_note_card(t("login_gate_title"), login_message)
    login_disabled = not (auth_is_supported() and auth_is_configured())
    if st.button(
        t("continue_google"),
        use_container_width=True,
        type="primary",
        disabled=login_disabled,
    ):
        st.login("google")
    if not auth_is_supported():
        st.warning("This Streamlit build does not expose st.login / st.user / st.logout.")
    elif not auth_is_configured():
        st.warning(t("google_setup_missing"))
        st.info(t("google_setup_hint"))


def render_paywall(email: str) -> None:
    crypto_state_key = f"crypto_payment_url::{email.strip().lower()}"
    if is_upgrade_flow():
        render_note_card(t("upgrade_flow_title"), t("upgrade_paywall_prompt"))
    elif is_from_email():
        render_note_card(t("email_welcome_title"), t("email_paywall_prompt"))
    st.divider()
    st.subheader(t("paywall_title"))
    st.caption(t("paywall_desc"))
    st.warning(f"⚠ {t('paywall_urgency')}")
    render_metric_card(
        t("pricing_anchor_title"),
        get_vip_price_label(),
        t("pricing_anchor_note"),
    )
    render_list_card(
        t("vip_offer_title"),
        [
            t("vip_offer_item_1"),
            t("vip_offer_item_2"),
            t("vip_offer_item_3"),
            t("vip_offer_item_4"),
            t("vip_offer_item_5"),
        ],
    )
    st.caption(t("vip_offer_result_note"))
    st.caption(f"💰 {t('vip_pricing_message_1')}")
    st.caption(t("vip_pricing_message_2"))

    paywall_items = [
        t("vip_feature_strategy"),
        t("vip_feature_plan"),
        t("vip_feature_bible"),
        t("vip_feature_pricing"),
        t("vip_feature_ppv"),
        t("vip_feature_updates"),
    ]
    render_list_card(t("paywall_stack_title"), paywall_items)
    st.caption(t("paywall_stack_note"))

    checkout_url = build_checkout_url(email)
    crypto_checkout_container = st.container()
    card_enabled = card_checkout_enabled()
    crypto_enabled = crypto_checkout_enabled()
    if not st.session_state.get("premium_unlocked", False):
        st.warning(t("vip_upgrade_message"))
    if card_enabled and checkout_url:
        st.link_button(t("pay_with_card"), checkout_url, use_container_width=True)
    else:
        st.button(t("pay_with_card"), use_container_width=True, disabled=True, key="pay_with_card_disabled")
        st.caption(t("card_disabled_notice"))
    if crypto_enabled:
        if st.button(t("pay_with_crypto"), use_container_width=True):
            payment_url = create_crypto_payment(email)
            if payment_url:
                st.session_state[crypto_state_key] = payment_url
                st.success(t("crypto_payment_ready"))
            elif not get_nowpayments_api_key():
                st.error(t("crypto_payment_unavailable"))
            else:
                st.error(t("crypto_payment_failed"))
        saved_crypto_url = str(st.session_state.get(crypto_state_key, "") or "").strip()
        if saved_crypto_url:
            with crypto_checkout_container:
                render_note_card(t("crypto_step_title"), t("crypto_step_body"))
                st.info(t("crypto_payment_manual_hint"))
                st.link_button(t("open_crypto_payment"), saved_crypto_url, use_container_width=True)
                st.markdown(f"**{t('crypto_direct_link')}:** {saved_crypto_url}")
        st.caption(t("vip_sync_notice"))
    else:
        st.button(t("pay_with_crypto"), use_container_width=True, disabled=True, key="pay_with_crypto_disabled")
        st.caption(t("crypto_disabled_notice"))
        st.session_state.pop(crypto_state_key, None)
    st.caption(t("vip_refresh_checkout_notice"))
    if st.button(t("refresh_vip_access"), use_container_width=True):
        refreshed = check_lemonsqueezy_status(email, force_refresh=True) or sync_paid_user_from_remote(
            email
        )
        if refreshed:
            st.session_state["premium_unlocked"] = True
            st.success(t("vip_refresh_success"))
            st.rerun()
        st.warning(t("vip_refresh_pending"))
    render_checkout_button(
        checkout_url,
        t("start_vip_membership"),
        button_key="start_vip_membership_disabled",
        show_supporting_text=True,
    )
    st.divider()
    render_paywall_faq()
    render_checkout_button(
        checkout_url,
        t("unlock_vip_strategy"),
        button_key="unlock_vip_strategy_disabled",
        show_supporting_text=False,
    )
    st.caption(t("payment_notice"))


def render_admin_email_tools() -> None:
    if not admin_mode_enabled():
        return

    st.divider()
    st.subheader(t("admin_email_tools_title"))
    st.caption(t("admin_email_tools_desc"))
    st.caption(t("email_tools_future_ready"))
    email_store = ensure_email_store()
    render_metric_card(
        t("saved_email_count"),
        str(len(email_store.get("users", []))),
        t("monthly_email_subject"),
    )

    resend_warning = ""
    if resend is None:
        resend_warning = t("resend_package_missing")
    elif not get_resend_api_key():
        resend_warning = t("resend_missing_key")

    if resend_warning:
        st.warning(resend_warning)

    action_row = st.columns(2)
    with action_row[0]:
        if st.button(t("send_test_email"), use_container_width=True):
            target_email = get_current_user_email()
            if not target_email:
                target_email = get_test_email_fallback()
                st.info(t("email_test_fallback_used"))
            success, message = send_email(
                target_email,
                t("monthly_email_subject"),
                build_monthly_email_content(),
            )
            if success:
                st.success(message)
            else:
                st.warning(message)
    with action_row[1]:
        if st.button(t("send_to_all_users"), use_container_width=True):
            sent, failed = send_to_all_users()
            if sent == 0 and failed == 0:
                st.info(t("emails_empty"))
            else:
                st.info(t("email_bulk_sent_count").format(count=sent))
                if failed == 0:
                    st.success(t("email_bulk_success").format(sent=sent, failed=failed))
                else:
                    st.warning(t("email_bulk_success").format(sent=sent, failed=failed))


def build_dashboard_snapshot(
    financials: dict[str, float | int | str],
    profile: dict[str, float | int | str],
    strategy_result: dict[str, object] | None = None,
) -> dict[str, float | int | str]:
    if strategy_result:
        return {
            "current_net_income": float(strategy_result["current_net_income"]),
            "target_income": float(strategy_result["target_income"]),
            "gap_value": float(strategy_result["gap_value"]),
            "score": int(strategy_result["score"]),
            "status": str(strategy_result["status"]),
            "explanation": str(strategy_result["explanation"]),
        }

    score_details = compute_strategy_score(financials, profile)
    return {
        "current_net_income": float(financials["net_income"]),
        "target_income": float(profile["target_income"]),
        "gap_value": float(profile["target_income"]) - float(financials["net_income"]),
        "score": int(score_details["score"]),
        "status": str(score_details["status"]),
        "explanation": str(score_details["explanation"]),
    }


def get_current_month_key() -> str:
    return datetime.now().strftime("%Y-%m")


def get_focus_of_month(net_income: float) -> str:
    if net_income < 1000:
        return t("focus_low")
    if net_income <= 5000:
        return t("focus_mid")
    return t("focus_high")


def get_consistency_badge(update_count: int) -> str:
    if update_count >= 12:
        return t("badge_elite")
    if update_count >= 6:
        return t("badge_consistent")
    if update_count >= 3:
        return t("badge_active")
    if update_count >= 1:
        return t("badge_starter")
    return t("badge_none")


def get_reengagement_message() -> str:
    today = datetime.now().date()
    last_visit_raw = str(st.session_state.get("last_visit_date", "")).strip()
    message = ""
    if last_visit_raw:
        try:
            last_visit = datetime.fromisoformat(last_visit_raw).date()
            if (today - last_visit).days >= 7:
                message = t("welcome_back")
        except ValueError:
            message = ""
    st.session_state["last_visit_date"] = today.isoformat()
    return message


def refresh_monthly_strategy(
    financials: dict[str, float | int | str],
) -> dict[str, object]:
    previous_result = st.session_state.get("strategy_result")
    if isinstance(previous_result, dict):
        st.session_state["previous_strategy_result"] = previous_result

    profile = build_current_vip_profile(financials)
    package = generate_strategy_package(
        profile,
        financials,
        previous_result if isinstance(previous_result, dict) else None,
    )
    package["strategy_month"] = get_current_month_key()
    package["focus_of_month"] = get_focus_of_month(float(financials["net_income"]))
    st.session_state["strategy_result"] = package
    st.session_state["strategy_cycle_month"] = str(package["strategy_month"])
    return package


def render_monthly_cycle_section(
    financials: dict[str, float | int | str],
    strategy_result: dict[str, object] | None,
) -> dict[str, object] | None:
    st.divider()
    st.subheader(t("monthly_strategy_cycle_title"))
    current_month = get_current_month_key()
    active_result = strategy_result
    focus_of_month = (
        str(strategy_result.get("focus_of_month", ""))
        if isinstance(strategy_result, dict)
        else get_focus_of_month(float(financials["net_income"]))
    )
    render_metric_card(
        t("monthly_strategy_cycle_title"),
        current_month,
        f"{t('focus_of_month')}: {focus_of_month}",
    )

    stored_month = str(st.session_state.get("strategy_cycle_month", "")).strip()
    needs_refresh = stored_month != current_month or not isinstance(strategy_result, dict)
    if needs_refresh:
        render_note_card(t("monthly_strategy_cycle_title"), t("new_month_detected"))
    if st.button(t("generate_new_monthly_strategy"), use_container_width=True):
        active_result = refresh_monthly_strategy(financials)
    return active_result


def render_strategy_dashboard(snapshot: dict[str, float | int | str]) -> None:
    st.markdown(f"### {t('strategy_dashboard_title')}")
    top_row = st.columns(2)
    with top_row[0]:
        render_metric_card(
            t("current_net_income"),
            format_currency(float(snapshot["current_net_income"])),
            t("vip_title"),
        )
    with top_row[1]:
        render_metric_card(
            t("target_income_metric"),
            format_currency(float(snapshot["target_income"])),
            t("strategy_consultant"),
        )

    bottom_row = st.columns(2)
    with bottom_row[0]:
        render_metric_card(
            t("gap_to_target"),
            format_currency(float(snapshot["gap_value"])),
            t("money_gap_body"),
        )
    with bottom_row[1]:
        render_metric_card(
            t("strategy_score"),
            f"{int(snapshot['score'])}/100",
            str(snapshot["status"]),
        )

    render_note_card(t("strategy_score"), str(snapshot["explanation"]))


def render_vip_workspace(
    snapshot: dict[str, float | int | str],
    financials: dict[str, float | int | str],
    current_focus: str,
) -> None:
    follower_count = max(int(st.session_state.get("follower_count", 0)), 1)
    arppu = float(financials["gross_income"]) / follower_count if follower_count > 0 else 0.0
    margin = (
        (float(financials["net_income"]) / float(financials["gross_income"])) * 100
        if float(financials["gross_income"]) > 0
        else 0.0
    )
    current_month = get_current_month_key()
    user_name = get_current_user_name() or "Creator"
    user_picture = get_user_claim("picture", "")
    initials = "".join(part[:1] for part in user_name.split()[:2]).upper() or "GP"
    primary_nav_labels = [
        t("dashboard_nav_dashboard"),
        t("dashboard_nav_documents"),
        t("dashboard_nav_payments"),
        t("dashboard_nav_calendar"),
        t("dashboard_nav_profile"),
    ]
    utility_nav_labels = [
        t("dashboard_nav_darkmode"),
        t("dashboard_nav_settings"),
        t("dashboard_nav_logout"),
    ]
    nav_items = "".join(
        f"""
        <div class="wolf-dashboard-nav-item {'is-active' if index == 0 else ''}">
            <span class="wolf-dashboard-nav-dot"></span>
            <span>{html.escape(label)}</span>
        </div>
        """
        for index, label in enumerate(primary_nav_labels)
    )
    utility_items = "".join(
        f"""
        <div class="wolf-dashboard-nav-item is-utility">
            <span class="wolf-dashboard-nav-dot"></span>
            <span>{html.escape(label)}</span>
        </div>
        """
        for label in utility_nav_labels
    )
    profile_avatar = (
        f'<img class="wolf-dashboard-profile-avatar-img" src="{html.escape(user_picture, quote=True)}" alt="{html.escape(user_name)}" />'
        if user_picture
        else f'<div class="wolf-dashboard-profile-avatar">{html.escape(initials)}</div>'
    )
    sidebar_avatar = (
        f'<img class="wolf-dashboard-sidebar-avatar-img" src="{html.escape(user_picture, quote=True)}" alt="{html.escape(user_name)}" />'
        if user_picture
        else f'<div class="wolf-dashboard-sidebar-avatar">{html.escape(initials)}</div>'
    )

    st.markdown(
        f"""
        <div class="wolf-dashboard-frame">
            <div class="wolf-dashboard-topbar">
                <div class="wolf-dashboard-topbar-title">{html.escape(t("dashboard_top_title"))}</div>
                <div class="wolf-dashboard-topbar-meta">
                    <span>{html.escape(t("dashboard_workspace"))}</span>
                    <span>{html.escape(current_month)}</span>
                    <span class="wolf-dashboard-topbar-badge">VIP</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    side_col, main_col, profile_col = st.columns([0.82, 1.8, 0.95], gap="large")
    with side_col:
        st.markdown(
            f"""
            <div class="wolf-dashboard-side">
                <div class="wolf-dashboard-sidebar-profile">
                    {sidebar_avatar}
                    <div>
                        <div class="wolf-dashboard-sidebar-name">{html.escape(user_name)}</div>
                        <div class="wolf-dashboard-sidebar-role">{html.escape(t("vip_title"))}</div>
                    </div>
                </div>
                <div class="wolf-dashboard-nav-group">
                    {nav_items}
                </div>
                <div class="wolf-dashboard-nav-divider"></div>
                <div class="wolf-dashboard-nav-group">
                    {utility_items}
                </div>
                <div class="wolf-dashboard-side-promo">
                    <div class="wolf-dashboard-side-promo-title">{html.escape(t("dashboard_focus_chip"))}</div>
                    <p class="wolf-dashboard-side-promo-copy">{html.escape(current_focus)}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with main_col:
        st.markdown(
            f"""
            <div class="wolf-dashboard-hero">
                <div class="wolf-dashboard-chip-row">
                    <div class="wolf-dashboard-chip">{html.escape(t("dashboard_focus_chip"))}: {html.escape(current_focus)}</div>
                    <div class="wolf-dashboard-chip">{html.escape(t("dashboard_sync_chip"))}</div>
                    <div class="wolf-dashboard-chip">{html.escape(current_month)}</div>
                </div>
                <h2 class="wolf-dashboard-hero-title">{html.escape(t("dashboard_welcome").format(name=user_name))}</h2>
                <p class="wolf-dashboard-hero-body">{html.escape(t("dashboard_chart_body"))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="wolf-dashboard-searchbar">
                <div class="wolf-dashboard-searchbar-copy">{html.escape(t("dashboard_search_placeholder"))}</div>
                <div class="wolf-dashboard-search-actions">
                    <div class="wolf-dashboard-search-action">&#9906;</div>
                    <div class="wolf-dashboard-search-action">&#10022;</div>
                    <div class="wolf-dashboard-search-action">&#128276;</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        kpi_row_1 = st.columns(2, gap="large")
        with kpi_row_1[0]:
            render_metric_card(
                t("current_net_income"),
                format_currency(float(snapshot["current_net_income"])),
                str(snapshot["status"]),
            )
        with kpi_row_1[1]:
            render_metric_card(
                t("dashboard_card_growth"),
                format_currency(float(snapshot["gap_value"])),
                t("target_income_metric"),
            )

        kpi_row_2 = st.columns(2, gap="large")
        with kpi_row_2[0]:
            render_metric_card(
                t("dashboard_card_margin"),
                f"{margin:.0f}%",
                t("net_income"),
            )
        with kpi_row_2[1]:
            render_metric_card(
                t("dashboard_card_arppu"),
                format_currency(arppu),
                f"{t('dashboard_card_focus')}: {current_focus}",
            )

        st.markdown(
            f"""
            <div class="wolf-dashboard-chart">
                <div class="wolf-dashboard-chart-header">
                    <div>
                        <div class="wolf-dashboard-chart-title">{html.escape(t("dashboard_chart_title"))}</div>
                        <p class="wolf-dashboard-chart-copy">{html.escape(str(snapshot["explanation"]))}</p>
                    </div>
                    <div class="wolf-dashboard-pills">
                        <div class="wolf-dashboard-pill">30D</div>
                        <div class="wolf-dashboard-pill">90D</div>
                        <div class="wolf-dashboard-pill is-active">VIP</div>
                    </div>
                </div>
                <div class="wolf-dashboard-visual">
                    <div class="wolf-dashboard-line"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        bottom_left, bottom_right = st.columns(2, gap="large")
        with bottom_left:
            render_list_card(
                t("dashboard_nav_strategy"),
                [
                    t("immediate_fix_title"),
                    t("revenue_optimization_title"),
                    t("growth_focus_section"),
                    t("biggest_bottleneck_title"),
                ],
            )
        with bottom_right:
            render_note_card(
                t("dashboard_nav_membership"),
                f"{t('strategy_score')}: {int(snapshot['score'])}/100 • {t('focus_of_month')}: {current_focus}",
            )

    with profile_col:
        st.markdown(
            f"""
            <div class="wolf-dashboard-profile">
                <div class="wolf-dashboard-profile-top">
                    {profile_avatar}
                    <div class="wolf-dashboard-profile-name">{html.escape(user_name)}</div>
                    <div class="wolf-dashboard-profile-role">{html.escape(t("vip_title"))}</div>
                </div>
                <div class="wolf-dashboard-profile-actions">
                    <div class="wolf-dashboard-profile-action">&#128200;</div>
                    <div class="wolf-dashboard-profile-action">&#128172;</div>
                    <div class="wolf-dashboard-profile-action">&#10022;</div>
                </div>
                <div class="wolf-dashboard-profile-section">
                    <div class="wolf-dashboard-profile-label">{html.escape(t("dashboard_focus_chip"))}</div>
                    <p class="wolf-dashboard-profile-copy">{html.escape(current_focus)}</p>
                </div>
                <div class="wolf-dashboard-profile-section">
                    <div class="wolf-dashboard-profile-label">{html.escape(t("dashboard_sync_chip"))}</div>
                    <p class="wolf-dashboard-profile-copy">{html.escape(t("dashboard_workspace_body"))}</p>
                </div>
                <div class="wolf-dashboard-billing">
                    <div class="wolf-dashboard-billing-title">{html.escape(t("target_income_metric"))}</div>
                    <div class="wolf-dashboard-billing-value">{html.escape(format_currency(float(snapshot["target_income"])))}</div>
                    <div class="wolf-dashboard-billing-note">{html.escape(t("gap_to_target"))}: {html.escape(format_currency(float(snapshot["gap_value"])))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_structured_strategy(strategy_result: dict[str, object]) -> None:
    warning = strategy_result.get("warning")
    if warning:
        st.info(str(warning))

    top_row = st.columns(2)
    with top_row[0]:
        render_list_card(
            t("immediate_fix_title"),
            list(strategy_result["immediate_fix"]),  # type: ignore[arg-type]
        )
    with top_row[1]:
        render_list_card(
            t("revenue_optimization_title"),
            list(strategy_result["revenue_optimization"]),  # type: ignore[arg-type]
        )

    middle_row = st.columns(2)
    with middle_row[0]:
        render_note_card(
            t("growth_focus_section"),
            f"{strategy_result['growth_focus_label']}: {strategy_result['growth_focus_body']}",
        )
    with middle_row[1]:
        render_note_card(
            t("biggest_bottleneck_title"),
            str(strategy_result["biggest_bottleneck"]),
        )

    st.markdown(f"### {t('weekly_plan_title')}")
    week_columns = st.columns(2)
    weekly_plan = list(strategy_result["weekly_plan"])  # type: ignore[arg-type]
    for index, week in enumerate(weekly_plan):
        with week_columns[index % 2]:
            render_list_card(
                t(str(week["title_key"])),
                list(week["steps"]),
            )


def build_progress_feedback(
    revenue_growth: float,
    subscriber_growth: float,
    current_score: int,
    previous_snapshot: dict[str, float | int | str] | None,
    current_focus_key: str,
) -> dict[str, list[str] | str]:
    improved: list[str] = []
    declined: list[str] = []

    if revenue_growth > 0:
        improved.append(f"{t('revenue_growth')}: {revenue_growth:.1f}%")
    elif revenue_growth < 0:
        declined.append(f"{t('revenue_growth')}: {revenue_growth:.1f}%")

    if subscriber_growth > 0:
        improved.append(f"{t('subscriber_growth')}: {subscriber_growth:.1f}%")
    elif subscriber_growth < 0:
        declined.append(f"{t('subscriber_growth')}: {subscriber_growth:.1f}%")

    if previous_snapshot:
        previous_score = int(previous_snapshot.get("score", 0))
        if current_score > previous_score:
            improved.append(f"{t('strategy_score')}: +{current_score - previous_score}")
        elif current_score < previous_score:
            declined.append(f"{t('strategy_score')}: -{previous_score - current_score}")

    if revenue_growth > 0 and subscriber_growth >= 0:
        status_message = t("progress_positive")
    elif revenue_growth < 0 or subscriber_growth < 0:
        status_message = t("progress_negative")
    else:
        status_message = t("progress_mixed")

    fix_map = {
        "traffic": t("fix_next_traffic"),
        "conversion": t("fix_next_conversion"),
        "retention": t("fix_next_retention"),
    }

    return {
        "status_message": status_message,
        "improved": improved or [t("nothing_improved")],
        "declined": declined or [t("nothing_declined")],
        "fix_next": [fix_map.get(current_focus_key, t("fix_next_conversion"))],
    }


def render_history_table() -> None:
    st.divider()
    st.subheader(t("history_title"))
    history = st.session_state.get("history", [])
    if not history:
        st.caption(t("history_empty"))
        return

    rows = [
        {
            t("month"): item["month"],
            t("revenue"): format_currency(float(item["revenue"])),
            t("subscribers"): int(item["subscribers"]),
            t("strategy_score"): int(item["score"]),
        }
        for item in history
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_tracking_system(
    target_income: float,
    current_score: int,
    current_focus_key: str,
) -> dict[str, float]:
    st.divider()
    st.subheader(t("your_progress_title"))
    st.caption(t("tracking_growth_note"))

    input_row = st.columns(2)
    with input_row[0]:
        last_month_revenue = st.number_input(
            t("last_month_revenue"),
            min_value=0.0,
            value=float(st.session_state.get("tracking_last_month_revenue", 0.0)),
            step=50.0,
            key="tracking_last_month_revenue",
        )
        current_subscribers = st.number_input(
            t("current_subscribers"),
            min_value=0,
            value=int(st.session_state.get("tracking_current_subscribers", st.session_state.get("follower_count", 0))),
            step=10,
            key="tracking_current_subscribers",
        )
    with input_row[1]:
        current_revenue = st.number_input(
            t("current_revenue_input"),
            min_value=0.0,
            value=float(st.session_state.get("tracking_current_revenue", st.session_state.get("money_engine_result", {}).get("net_income", 0.0) if isinstance(st.session_state.get("money_engine_result"), dict) else 0.0)),
            step=50.0,
            key="tracking_current_revenue",
        )
        subscriber_change = st.number_input(
            t("subscriber_change"),
            value=int(st.session_state.get("tracking_subscriber_change", 20)),
            step=5,
            key="tracking_subscriber_change",
        )

    revenue_growth = (
        ((float(current_revenue) - float(last_month_revenue)) / float(last_month_revenue)) * 100
        if float(last_month_revenue) > 0
        else (100.0 if float(current_revenue) > 0 else 0.0)
    )
    previous_subscribers = max(int(current_subscribers) - int(subscriber_change), 1)
    growth_percent = (float(subscriber_change) / previous_subscribers) * 100 if current_subscribers > 0 else 0.0
    progress_percent = (float(current_revenue) / max(target_income, 1.0)) * 100 if target_income > 0 else 0.0

    metric_row = st.columns(3)
    with metric_row[0]:
        render_metric_card(
            t("revenue_growth"),
            f"{revenue_growth:.1f}%",
            t("current_revenue_input"),
        )
    with metric_row[1]:
        render_metric_card(
            t("subscriber_growth"),
            f"{growth_percent:.1f}%",
            t("current_subscribers"),
        )
    with metric_row[2]:
        render_metric_card(
            t("progress_to_target"),
            f"{progress_percent:.1f}%",
            format_currency(target_income),
        )

    history = st.session_state.get("history", [])
    previous_snapshot = history[-1] if history else None
    feedback = build_progress_feedback(
        revenue_growth,
        growth_percent,
        current_score,
        previous_snapshot if isinstance(previous_snapshot, dict) else None,
        current_focus_key,
    )
    render_note_card(t("your_progress_title"), str(feedback["status_message"]))
    feedback_row = st.columns(3)
    with feedback_row[0]:
        render_list_card(t("what_improved"), list(feedback["improved"]))  # type: ignore[arg-type]
    with feedback_row[1]:
        render_list_card(t("what_declined"), list(feedback["declined"]))  # type: ignore[arg-type]
    with feedback_row[2]:
        render_list_card(t("what_to_fix_next"), list(feedback["fix_next"]))  # type: ignore[arg-type]

    current_month = get_current_month_key()
    if st.button(t("save_monthly_update"), use_container_width=True):
        snapshot = {
            "month": current_month,
            "revenue": float(current_revenue),
            "subscribers": int(current_subscribers),
            "score": int(current_score),
        }
        updated_history = list(history)
        if updated_history and updated_history[-1]["month"] == current_month:
            updated_history[-1] = snapshot
        else:
            updated_history.append(snapshot)
        st.session_state["history"] = updated_history
        st.session_state["progress_update_count"] = int(
            st.session_state.get("progress_update_count", 0)
        ) + 1
        history = updated_history

    badge = get_consistency_badge(int(st.session_state.get("progress_update_count", 0)))
    render_metric_card(
        t("consistency_badge"),
        badge,
        f"{int(st.session_state.get('progress_update_count', 0))} updates",
    )
    render_history_table()
    return {
        "revenue_growth": revenue_growth,
        "growth_percent": growth_percent,
        "progress_percent": progress_percent,
        "current_subscribers": float(current_subscribers),
        "current_revenue": float(current_revenue),
        "new_subscribers": float(subscriber_change),
    }


def render_strategy_history(strategy_result: dict[str, object] | None) -> None:
    previous_result = st.session_state.get("previous_strategy_result")
    if not strategy_result or not isinstance(previous_result, dict):
        return

    summary_lines = [
        f"{t('previous_score')}: {int(previous_result.get('score', 0))}/100 ({previous_result.get('status', t('status_average'))})",
        f"{t('previous_bottleneck')}: {t(str(previous_result.get('bottleneck_key', 'bottleneck_system')))}",
        f"{t('previous_focus')}: {t(str(previous_result.get('growth_focus_key', 'conversion')))}",
    ]
    render_list_card(t("previous_strategy_title"), summary_lines)
    render_list_card(
        t("what_changed_title"),
        list(strategy_result.get("what_changed", [t("no_changes_yet")])),
    )


def render_strategy_export(
    financials: dict[str, float | int | str],
    strategy_result: dict[str, object],
    tracking_stats: dict[str, float],
) -> None:
    report_text = build_strategy_report(financials, strategy_result, tracking_stats)
    st.download_button(
        t("download_strategy_report"),
        data=report_text,
        file_name="my_strategy_report.txt",
        mime="text/plain",
        use_container_width=True,
    )


def render_vip_sidebar(current_focus_label: str) -> str:
    user_name = get_current_user_name() or "Creator"
    user_email = get_current_user_email() or ""
    user_picture = get_user_claim("picture", "")
    initials = "".join(part[:1] for part in user_name.split()[:2]).upper() or "GP"

    with st.sidebar:
        st.markdown(f"### {t('vip_title')}")
        if user_picture:
            st.image(user_picture, width=72)
        else:
            st.markdown(
                f'<div class="wolf-avatar">{html.escape(initials)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(f"**{user_name}**")
        if user_email:
            st.caption(user_email)
        st.success(t("vip_sidebar_status"))
        st.caption(f"{t('dashboard_focus_chip')}: {current_focus_label}")

        section_options = {
            "dashboard": t("vip_nav_dashboard"),
            "calculator": t("vip_nav_calculator"),
            "strategy": t("vip_nav_strategy"),
            "tracking": t("vip_nav_tracking"),
            "scenarios": t("vip_nav_scenarios"),
            "guide": t("vip_nav_guide"),
            "advanced": t("vip_nav_advanced"),
        }
        current_section = str(st.session_state.get("vip_section", "dashboard"))
        if current_section not in section_options:
            current_section = "dashboard"
        selected_section = st.radio(
            t("vip_nav_section"),
            options=list(section_options.keys()),
            index=list(section_options.keys()).index(current_section),
            format_func=lambda key: section_options[key],
            key="vip_section_radio",
        )
        st.session_state["vip_section"] = selected_section
        st.divider()
        st.button(t("logout"), use_container_width=True, on_click=st.logout, key="vip_sidebar_logout")

    return str(st.session_state.get("vip_section", "dashboard"))


def render_vip_dashboard_overview(
    financials: dict[str, float | int | str],
    dashboard_snapshot: dict[str, float | int | str],
    current_focus_label: str,
) -> None:
    st.subheader(t("strategy_dashboard_title"))
    top_row = st.columns(2)
    with top_row[0]:
        render_metric_card(
            t("current_net_income"),
            format_currency(float(dashboard_snapshot["current_net_income"])),
            str(dashboard_snapshot["status"]),
        )
    with top_row[1]:
        render_metric_card(
            t("target_income_metric"),
            format_currency(float(dashboard_snapshot["target_income"])),
            t("dashboard_focus_chip") + f": {current_focus_label}",
        )

    mid_row = st.columns(2)
    with mid_row[0]:
        render_metric_card(
            t("gap_to_target"),
            format_currency(float(dashboard_snapshot["gap_value"])),
            t("money_gap_body"),
        )
    with mid_row[1]:
        render_metric_card(
            t("strategy_score"),
            f"{int(dashboard_snapshot['score'])}/100",
            str(dashboard_snapshot["status"]),
        )

    bottom_row = st.columns(2)
    follower_count = max(int(st.session_state.get("follower_count", 0)), 1)
    arppu = float(financials["gross_income"]) / follower_count if follower_count > 0 else 0.0
    margin = (
        (float(financials["net_income"]) / float(financials["gross_income"])) * 100
        if float(financials["gross_income"]) > 0
        else 0.0
    )
    with bottom_row[0]:
        render_metric_card(
            t("dashboard_card_arppu"),
            format_currency(arppu),
            t("revenue_per_fan"),
        )
    with bottom_row[1]:
        render_metric_card(
            t("dashboard_card_margin"),
            f"{margin:.0f}%",
            t("net_income"),
        )

    render_note_card(t("dashboard_chart_title"), str(dashboard_snapshot["explanation"]))


def render_reference_vip_shell(
    financials: dict[str, float | int | str],
    dashboard_snapshot: dict[str, float | int | str],
    current_focus_label: str,
    selected_section: str,
    compact_mode: bool = False,
) -> None:
    section_options = get_vip_section_options()
    user_name = get_current_user_name() or "Girlpire Member"
    user_picture = get_user_claim("picture", "")
    initials = "".join(part[:1] for part in user_name.split()[:2]).upper() or "GP"
    profile_role = section_options.get(selected_section, t("vip_nav_dashboard"))

    net_income = float(financials.get("net_income", 0.0))
    gross_income = float(financials.get("gross_income", 0.0))
    total_expenses = float(st.session_state.get("monthly_expenses", 0.0)) + float(
        st.session_state.get("agency_cost", 0.0)
    )
    target_income = float(dashboard_snapshot.get("target_income", 0.0))
    gap_value = float(dashboard_snapshot.get("gap_value", 0.0))
    score_value = int(dashboard_snapshot.get("score", 0))
    status_value = str(dashboard_snapshot.get("status", t("status_average")))
    follower_count = max(int(st.session_state.get("follower_count", 0)), 1)
    arppu_value = gross_income / follower_count if follower_count > 0 else 0.0
    margin_pct = (net_income / gross_income) * 100 if gross_income > 0 else 0.0
    revenue_ring_pct = clamp_percentage(score_value)
    expense_ring_pct = clamp_percentage((total_expenses / gross_income) * 100 if gross_income > 0 else 0.0)
    target_pct = clamp_percentage((net_income / target_income) * 100 if target_income > 0 else 0.0)
    chart_label = datetime.now().strftime("%A, %d %B %Y")
    chart_tooltip = format_compact_currency(max(gross_income, net_income))

    top_sections = ["dashboard", "calculator", "strategy", "tracking", "scenarios"]
    bottom_sections = ["guide", "advanced"]
    nav_icons = {
        "dashboard": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
        "calculator": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="11" x2="8" y2="11"/><line x1="12" y1="11" x2="12" y2="11"/><line x1="16" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="8" y2="15"/><line x1="12" y1="15" x2="12" y2="15"/><line x1="16" y1="15" x2="16" y2="15"/></svg>',
        "strategy": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
        "tracking": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
        "scenarios": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        "guide": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
        "advanced": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06A2 2 0 1 1 4.37 17l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82L4.21 7.24a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.08a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.08a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
        "logout": '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
    }

    def nav_link(section_key: str, label: str, accent: bool = False) -> str:
        target_url = html.escape(
            build_app_url_with_params(
                vip_section=section_key if section_key != "logout" else selected_section,
                vip_action="logout" if section_key == "logout" else None,
            ),
            quote=True,
        )
        classes = "nav-item active" if section_key == selected_section else "nav-item"
        style = ' style="color:#ef4444;"' if accent else ""
        return (
            f'<a class="{classes}" href="{target_url}" target="_top"{style}>'
            f"{nav_icons.get(section_key, nav_icons['dashboard'])}"
            f"<span>{html.escape(label)}</span></a>"
        )

    nav_html = "".join(
        nav_link(section_key, section_options[section_key])
        for section_key in top_sections
        if section_key in section_options
    )
    utility_html = "".join(
        nav_link(section_key, section_options[section_key])
        for section_key in bottom_sections
        if section_key in section_options
    ) + nav_link("logout", t("dashboard_nav_logout"), accent=True)

    avatar_html = (
        f'<div class="profile-avatar"><img src="{html.escape(user_picture, quote=True)}" alt="{html.escape(user_name, quote=True)}"></div>'
        if user_picture
        else f'<div class="profile-avatar">{html.escape(initials)}</div>'
    )

    team_rows = [
        ("Pricing Engine", f"{format_currency(arppu_value)} / fan", "P"),
        ("Margin Control", f"{margin_pct:.0f}% margin", "M"),
        ("Focus of Month", current_focus_label, "F"),
    ]
    team_html = "".join(
        f"""
        <div class="team-member">
          <div class="member-avatar">{html.escape(initial)}</div>
          <div>
            <div class="member-name">{html.escape(name)}</div>
            <div class="member-role">{html.escape(role)}</div>
          </div>
        </div>
        """
        for name, role, initial in team_rows
    )

    progress_rows = [
        ("Pricing Ladder", "Lift revenue per fan", format_compact_currency(arppu_value), current_focus_label, 72, "#10b981"),
        ("Retention Loop", "Protect margin", f"{margin_pct:.0f}%", status_value, 58, "#f59e0b"),
        ("VIP Growth Map", "Close the revenue gap", format_compact_currency(gap_value), t("strategy_score"), max(target_pct, 84), "#7c3aed"),
    ]
    progress_html = "".join(
        f"""
        <div class="table-row"{' style="border-bottom:none;"' if index == len(progress_rows) - 1 else ''}>
          <div class="table-name">
            <div class="table-avatar">{html.escape(name[:1])}</div>
            <span>{html.escape(name)}</span>
          </div>
          <div>
            <div style="font-size:11px;color:var(--text-muted);">{html.escape(progress)}</div>
            <div class="progress-bar"><div class="progress-fill" style="width:{pct}%;"></div></div>
          </div>
          <div style="font-weight:600;">{html.escape(achieved)}</div>
          <div>
            <span class="status-badge">
              <span class="status-dot" style="background:{color};"></span>
              {html.escape(status)}
            </span>
          </div>
          <div class="dots-btn">⋯</div>
        </div>
        """
        for index, (name, progress, achieved, status, pct, color) in enumerate(progress_rows)
    )

    circumference = 151
    revenue_dash = max(0, min(circumference, round((revenue_ring_pct / 100) * circumference, 1)))
    expense_dash = max(0, min(circumference, round((expense_ring_pct / 100) * circumference, 1)))
    donut_dash = max(0, min(239, round((target_pct / 100) * 239, 1)))

    template = textwrap.dedent(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Girlpire Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
          :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #1e2340;
            --bg-card-hover: #242b4d;
            --bg-sidebar: #12172b;
            --accent-purple: #7c3aed;
            --accent-purple-light: #9d6ef8;
            --accent-violet: #6d28d9;
            --gradient-main: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
            --gradient-expense: linear-gradient(135deg, #6d28d9 0%, #7c3aed 100%);
            --text-primary: #f0f0ff;
            --text-secondary: #8b92b8;
            --text-muted: #5a6080;
            --border: rgba(124, 58, 237, 0.15);
            --border-active: rgba(124, 58, 237, 0.5);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --radius: 16px;
            --radius-sm: 10px;
            --sidebar-width: 200px;
          }
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            overflow: hidden;
          }
          .sidebar {
            width: var(--sidebar-width);
            background: var(--bg-sidebar);
            display: flex;
            flex-direction: column;
            padding: 24px 0;
            flex-shrink: 0;
            border-right: 1px solid var(--border);
            position: relative;
            z-index: 10;
          }
          .sidebar-logo {
            padding: 0 20px 28px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 3px;
            color: var(--text-secondary);
            text-transform: uppercase;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
          }
          .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 20px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 13.5px;
            font-weight: 400;
            color: var(--text-secondary);
            position: relative;
            text-decoration: none;
          }
          .nav-item:hover { color: var(--text-primary); background: rgba(124,58,237,0.08); }
          .nav-item.active {
            color: var(--text-primary);
            background: rgba(124,58,237,0.12);
            font-weight: 600;
          }
          .nav-item.active::before {
            content: '';
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 3px;
            background: var(--gradient-main);
            border-radius: 0 3px 3px 0;
          }
          .nav-icon {
            width: 18px; height: 18px;
            opacity: 0.8;
            flex-shrink: 0;
          }
          .nav-divider {
            height: 1px;
            background: var(--border);
            margin: 16px 20px;
          }
          .sidebar-bottom {
            margin-top: auto;
            padding: 0 12px;
          }
          .upgrade-card {
            background: rgba(124,58,237,0.15);
            border: 1px solid var(--border-active);
            border-radius: var(--radius);
            padding: 16px;
            text-align: center;
            transition: all 0.2s;
          }
          .upgrade-icon {
            width: 36px; height: 36px;
            background: var(--gradient-main);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 10px;
            font-size: 16px;
          }
          .upgrade-card p { font-size: 12px; color: var(--text-primary); font-weight: 600; }
          .upgrade-card span { font-size: 10px; color: var(--text-secondary); }
          .main {
            flex: 1;
            display: flex;
            overflow: hidden;
          }
          .center-panel {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
          }
          .center-panel::-webkit-scrollbar { width: 4px; }
          .center-panel::-webkit-scrollbar-track { background: transparent; }
          .center-panel::-webkit-scrollbar-thumb { background: var(--accent-purple); border-radius: 4px; }
          .topbar {
            display: flex;
            align-items: center;
            gap: 16px;
          }
          .search-box {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-muted);
            font-size: 13px;
            transition: border-color 0.2s;
          }
          .topbar-btn {
            width: 40px; height: 40px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            display: flex; align-items: center; justify-content: center;
            position: relative;
            color: var(--text-secondary);
            font-size: 16px;
          }
          .badge {
            position: absolute;
            top: -4px; right: -4px;
            width: 16px; height: 16px;
            background: var(--accent-purple);
            border-radius: 50%;
            font-size: 9px;
            font-weight: 700;
            display: flex; align-items: center; justify-content: center;
            color: white;
          }
          .stat-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }
          .stat-card {
            border-radius: var(--radius);
            padding: 22px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
          }
          .stat-card.finance { background: var(--gradient-main); }
          .stat-card.expense { background: var(--gradient-expense); }
          .stat-card::before {
            content: '';
            position: absolute;
            top: -30px; right: -30px;
            width: 100px; height: 100px;
            background: rgba(255,255,255,0.06);
            border-radius: 50%;
          }
          .stat-label { font-size: 12px; font-weight: 500; opacity: 0.85; margin-bottom: 6px; }
          .stat-value { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }
          .stat-ring {
            width: 58px; height: 58px;
            position: relative;
            flex-shrink: 0;
          }
          .stat-ring svg { transform: rotate(-90deg); }
          .stat-ring-label {
            position: absolute;
            inset: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px;
            font-weight: 700;
          }
          .charts-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }
          .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
          }
          .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
          }
          .card-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
          .card-menu {
            width: 24px; height: 24px;
            display: flex; align-items: center; justify-content: center;
            color: var(--text-muted);
            font-size: 14px;
            border-radius: 6px;
          }
          .chart-container {
            position: relative;
            height: 120px;
          }
          .chart-svg { width: 100%; height: 100%; }
          .chart-tooltip {
            background: var(--accent-purple);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 10px;
            font-weight: 700;
            position: absolute;
            top: 20px;
            left: 55%;
            transform: translateX(-50%);
          }
          .chart-tooltip::after {
            content: '';
            position: absolute;
            top: 100%; left: 50%;
            transform: translateX(-50%);
            border: 4px solid transparent;
            border-top-color: var(--accent-purple);
          }
          .chart-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 10px;
            color: var(--text-muted);
          }
          .donut-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
          }
          .donut-wrap {
            position: relative;
            width: 100px; height: 100px;
          }
          .donut-wrap svg { transform: rotate(-90deg); }
          .donut-label {
            position: absolute;
            inset: 0;
            display: flex; align-items: center; justify-content: center;
            flex-direction: column;
          }
          .donut-pct { font-size: 20px; font-weight: 700; }
          .donut-legend {
            display: flex;
            gap: 16px;
            font-size: 10px;
            color: var(--text-secondary);
            flex-wrap: wrap;
            justify-content: center;
          }
          .legend-dot {
            display: inline-block;
            width: 7px; height: 7px;
            border-radius: 50%;
            margin-right: 5px;
          }
          .table-shell { overflow-x: auto; }
          .table-header {
            display: grid;
            grid-template-columns: 2fr 1.5fr 1fr 1.2fr 0.5fr;
            padding: 0 0 10px;
            min-width: 640px;
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 500;
            border-bottom: 1px solid var(--border);
            margin-bottom: 10px;
          }
          .table-row {
            display: grid;
            grid-template-columns: 2fr 1.5fr 1fr 1.2fr 0.5fr;
            min-width: 640px;
            padding: 10px 0;
            font-size: 12.5px;
            align-items: center;
            border-bottom: 1px solid var(--border);
            transition: background 0.2s;
            border-radius: var(--radius-sm);
          }
          .table-row:hover { background: rgba(124,58,237,0.06); padding-left: 6px; padding-right: 6px; }
          .table-name {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .table-avatar {
            width: 28px; height: 28px;
            border-radius: 50%;
            background: linear-gradient(135deg,#7c3aed,#a855f7);
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700;
            flex-shrink: 0;
          }
          .progress-bar {
            height: 4px;
            background: rgba(255,255,255,0.08);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 4px;
            width: 80px;
          }
          .progress-fill {
            height: 100%;
            background: var(--gradient-main);
            border-radius: 4px;
          }
          .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            color: var(--text-secondary);
          }
          .status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
          .dots-btn { color: var(--text-muted); font-size: 14px; }
          .right-panel {
            width: 230px;
            flex-shrink: 0;
            background: var(--bg-secondary);
            border-left: 1px solid var(--border);
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
          }
          .profile-card {
            text-align: center;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
          }
          .profile-avatar {
            width: 64px; height: 64px;
            border-radius: 50%;
            background: var(--gradient-main);
            margin: 0 auto 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
            font-weight: 700;
            border: 3px solid rgba(124,58,237,0.4);
            position: relative;
            overflow: hidden;
          }
          .profile-avatar img { width: 100%; height: 100%; object-fit: cover; }
          .profile-name { font-size: 14px; font-weight: 700; }
          .profile-role { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
          .profile-actions {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 12px;
          }
          .profile-btn {
            width: 32px; height: 32px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            display: flex; align-items: center; justify-content: center;
            font-size: 13px;
            color: var(--text-secondary);
          }
          .section-title { font-size: 11px; font-weight: 700; color: var(--text-secondary); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 10px; }
          .about-text { font-size: 11px; color: var(--text-muted); line-height: 1.6; margin-bottom: 14px; }
          .team-member {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
          }
          .team-member:last-child { border-bottom: none; }
          .member-avatar {
            width: 30px; height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg,#7c3aed,#a855f7);
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700;
            flex-shrink: 0;
            overflow: hidden;
          }
          .member-name { font-size: 12px; font-weight: 600; }
          .member-role { font-size: 10px; color: var(--text-muted); }
          .send-money-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          .send-money-label { font-size: 10px; color: var(--text-muted); }
          .send-money-value { font-size: 16px; font-weight: 700; }
          .send-money-left { display: flex; align-items: center; gap: 8px; }
          .card-chip {
            width: 30px; height: 20px;
            background: var(--gradient-main);
            border-radius: 4px;
            display: flex; align-items: center; justify-content: center;
            font-size: 8px;
            font-weight: 700;
          }
          .view-all { font-size: 11px; color: var(--accent-purple-light); }
          @media (max-width: 1180px) {
            body { overflow: auto; }
            .main { flex-direction: column; }
            .right-panel {
              width: 100%;
              border-left: none;
              border-top: 1px solid var(--border);
            }
          }
          @media (max-width: 860px) {
            body { display: block; }
            .sidebar {
              width: 100%;
              border-right: none;
              border-bottom: 1px solid var(--border);
            }
            .stat-row, .charts-row { grid-template-columns: 1fr; }
            .center-panel { padding: 18px; }
            .topbar { flex-wrap: wrap; }
            .search-box { width: 100%; }
          }
        </style>
        </head>
        <body>
        <aside class="sidebar">
          <div class="sidebar-logo">Girlpire</div>
          <nav>__NAV_ITEMS__</nav>
          <div class="nav-divider"></div>
          <nav>__UTILITY_ITEMS__</nav>
          <div class="sidebar-bottom" style="margin-top:24px;">
            <div class="upgrade-card">
              <div class="upgrade-icon">💎</div>
              <p>Girlpire VIP</p>
              <span>Verified membership active</span>
            </div>
          </div>
        </aside>
        <div class="main">
          <div class="center-panel">
            <div class="topbar">
              <div class="search-box">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                __SEARCH_PLACEHOLDER__
              </div>
              <div class="topbar-btn">🛒<div class="badge">4</div></div>
              <div class="topbar-btn">🔔<div class="badge">3</div></div>
            </div>
            <div class="stat-row">
              <div class="stat-card finance">
                <div>
                  <div class="stat-label">Total Finance</div>
                  <div class="stat-value">__FINANCE_VALUE__</div>
                </div>
                <div class="stat-ring">
                  <svg width="58" height="58" viewBox="0 0 58 58">
                    <circle cx="29" cy="29" r="24" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="5"/>
                    <circle cx="29" cy="29" r="24" fill="none" stroke="white" stroke-width="5" stroke-dasharray="__FINANCE_DASH__ 151" stroke-linecap="round"/>
                  </svg>
                  <div class="stat-ring-label">+__FINANCE_PCT__%</div>
                </div>
              </div>
              <div class="stat-card expense">
                <div>
                  <div class="stat-label">Total Expense</div>
                  <div class="stat-value">__EXPENSE_VALUE__</div>
                </div>
                <div class="stat-ring">
                  <svg width="58" height="58" viewBox="0 0 58 58">
                    <circle cx="29" cy="29" r="24" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="5"/>
                    <circle cx="29" cy="29" r="24" fill="none" stroke="white" stroke-width="5" stroke-dasharray="__EXPENSE_DASH__ 151" stroke-linecap="round"/>
                  </svg>
                  <div class="stat-ring-label">+__EXPENSE_PCT__%</div>
                </div>
              </div>
            </div>
            <div class="charts-row">
              <div class="card">
                <div class="card-header">
                  <div class="card-title" style="font-size:14px;color:var(--text-primary);font-weight:700;">__CHART_DATE__</div>
                </div>
                <div class="chart-container">
                  <div class="chart-tooltip">__CHART_TOOLTIP__</div>
                  <svg class="chart-svg" viewBox="0 0 300 100" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#7c3aed" stop-opacity="0.4"/>
                        <stop offset="100%" stop-color="#7c3aed" stop-opacity="0"/>
                      </linearGradient>
                    </defs>
                    <line x1="0" y1="20" x2="300" y2="20" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
                    <line x1="0" y1="50" x2="300" y2="50" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
                    <line x1="0" y1="80" x2="300" y2="80" stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
                    <path d="M0,85 L30,70 L60,65 L90,72 L120,58 L150,40 L180,50 L210,42 L240,35 L270,28 L300,18 L300,100 L0,100 Z" fill="url(#chartGrad)"/>
                    <path d="M0,85 L30,70 L60,65 L90,72 L120,58 L150,40 L180,50 L210,42 L240,35 L270,28 L300,18" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="150" cy="40" r="5" fill="#7c3aed" stroke="white" stroke-width="2"/>
                  </svg>
                </div>
                <div class="chart-labels">
                  <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                </div>
              </div>
              <div class="card">
                <div class="card-header">
                  <div class="card-title" style="font-size:14px;color:var(--text-primary);font-weight:700;">Your Finance Target</div>
                  <div class="card-menu">⋮</div>
                </div>
                <div class="donut-container">
                  <div class="donut-wrap">
                    <svg width="100" height="100" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
                      <circle cx="50" cy="50" r="38" fill="none" stroke="url(#donutGrad)" stroke-width="10" stroke-dasharray="__DONUT_DASH__ 239" stroke-linecap="round"/>
                      <defs>
                        <linearGradient id="donutGrad" x1="0" y1="0" x2="1" y2="1">
                          <stop offset="0%" stop-color="#7c3aed"/>
                          <stop offset="100%" stop-color="#a855f7"/>
                        </linearGradient>
                      </defs>
                    </svg>
                    <div class="donut-label"><div class="donut-pct">__TARGET_PCT__%</div></div>
                  </div>
                  <div class="donut-legend">
                    <span><span class="legend-dot" style="background:#7c3aed;"></span>Result Achieved</span>
                    <span><span class="legend-dot" style="background:rgba(255,255,255,0.2);"></span>In The Process</span>
                  </div>
                  <div style="font-size:10px;color:var(--text-muted);text-align:center;">__FOCUS_TEXT__</div>
                </div>
              </div>
            </div>
            <div class="card">
              <div class="card-header">
                <div class="card-title" style="font-size:14px;color:var(--text-primary);font-weight:700;">Projects Finance</div>
                <div class="view-all">__SECTION_LABEL__</div>
              </div>
              <div class="table-shell">
                <div class="table-header">
                  <span>Name</span>
                  <span>Progress</span>
                  <span>Achieved</span>
                  <span>Status</span>
                  <span></span>
                </div>
                __PROJECT_ROWS__
              </div>
            </div>
          </div>
          <aside class="right-panel">
            <div class="profile-card">
              __PROFILE_AVATAR__
              <div class="profile-name">__PROFILE_NAME__</div>
              <div class="profile-role">__PROFILE_ROLE__</div>
              <div class="profile-actions">
                <div class="profile-btn">👤</div>
                <div class="profile-btn">✉️</div>
                <div class="profile-btn">🔗</div>
              </div>
            </div>
            <div>
              <div class="section-title">About</div>
              <div class="about-text">__ABOUT_TEXT__</div>
              <div class="section-title">Team</div>
              __TEAM_ROWS__
            </div>
            <div>
              <div class="section-title">Send Money</div>
              <div class="send-money-card">
                <div class="send-money-left">
                  <div class="card-chip">VIP</div>
                  <div><div class="send-money-label">Current Goal</div></div>
                </div>
                <div class="send-money-value">__SEND_VALUE__</div>
              </div>
            </div>
          </aside>
        </div>
        </body>
        </html>
        """
    ).strip()

    html_output = (
        template.replace("__NAV_ITEMS__", nav_html)
        .replace("__UTILITY_ITEMS__", utility_html)
        .replace("__SEARCH_PLACEHOLDER__", html.escape(t("dashboard_search_placeholder")))
        .replace("__FINANCE_VALUE__", html.escape(format_compact_currency(net_income)))
        .replace("__FINANCE_DASH__", str(revenue_dash))
        .replace("__FINANCE_PCT__", str(revenue_ring_pct))
        .replace("__EXPENSE_VALUE__", html.escape(format_compact_currency(total_expenses)))
        .replace("__EXPENSE_DASH__", str(expense_dash))
        .replace("__EXPENSE_PCT__", str(expense_ring_pct))
        .replace("__CHART_DATE__", html.escape(chart_label))
        .replace("__CHART_TOOLTIP__", html.escape(chart_tooltip))
        .replace("__DONUT_DASH__", str(donut_dash))
        .replace("__TARGET_PCT__", str(target_pct))
        .replace("__FOCUS_TEXT__", html.escape(current_focus_label))
        .replace("__SECTION_LABEL__", html.escape(section_options.get(selected_section, t("vip_nav_dashboard"))))
        .replace("__PROJECT_ROWS__", progress_html)
        .replace("__PROFILE_AVATAR__", avatar_html)
        .replace("__PROFILE_NAME__", html.escape(user_name))
        .replace("__PROFILE_ROLE__", html.escape(profile_role))
        .replace("__ABOUT_TEXT__", html.escape(str(dashboard_snapshot.get("explanation", ""))))
        .replace("__TEAM_ROWS__", team_html)
        .replace("__SEND_VALUE__", html.escape(format_compact_currency(target_income if target_income > 0 else gross_income)))
    )
    if compact_mode:
        html_output = html_output.replace(
            "</style>",
            """
            .sidebar{display:none !important;}
            .right-panel{display:none !important;}
            .center-panel{padding:0 0 0 0;}
            .main{display:block;}
            body{display:block;overflow:hidden;}
            </style>
            """,
        )
    components.html(html_output, height=760 if compact_mode else 1160, scrolling=False)


def render_vip_navigation_panel(selected_section: str, current_focus_label: str) -> None:
    section_options = get_vip_section_options()
    user_name = get_current_user_name() or "Girlpire Member"
    user_email = get_current_user_email() or ""
    checkout_url = build_checkout_url(user_email)
    crypto_state_key = f"sidebar_crypto_payment_url::{user_email.strip().lower()}"
    user_picture = get_user_claim("picture", "")
    initials = "".join(part[:1] for part in user_name.split()[:2]).upper() or "GP"
    avatar_html = (
        f'<img class="wolf-avatar-img" src="{html.escape(user_picture, quote=True)}" alt="{html.escape(user_name)}" />'
        if user_picture
        else f'<div class="wolf-avatar">{html.escape(initials)}</div>'
    )

    st.markdown(
        f"""
        <div class="wolf-card wolf-vip-sidebar-shell">
            <div class="wolf-vip-sidebar-profile">
                <div class="wolf-vip-sidebar-brand">{get_brand_symbol_html()}</div>
                {avatar_html}
                <div class="wolf-vip-sidebar-name">{html.escape(user_name)}</div>
                <div class="wolf-vip-sidebar-email">{html.escape(user_email)}</div>
                <div class="wolf-vip-sidebar-chip">{html.escape(t("dashboard_vip_badge"))}</div>
                <div class="wolf-vip-sidebar-chip">{html.escape(current_focus_label)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for key, label in section_options.items():
        button_type = "primary" if key == selected_section else "secondary"
        if st.button(label, key=f"vip_nav_{key}", use_container_width=True, type=button_type):
            st.session_state["vip_section"] = key
            st.rerun()

    st.button(t("logout"), key="vip_nav_logout", use_container_width=True, on_click=st.logout)
    st.markdown(
        f'<div class="wolf-panel-label" style="margin-top:0.85rem;">{html.escape(t("language"))}</div>',
        unsafe_allow_html=True,
    )
    render_language_selector("vip_language_selector")

    st.divider()
    if card_checkout_enabled() and checkout_url:
        st.link_button(t("pay_with_card"), checkout_url, use_container_width=True)
    else:
        st.button(t("pay_with_card"), disabled=True, use_container_width=True, key="vip_nav_card_disabled")
        st.caption(t("card_disabled_notice"))

    if crypto_checkout_enabled():
        if st.button(t("pay_with_crypto"), key="vip_nav_crypto", use_container_width=True):
            payment_url = create_crypto_payment(user_email)
            if payment_url:
                st.session_state[crypto_state_key] = payment_url
                st.success(t("crypto_payment_ready"))
            elif not get_nowpayments_api_key():
                st.warning(t("crypto_payment_unavailable"))
            else:
                st.error(t("crypto_payment_failed"))

        saved_crypto_url = str(st.session_state.get(crypto_state_key, "") or "").strip()
        if saved_crypto_url:
            st.link_button(
                t("open_crypto_payment"),
                saved_crypto_url,
                use_container_width=True,
            )
    else:
        st.button(
            t("pay_with_crypto"),
            key="vip_nav_crypto_disabled",
            use_container_width=True,
            disabled=True,
        )
        st.caption(t("crypto_disabled_notice"))
        st.session_state.pop(crypto_state_key, None)


def render_vip_calculator_section() -> dict[str, float | int | str] | None:
    st.subheader(t("vip_nav_calculator"))
    with st.form("vip_money_engine_form"):
        col1, col2 = st.columns(2)
        with col1:
            follower_count = st.number_input(
                t("follower_count"),
                min_value=0,
                value=int(st.session_state.get("follower_count", 0)),
                step=10,
                key="vip_calc_follower_count",
            )
            monthly_sub_price = st.number_input(
                t("monthly_sub_price"),
                min_value=0.0,
                value=float(st.session_state.get("monthly_sub_price", 0.0)),
                step=0.5,
                key="vip_calc_monthly_sub_price",
            )
        with col2:
            expected_tips_ppv = st.number_input(
                t("expected_tips_ppv"),
                min_value=0.0,
                value=float(st.session_state.get("expected_tips_ppv", 0.0)),
                step=25.0,
                key="vip_calc_expected_tips_ppv",
            )
            target_income = st.number_input(
                t("target_monthly_income_input"),
                min_value=0.0,
                value=float(st.session_state.get("target_income_goal", 0.0)),
                step=100.0,
                key="vip_calc_target_income_goal",
            )
        submitted = st.form_submit_button(
            t("calculate_money_engine"),
            use_container_width=True,
        )

    if submitted:
        with st.spinner(t("analyzing_potential")):
            st.session_state["follower_count"] = int(follower_count)
            st.session_state["monthly_sub_price"] = float(monthly_sub_price)
            st.session_state["expected_tips_ppv"] = float(expected_tips_ppv)
            st.session_state["target_income_goal"] = float(target_income)
            st.session_state["money_engine_result"] = build_money_engine_result(
                int(follower_count),
                float(monthly_sub_price),
                float(expected_tips_ppv),
                float(target_income),
            )
        st.rerun()

    result = st.session_state.get("money_engine_result")
    if not isinstance(result, dict):
        render_note_card(t("vip_nav_calculator"), t("free_desc"))
        return None

    st.caption(t("estimate_note"))
    metrics = [
        (t("gross_income"), format_currency(float(result["gross_income"]))),
        (t("platform_fee"), format_currency(float(result["platform_fee"]))),
        (t("net_income"), format_currency(float(result["net_income"]))),
        (t("yearly_net_income"), format_currency(float(result["yearly_net_income"]))),
    ]
    metric_columns = st.columns(2)
    for index, (label, value) in enumerate(metrics):
        with metric_columns[index % 2]:
            render_metric_card(label, value)

    secondary_row = st.columns(2)
    with secondary_row[0]:
        render_metric_card(
            t("revenue_per_fan"),
            t("revenue_per_fan_value").format(amount=format_currency(float(result["arppu"]))),
            str(result["arppu_insight"]),
        )
    with secondary_row[1]:
        render_metric_card(
            t("target_engine_title"),
            f"{int(result['required_subscribers']):,}",
            t("target_engine_body").format(
                target=format_currency(float(result["target_income"])),
                fans=f"{int(result['required_subscribers']):,}",
            ),
        )
    return result


def render_vip_guide_section(is_vip: bool, financials: dict[str, float | int | str], strategy_result: dict[str, object] | None) -> None:
    st.subheader(t("vip_guide_title"))
    st.caption(t("vip_guide_desc"))

    if not is_vip:
        render_note_card(t("guide_locked_title"), t("guide_locked_body"))
        return

    st.markdown(f"### {t('guide_library_title')}")
    app_bytes = load_pdf_bytes(str(GUIDE_PDF_APP_PATH))
    part_1_bytes = load_pdf_bytes(str(GUIDE_PDF_PART_1_PATH))
    part_2_bytes = load_pdf_bytes(str(GUIDE_PDF_PART_2_PATH))

    part_columns = st.columns(3)
    with part_columns[0]:
        st.markdown(f"**{t('guide_app_title')}**")
        if app_bytes:
            st.download_button(
                t("download_guide_pdf_app"),
                data=app_bytes,
                file_name="Onlyfans App Guide.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_guide_app",
            )
        else:
            st.warning(t("guide_app_missing_file"))

    with part_columns[1]:
        st.markdown(f"**{t('guide_part_1_title')}**")
        if part_1_bytes:
            st.download_button(
                t("download_guide_pdf_part_1"),
                data=part_1_bytes,
                file_name="OnlyFans Beginner's Guide - Part 1.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_guide_part_1",
            )
        else:
            st.warning(t("guide_part_1_missing_file"))

    with part_columns[2]:
        st.markdown(f"**{t('guide_part_2_title')}**")
        if part_2_bytes:
            st.download_button(
                t("download_guide_pdf_part_2"),
                data=part_2_bytes,
                file_name="OnlyFans Beginner's Guide - Part 2.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_guide_part_2",
            )
        else:
            st.warning(t("guide_part_2_missing_file"))

    if isinstance(strategy_result, dict):
        tracking_stats = {
            "revenue_growth": 0.0,
            "growth_percent": 0.0,
            "progress_percent": 0.0,
            "current_subscribers": float(st.session_state.get("tracking_current_subscribers", 0)),
            "current_revenue": float(st.session_state.get("tracking_current_revenue", 0.0)),
            "new_subscribers": float(st.session_state.get("tracking_subscriber_change", 0)),
        }
        render_strategy_export(financials, strategy_result, tracking_stats)


def render_dashboard_guide_library(is_vip: bool) -> None:
    st.markdown(f"### {t('dashboard_guides_title')}")
    app_bytes = load_pdf_bytes(str(GUIDE_PDF_APP_PATH))
    part_1_bytes = load_pdf_bytes(str(GUIDE_PDF_PART_1_PATH))
    part_2_bytes = load_pdf_bytes(str(GUIDE_PDF_PART_2_PATH))

    guide_cols = st.columns(3)
    with guide_cols[0]:
        render_guide_library_card(t("guide_app_title"), t("vip_guide_desc"))
        if is_vip and app_bytes:
            st.download_button(
                t("download_guide_pdf_app"),
                data=app_bytes,
                file_name="Onlyfans App Guide.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dashboard_guide_app",
            )
        elif not is_vip:
            st.warning(t("guide_locked_body"))
        else:
            st.warning(t("guide_app_missing_file"))

    with guide_cols[1]:
        render_guide_library_card(t("guide_part_1_title"), t("vip_guide_desc"))
        if is_vip and part_1_bytes:
            st.download_button(
                t("download_guide_pdf_part_1"),
                data=part_1_bytes,
                file_name="OnlyFans Beginner's Guide - Part 1.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dashboard_guide_part_1",
            )
        elif not is_vip:
            st.warning(t("guide_locked_body"))
        else:
            st.warning(t("guide_part_1_missing_file"))

    with guide_cols[2]:
        render_guide_library_card(t("guide_part_2_title"), t("vip_guide_desc"))
        if is_vip and part_2_bytes:
            st.download_button(
                t("download_guide_pdf_part_2"),
                data=part_2_bytes,
                file_name="OnlyFans Beginner's Guide - Part 2.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dashboard_guide_part_2",
            )
        elif not is_vip:
            st.warning(t("guide_locked_body"))
        else:
            st.warning(t("guide_part_2_missing_file"))


def build_dashboard_chart_dataframe(
    financials: dict[str, float | int | str],
    dashboard_snapshot: dict[str, float | int | str],
    metric_key: str,
) -> pd.DataFrame:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    factors = [0.58, 0.67, 0.64, 0.81, 0.75, 0.88, 1.0]

    if metric_key == "gross":
        base_value = float(financials.get("gross_income", 0.0))
    elif metric_key == "target":
        base_value = float(dashboard_snapshot.get("target_income", 0.0))
    else:
        base_value = float(financials.get("net_income", 0.0))

    divisor = 4 if base_value > 0 else 1
    values = [round((base_value * factor) / divisor, 2) for factor in factors]
    return pd.DataFrame({"Day": days, "Amount": values})


def render_membership_status_panel(current_email: str, is_vip: bool) -> None:
    membership = get_vip_membership_details(current_email)
    since_value = membership.get("started_at", "") or "-"
    expires_value = membership.get("expires_at", "") or "-"
    render_metric_card(
        t("dashboard_nav_membership"),
        t("dashboard_vip_badge") if is_vip else t("guide_locked_title"),
        t("dashboard_membership_tip"),
    )
    membership_cols = st.columns(2)
    with membership_cols[0]:
        render_metric_card(t("dashboard_membership_since"), since_value)
    with membership_cols[1]:
        render_metric_card(t("dashboard_membership_expires"), expires_value)


def render_dashboard_home(
    financials: dict[str, float | int | str],
    dashboard_snapshot: dict[str, float | int | str],
    current_focus_label: str,
    strategy_result: dict[str, object] | None,
) -> None:
    current_email = get_current_user_email()
    is_vip = bool(st.session_state.get("premium_unlocked", False))
    user_name = get_current_user_name() or "Girlpire Member"
    user_picture = get_user_claim("picture", "")

    header_cols = st.columns([8.5, 1.2, 1.2], gap="small")
    with header_cols[0]:
        st.markdown(
            f"""
            <div class="wolf-card" style="padding:0.95rem 1rem;">
                <div class="wolf-dashboard-brandbar">
                    {get_brand_symbol_html()}
                    <div class="wolf-dashboard-brand-meta">
                        <div class="wolf-dashboard-brand-title">{html.escape(t("brand"))}</div>
                        <div class="wolf-dashboard-brand-subtitle">{html.escape(t("dashboard_workspace"))}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        if st.button("🛒", key="dashboard_membership_toggle", use_container_width=True):
            st.session_state["dashboard_membership_open"] = not bool(
                st.session_state.get("dashboard_membership_open", False)
            )
    with header_cols[2]:
        st.markdown(
            f"""
            <div class="wolf-card" style="padding:0.85rem 0.9rem; text-align:center;">
                <div style="font-weight:800; color:var(--wolf-text);">{html.escape(t("dashboard_bell_label"))}</div>
                <div class="wolf-muted" style="font-size:0.8rem;">{html.escape(t("dashboard_vip_badge")) if is_vip else html.escape(t("guide_locked_title"))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.get("dashboard_membership_open", False):
        render_membership_status_panel(current_email, is_vip)

    main_col, side_col = st.columns([2.2, 1.0], gap="large")
    with main_col:
        stat_cols = st.columns(2)
        with stat_cols[0]:
            render_metric_card(
                "Total Finance",
                format_currency(float(financials.get("net_income", 0.0))),
                t("net_income"),
            )
        with stat_cols[1]:
            render_metric_card(
                "Target Income",
                format_currency(float(dashboard_snapshot.get("target_income", 0.0))),
                f"{t('gap_to_target')}: {format_currency(float(dashboard_snapshot.get('gap_value', 0.0)))}",
            )

        chart_cols = st.columns([1.55, 1.0], gap="large")
        with chart_cols[0]:
            st.markdown(f"### {t('mentor_analysis_title')}")
            metric_choice = st.radio(
                t("dashboard_chart_selector"),
                options=[
                    ("net", t("dashboard_chart_net")),
                    ("gross", t("dashboard_chart_gross")),
                    ("target", t("dashboard_chart_target")),
                ],
                format_func=lambda item: item[1],
                horizontal=True,
                key="dashboard_chart_metric_choice",
            )
            chart_df = build_dashboard_chart_dataframe(financials, dashboard_snapshot, metric_choice[0])
            st.line_chart(chart_df.set_index("Day"), use_container_width=True, height=280)

        with chart_cols[1]:
            render_metric_card(
                t("strategy_score"),
                f"{int(dashboard_snapshot.get('score', 0))}/100",
                str(dashboard_snapshot.get("status", t("status_average"))),
            )
            progress_ratio = clamp_percentage(
                (
                    (float(financials.get("net_income", 0.0)) / float(dashboard_snapshot.get("target_income", 0.0)))
                    * 100
                )
                if float(dashboard_snapshot.get("target_income", 0.0)) > 0
                else 0.0
            )
            st.progress(progress_ratio / 100 if progress_ratio > 0 else 0.0)
            render_note_card(t("focus_of_month"), current_focus_label)
            membership_preview = get_vip_membership_details(current_email)
            st.markdown(
                f"""
                <div class="wolf-card">
                    <div class="wolf-inline-title">{html.escape(t('dashboard_nav_membership'))}</div>
                    <p class="wolf-muted"><strong>{html.escape(t('dashboard_membership_since'))}:</strong> {html.escape(membership_preview.get('started_at', '-'))}</p>
                    <p class="wolf-muted"><strong>{html.escape(t('dashboard_membership_expires'))}:</strong> {html.escape(membership_preview.get('expires_at', '-'))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_dashboard_guide_library(is_vip)

        if isinstance(strategy_result, dict):
            render_structured_strategy(strategy_result)
        else:
            render_note_card(t("strategy_consultant"), t("strategy_generate_hint"))

    with side_col:
        avatar_html = (
            f'<img class="wolf-dashboard-profile-avatar-img" src="{html.escape(user_picture, quote=True)}" alt="{html.escape(user_name)}" />'
            if user_picture
            else f'<div class="wolf-dashboard-profile-avatar">{html.escape("".join(part[:1] for part in user_name.split()[:2]).upper() or "GP")}</div>'
        )
        st.markdown(
            f"""
            <div class="wolf-card">
                <div class="wolf-dashboard-profile-top">
                    {avatar_html}
                    <div class="wolf-dashboard-profile-name">{html.escape(user_name)}</div>
                    <div class="wolf-dashboard-profile-role">{html.escape(t('vip_title'))}</div>
                </div>
                <div class="wolf-vip-sidebar-chip" style="margin-top:0.75rem;">{html.escape(t('dashboard_vip_badge'))}</div>
                <div class="wolf-vip-sidebar-chip" style="margin-top:0.45rem;">{html.escape(current_focus_label)}</div>
                <div style="height:0.8rem;"></div>
                <div class="wolf-inline-title">{html.escape(t('dashboard_nav_membership'))}</div>
                <p class="wolf-muted">{html.escape(t('dashboard_membership_tip'))}</p>
                <p class="wolf-muted"><strong>{html.escape(t('dashboard_membership_since'))}:</strong> {html.escape(get_vip_membership_details(current_email).get('started_at', '-'))}</p>
                <p class="wolf-muted"><strong>{html.escape(t('dashboard_membership_expires'))}:</strong> {html.escape(get_vip_membership_details(current_email).get('expires_at', '-'))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_vip_area(financials: dict[str, float | int | str]) -> None:
    if is_upgrade_flow():
        st.markdown('<div id="vip-section"></div>', unsafe_allow_html=True)
        render_note_card(t("upgrade_flow_title"), t("upgrade_paid_prompt"))
    elif is_from_email():
        st.markdown('<div id="vip-section"></div>', unsafe_allow_html=True)
        render_note_card(t("email_welcome_title"), t("email_paid_prompt"))

    current_email = get_current_user_email()
    current_profile = build_current_vip_profile(financials)
    stored_strategy = st.session_state.get("strategy_result")
    if not isinstance(stored_strategy, dict) or "current_net_income" not in stored_strategy:
        stored_strategy = None
        st.session_state["strategy_result"] = None
    base_result = st.session_state.get("money_engine_result")
    has_live_money_data = isinstance(base_result, dict)
    shell_financials = financials
    shell_snapshot = build_dashboard_snapshot(financials, current_profile, stored_strategy)
    if not has_live_money_data:
        shell_financials = calculate_financials(0, 0.0, 0.0)
        shell_snapshot = {
            "current_net_income": 0.0,
            "target_income": 0.0,
            "gap_value": 0.0,
            "score": 0,
            "status": str(t("status_average")),
            "explanation": str(t("vip_desc")),
        }
    dashboard_snapshot = build_dashboard_snapshot(financials, current_profile, stored_strategy)
    current_focus_label = (
        str(stored_strategy.get("focus_of_month", ""))
        if stored_strategy
        else get_focus_of_month(float(financials["net_income"]))
    )
    if not has_live_money_data:
        current_focus_label = t("vip_nav_dashboard")
    selected_section = sync_vip_section_from_query_params()
    reengagement_message = get_reengagement_message()
    strategy_result = stored_strategy

    left_col, right_col = st.columns([1.05, 3.95], gap="large")
    with left_col:
        render_vip_navigation_panel(selected_section, current_focus_label)

    with right_col:
        st.markdown('<div id="vip-content"></div>', unsafe_allow_html=True)
        if selected_section == "dashboard":
            render_dashboard_home(
                shell_financials,
                shell_snapshot,
                current_focus_label,
                strategy_result if isinstance(strategy_result, dict) else None,
            )

        if selected_section == "strategy":
            if reengagement_message:
                render_note_card(t("monthly_strategy_cycle_title"), reengagement_message)
            strategy_result = render_monthly_cycle_section(financials, stored_strategy)
            if isinstance(strategy_result, dict):
                st.session_state["strategy_result"] = strategy_result
                stored_strategy = strategy_result
                dashboard_snapshot = build_dashboard_snapshot(financials, current_profile, stored_strategy)
                current_focus_label = str(strategy_result.get("focus_of_month", current_focus_label))

            experience_options = {
                "beginner": t("beginner"),
                "intermediate": t("intermediate"),
                "advanced": t("advanced"),
            }
            challenge_options = {
                "traffic": t("traffic"),
                "conversion": t("conversion"),
                "pricing": t("pricing"),
                "retention": t("retention"),
                "consistency": t("consistency"),
            }

            with st.form("vip_strategy_form"):
                st.markdown(f"### {t('strategy_consultant')}")
                left, right = st.columns(2)
                with left:
                    st.number_input(
                        t("daily_time"),
                        min_value=0.5,
                        value=float(current_profile["daily_time"]),
                        step=0.5,
                        key="vip_daily_time",
                    )
                    st.number_input(
                        t("target_income"),
                        min_value=0.0,
                        value=float(current_profile["target_income"]),
                        step=100.0,
                        key="vip_target_income",
                    )
                with right:
                    st.selectbox(
                        t("experience_level"),
                        options=list(experience_options.keys()),
                        index=list(experience_options.keys()).index(str(current_profile["experience_level_code"])),
                        format_func=lambda key: experience_options[key],
                        key="vip_experience_level",
                    )
                    st.selectbox(
                        t("main_challenge"),
                        options=list(challenge_options.keys()),
                        index=list(challenge_options.keys()).index(str(current_profile["main_challenge"])),
                        format_func=lambda key: challenge_options[key],
                        key="vip_main_challenge",
                    )

                submitted = st.form_submit_button(t("generate_strategy"), use_container_width=True)

            if submitted:
                strategy_result = refresh_monthly_strategy(financials)
                stored_strategy = strategy_result
                st.session_state["strategy_result"] = strategy_result
                dashboard_snapshot = build_dashboard_snapshot(financials, current_profile, stored_strategy)
                current_focus_label = str(strategy_result.get("focus_of_month", current_focus_label))
                st.rerun()

            render_quick_strategy_engine(True)

            strategy_result = st.session_state.get("strategy_result")
            if strategy_result:
                dashboard_snapshot = build_dashboard_snapshot(financials, current_profile, strategy_result)
                current_focus_label = str(strategy_result.get("focus_of_month", current_focus_label))

        tracking_target = (
            float(strategy_result["target_income"])
            if isinstance(strategy_result, dict)
            else float(current_profile["target_income"])
        )
        tracking_score = (
            int(strategy_result["score"])
            if isinstance(strategy_result, dict)
            else int(dashboard_snapshot["score"])
        )
        tracking_focus = (
            str(strategy_result.get("growth_focus_key", "conversion"))
            if isinstance(strategy_result, dict)
            else determine_growth_focus(financials, current_profile)
        )

        if selected_section == "dashboard":
            render_admin_panel(current_email, show_wrapper=False)

        elif selected_section == "calculator":
            calculator_result = render_vip_calculator_section()
            if isinstance(calculator_result, dict):
                financials = calculator_result

        elif selected_section == "strategy":
            render_strategy_dashboard(dashboard_snapshot)
            if strategy_result:
                render_structured_strategy(strategy_result)
            else:
                render_note_card(t("strategy_consultant"), t("strategy_generate_hint"))
            render_strategy_history(strategy_result if isinstance(strategy_result, dict) else None)

        elif selected_section == "tracking":
            render_tracking_system(
                tracking_target,
                tracking_score,
                tracking_focus,
            )
            render_strategy_history(strategy_result if isinstance(strategy_result, dict) else None)

        elif selected_section == "scenarios":
            st.subheader(t("vip_nav_scenarios"))
            scenario_columns = st.columns(3)
            scenarios = build_scenarios(
                int(st.session_state.get("follower_count", 0)),
                float(st.session_state.get("monthly_sub_price", 0.0)),
                float(st.session_state.get("expected_tips_ppv", 0.0)),
            )
            for index, (scenario_name, scenario_financials) in enumerate(scenarios.items()):
                with scenario_columns[index]:
                    render_metric_card(
                        scenario_name,
                        format_currency(scenario_financials["net_income"]),
                        f"{t('gross_income')}: {format_currency(scenario_financials['gross_income'])}",
                    )

        elif selected_section == "guide":
            render_vip_guide_section(
                bool(st.session_state.get("premium_unlocked", False)),
                financials,
                strategy_result if isinstance(strategy_result, dict) else None,
            )

        elif selected_section == "advanced":
            st.subheader(t("advanced_metrics"))
            score_value = 0
            score_status = t("status_average")
            if isinstance(strategy_result, dict):
                score_value = int(strategy_result.get("score", 0))
                score_status = str(strategy_result.get("status", score_status))
            else:
                score_value = int(dashboard_snapshot["score"])
                score_status = str(dashboard_snapshot["status"])

            advanced_row = st.columns(2)
            with advanced_row[0]:
                render_metric_card(
                    t("strategy_score"),
                    f"{score_value}/100",
                    score_status,
                )
            with advanced_row[1]:
                render_metric_card(
                    t("profit_breakdown"),
                    format_currency(float(financials["net_income"])),
                    f"{t('gross_income')}: {format_currency(float(financials['gross_income']))}",
                )


def render_footer() -> None:
    st.markdown(
        f'<div class="wolf-footer">{html.escape(t("footer"))}</div>',
        unsafe_allow_html=True,
    )


def render_admin_panel(user_email: str, show_wrapper: bool = True) -> None:
    if not is_admin_user(user_email):
        return

    admin_email = get_admin_email()
    email_store = prune_expired_paid_users(ensure_email_store())
    users = list(email_store.get("users", []))
    paid_users = list(email_store.get("paid_users", []))
    vip_records = build_vip_member_records(users, paid_users)
    today_date = datetime.now().date()
    new_users: list[dict[str, str]] = []
    for user_record in users:
        created_at = str(user_record.get("created_at", "")).strip()
        try:
            created_date = datetime.fromisoformat(created_at).date()
        except ValueError:
            continue
        days_since_created = (today_date - created_date).days
        if 0 <= days_since_created <= 7:
            new_users.append(user_record)

    if show_wrapper:
        st.markdown("---")
    st.subheader("Girlpire Admin")

    stat_columns = st.columns(2)
    with stat_columns[0]:
        st.metric(t("total_users_metric"), len(users))
    with stat_columns[1]:
        st.metric(t("vip_users_metric"), len(paid_users))

    download_columns = st.columns(2)
    with download_columns[0]:
        st.download_button(
            t("download_all_users"),
            data=build_members_csv(users),
            file_name="girlpire_all_members.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_columns[1]:
        st.download_button(
            t("download_vip_users"),
            data=build_members_csv(vip_records),
            file_name="girlpire_vip_members.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.subheader(t("all_users_title"))
    if users:
        st.dataframe(build_admin_member_rows(users), use_container_width=True, hide_index=True)
    else:
        st.caption(t("no_users_saved"))

    st.subheader(t("new_users_title"))
    if new_users:
        st.dataframe(build_admin_member_rows(new_users), use_container_width=True, hide_index=True)
    else:
        st.caption(t("no_new_users"))

    st.subheader(t("vip_users_title"))
    if vip_records:
        st.dataframe(build_admin_member_rows(vip_records), use_container_width=True, hide_index=True)
    else:
        st.caption(t("no_vip_users"))

    st.subheader(t("grant_vip_title"))
    st.caption(t("grant_vip_desc"))
    with st.form("grant_vip_membership_form"):
        grant_columns = st.columns(2)
        with grant_columns[0]:
            vip_email_input = st.text_input(t("grant_vip_email"))
        with grant_columns[1]:
            vip_name_input = st.text_input(t("grant_vip_name"))
        grant_submitted = st.form_submit_button(
            t("grant_vip_button"),
            use_container_width=True,
        )
    if grant_submitted:
        normalized_grant_email = str(vip_email_input or "").strip().lower()
        if grant_vip_membership(normalized_grant_email, vip_name_input, days=30):
            if normalized_grant_email == str(user_email or "").strip().lower():
                st.session_state["premium_unlocked"] = True
            st.success(t("grant_vip_success").format(email=normalized_grant_email))
            st.rerun()
        st.error(t("grant_vip_failed"))

    if st.button("Send Test Email"):
        try:
            success, message = send_email(
                admin_email,
                "Girlpire Test",
                "<p>Admin panel çalışıyor</p>",
            )
            if success:
                st.success("Email gönderildi!")
            else:
                st.error(message)
        except Exception as e:
            st.error(f"Hata: {e}")

    if st.button(t("add_myself_vip"), use_container_width=True):
        if add_paid_user(user_email, get_current_user_name()):
            st.session_state["premium_unlocked"] = True
            st.success(t("vip_add_success"))
            st.rerun()
        else:
            st.error("VIP access could not be updated.")

    if st.button("Send To All Users"):
        try:
            send_to_all_users()
            st.success("Emails sent")
        except Exception as e:
            st.error(f"Hata: {e}")


def main() -> None:
    init_state()
    sync_language_from_query_params()
    detect_email_traffic()
    render_styles()
    if not google_login_ready():
        st.warning(
            "Google login not configured. Paste your Client ID and Secret into .streamlit/secrets.toml"
        )
        st.stop()

    try:
        logged_in = st.user.is_logged_in
    except Exception:
        logged_in = False

    if not logged_in:
        render_google_login_screen()
        st.stop()

    current_email = get_current_user_email()
    current_name = get_current_user_name()
    save_user_email(current_email, current_name)
    paid_users = load_paid_users()
    is_paid = current_email in paid_users
    st.session_state["premium_unlocked"] = is_paid or check_subscription_status(current_email)

    if st.session_state["premium_unlocked"]:
        financials = (
            st.session_state.get("money_engine_result")
            if isinstance(st.session_state.get("money_engine_result"), dict)
            else None
        )
        render_vip_area(
            financials or calculate_financials(
                int(st.session_state.get("follower_count", 0)),
                float(st.session_state.get("monthly_sub_price", 0.0)),
                float(st.session_state.get("expected_tips_ppv", 0.0)),
            )
        )
    else:
        render_header()
        render_logged_in_status()
        render_email_return_banner(
            logged_in,
            bool(st.session_state.get("premium_unlocked", False)),
            current_email,
        )
        financials = render_free_calculator()
        render_quick_strategy_engine(False)
        if financials:
            render_cta_section(financials)
        st.warning(t("vip_upgrade_message"))
        render_paywall(current_email)
        requested_section = str(getattr(st, "query_params", {}).get("vip_section", "") or "").strip().lower()
        if requested_section == "guide":
            render_note_card(t("guide_locked_title"), t("guide_locked_body"))

    render_footer()

try:
    main()
except Exception as exc:
    st.error("Application error")
    st.exception(exc)
    st.code(traceback.format_exc())
