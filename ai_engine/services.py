"""
AI Services Module - Core AI functionality using Groq API and LangChain.
Handles scam analysis, OCR processing, price verification, and AI assistant.
"""
import json
import time
import os
import re
import logging
# pyrefly: ignore [missing-import]
from django.conf import settings

logger = logging.getLogger(__name__)


def get_groq_client():
    """Initialize Groq client."""
    try:
        # pyrefly: ignore [missing-import]
        from groq import Groq
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return None
        return Groq(api_key=api_key)
    except ImportError:
        logger.warning("Groq package not installed")
        return None


def get_langchain_llm():
    """Initialize LangChain with Groq."""
    try:
        # pyrefly: ignore [missing-import]
        from langchain_groq import ChatGroq
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return None
        return ChatGroq(
            groq_api_key=api_key,
            model_name=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
            temperature=getattr(settings, 'AI_TEMPERATURE', 0.3),
            max_tokens=getattr(settings, 'AI_MAX_TOKENS', 2048),
        )
    except ImportError:
        logger.warning("LangChain Groq package not installed")
        return None


def analyze_scam_report(report):
    """Analyze a scam report using AI."""
    # pyrefly: ignore [missing-import]
    from scams.models import AIAnalysis

    start_time = time.time()
    client = get_groq_client()

    if not client:
        # Provide a fallback analysis
        _fallback_scam_analysis(report)
        return

    prompt = f"""You are an AI tourist safety expert. Analyze this scam report and provide a detailed assessment.

Report Details:
- Title: {report.title}
- Category: {report.get_category_display()}
- Description: {report.description}
- Location: {report.location_name}
- Charged Amount: {report.charged_amount} {report.currency}
- Expected Amount: {report.expected_amount} {report.currency}
- Incident Date: {report.incident_date}

Analyze and respond in this exact JSON format:
{{
    "scam_probability": <float 0-100>,
    "risk_score": <float 0-10>,
    "classification": "<specific scam type>",
    "summary": "<detailed 2-3 sentence analysis>",
    "fair_price_estimate": "<estimated fair price or null>",
    "warning_signs": ["<sign1>", "<sign2>"],
    "recommendations": ["<rec1>", "<rec2>"],
    "severity": "<low|medium|high|critical>"
}}"""

    try:
        response = client.chat.completions.create(
            model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
            messages=[
                {"role": "system", "content": "You are a tourist safety AI expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )

        result_text = response.choices[0].message.content.strip()
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)

        # Update report
        report.scam_probability = float(result.get('scam_probability', 50))
        report.ai_risk_score = float(result.get('risk_score', 5))
        report.ai_classification = result.get('classification', report.get_category_display())
        report.ai_summary = result.get('summary', '')
        report.is_ai_analyzed = True
        if result.get('severity'):
            report.severity = result['severity']
        report.save()

        # Save AI Analysis record
        processing_time = time.time() - start_time
        AIAnalysis.objects.create(
            report=report,
            analysis_type='scam_detection',
            input_data=prompt,
            output_data=json.dumps(result),
            confidence=report.scam_probability / 100,
            processing_time=processing_time,
        )

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        _fallback_scam_analysis(report)


def _fallback_scam_analysis(report):
    """Provide rule-based fallback analysis when AI is unavailable."""
    probability = 50.0
    risk_score = 5.0

    if report.charged_amount and report.expected_amount:
        if report.expected_amount > 0:
            ratio = float(report.charged_amount) / float(report.expected_amount)
            if ratio > 5:
                probability = 95.0
                risk_score = 9.5
            elif ratio > 3:
                probability = 85.0
                risk_score = 8.0
            elif ratio > 2:
                probability = 70.0
                risk_score = 7.0
            elif ratio > 1.5:
                probability = 55.0
                risk_score = 5.5
            else:
                probability = 30.0
                risk_score = 3.0

    high_risk_categories = ['taxi', 'currency', 'tour_guide']
    if report.category in high_risk_categories:
        probability = min(100, probability + 10)
        risk_score = min(10, risk_score + 1)

    report.scam_probability = probability
    report.ai_risk_score = risk_score
    report.ai_classification = report.get_category_display()
    report.ai_summary = f"Automated analysis: This {report.get_category_display()} report has a {probability:.0f}% scam probability based on price analysis and category risk assessment."
    report.is_ai_analyzed = True
    report.save()


def _build_bill_system_prompt():
    """Build a precise system prompt that prevents false positives."""
    return """You are a highly intelligent, nuanced tourist scam detection engine. Your primary job is to detect OVERCHARGING and TOURIST EXPLOITATION, independent of whether the bill is mathematically correct or authentic.

CRITICAL RULES — READ CAREFULLY:

1. AUTHENTICITY ≠ FAIRNESS: A bill can be 100% authentic, mathematically correct, and from a real business, but STILL be a scam if the prices are exploitative. Do not assume a bill is "Safe" just because it looks real.

2. ITEM-LEVEL PRICING ANALYSIS & MICRO-SURCHARGES (Crucial):
   - You MUST extract and analyze every single item individually.
   - You MUST actively look for unusual micro-surcharges such as: "Gas fee", "Cooking charge", "Convenience fee", "Packaging fee", "Table fee", or hidden "Service charges".
   - Understand that businesses usually include operational costs inside item pricing. Adding separate operational charges (like a cooking fee) is often an unfair practice.
   - Even if the bill total is very small, a suspicious hidden fee MUST be flagged. Do not ignore unfair charges just because the total amount is low.
   - Flag excessive luxury markups and unusually expensive basics.

3. SCAM PROBABILITY GUIDELINES (Nuanced Assessment):
   - 0-15%: Fair pricing, aligns perfectly with local economic standards and venue type.
   - 15-35%: Tourist Area Pricing / Slightly Expensive. Noticeable premium markup.
   - 35-65%: Suspicious Pricing. Exploitatively high prices, duplicate items, or excessive service fees.
   - 65-100%: Severe Overcharging / Scam. Extreme markups (e.g., 2x+ local averages), fake taxes.

4. FAIR PRICE ESTIMATION (CRITICAL: DO NOT JUST COPY THE TOTAL):
   - You MUST calculate what a REALISTIC, FAIR expected total would be.
   - If the bill is overpriced, your `fair_price_estimate` MUST BE LOWER than the billed total.
   - DO NOT echo the OCR total unless you are 100% certain the pricing is perfectly fair.
   - If you detect a 50% overcharge, your fair_price_estimate should be roughly 33% lower than the total.

5. SERVICE CHARGES & TAXES:
   - Identify unusual taxes or stacked service fees.
   - If service charges exceed standard regional norms (e.g. >10-15%), significantly increase scam_probability.

6. ANALYSIS NOTES (Reasoning):
   - Explain WHY the bill seems overpriced (or fair).
   - List WHICH items triggered suspicion.
   - Describe HOW far pricing deviates from expected norms.
   - NEVER use generic phrases like "Bill is mathematically correct" or "OCR succeeded". Focus entirely on PRICING FAIRNESS.

Respond with valid JSON only."""


def _validate_and_correct_analysis(analysis_result, bill):
    """Post-process AI output to catch and fix unrealistic values."""

    def safe_float(val, default):
        try:
            if val is None:
                return default
            return float(val)
        except (ValueError, TypeError):
            return default

    total_amount = safe_float(bill.total_amount, None)
    scam_prob = safe_float(analysis_result.get('scam_probability', 5), 5)
    fair_est = safe_float(analysis_result.get('fair_price_estimate'), None)
    confidence = safe_float(analysis_result.get('confidence_score', 0.75), 0.75)
    items = analysis_result.get('items_detected', [])
    suspicious = analysis_result.get('suspicious_charges', [])
    if not isinstance(suspicious, list):
        suspicious = []

    # --- Deterministic Rule Engine for Hidden Fees ---
    suspicious_keywords = [
        "gas", "cooking", "table charge", "service fee", "service charge", 
        "convenience", "operational", "packaging", "misc fee", "kitchen", 
        "handling", "maintenance"
    ]
    rule_penalty = 0

    if items and isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).lower()
            
            is_suspicious = any(kw in name for kw in suspicious_keywords)
            
            if is_suspicious:
                item["risk_level"] = "suspicious"
                if item.get("category") in [None, "unknown", "food", "beverage"]:
                    item["category"] = "operational_fee"
                
                # Check if it was already flagged
                already_flagged = any(name in str(s).lower() for s in suspicious)
                if not already_flagged:
                    suspicious.append(f"{item.get('name')} -> Hidden operational surcharge detected.")
                    # AI missed it, lower confidence
                    confidence -= 0.05
                
                if "tax" in name:
                    rule_penalty += 12
                elif "service" in name:
                    rule_penalty += 18
                else:
                    rule_penalty += 15

    analysis_result['items_detected'] = items
    analysis_result['suspicious_charges'] = suspicious

    # --- Fix 1: Validate fair_price_estimate ---
    if total_amount and total_amount > 0:
        if fair_est is not None and fair_est > 0:
            ratio = fair_est / float(total_amount)
            # Only reset if the AI hallucinates an impossibly low estimate (< 10% of total)
            if ratio < 0.1:
                fair_est = float(total_amount)
                analysis_result['fair_price_estimate'] = fair_est
            
            # If AI says it's overpriced but still returns fair_est == total, FORCE a reduction
            if scam_prob > 25 and ratio > 0.95:
                fair_est = float(total_amount) / (1.0 + (scam_prob / 100.0))
                analysis_result['fair_price_estimate'] = round(fair_est, 2)
        else:
            # If AI left it null, calculate it based on scam_probability
            if scam_prob > 15:
                fair_est = float(total_amount) / (1.0 + (scam_prob / 100.0))
            else:
                fair_est = float(total_amount)
            analysis_result['fair_price_estimate'] = round(fair_est, 2)

    # --- Fix 2: Calculate evidence-based scam probability ---
    evidence_score = 0

    if total_amount and fair_est and total_amount > 0 and fair_est > 0:
        overcharge_ratio = float(total_amount) / float(fair_est)
        if overcharge_ratio <= 1.05:
            evidence_score += 0  # Normal pricing
        elif overcharge_ratio <= 1.15:
            evidence_score += 15  # Slight markup
        elif overcharge_ratio <= 1.35:
            evidence_score += 40  # Noticeable overcharge / Tourist pricing
        elif overcharge_ratio <= 1.75:
            evidence_score += 70  # Suspiciously high
        else:
            evidence_score += 90  # Extreme overcharge

    if isinstance(suspicious, list):
        suspicious_score = min(len(suspicious) * 15, 45)
        evidence_score += suspicious_score
        
        # Add hard penalties from the deterministic rule engine
        evidence_score += rule_penalty
        
        # If there are suspicious charges (like micro-surcharges), we must guarantee a minimum 
        # risk level to reflect the concern, even if the total math isn't hugely inflated.
        if len(suspicious) > 0:
            evidence_score = max(evidence_score, 25)

    # Blend AI probability with our strict mathematical evidence score
    blended_prob = max(scam_prob, evidence_score)
    
    # Do NOT clamp down. If the bill is mathematically authentic but overpriced, it stays high.
    scam_prob = max(0, min(100, round(blended_prob, 1)))
    analysis_result['scam_probability'] = scam_prob

    # --- Fix 3: Confidence floor & realistic bounds ---
    # Don't return very low confidence for bills that were successfully parsed
    if items and len(items) > 0:
        confidence = max(confidence, 0.7)
    
    # User requested fix: NEVER 100% confidence. Range 55% to 92%
    if confidence >= 0.95:
        # Add realistic fuzziness based on total to avoid identical fake values
        fuzz = (hash(str(total_amount)) % 10) / 100.0
        confidence = 0.85 + fuzz
    
    confidence = max(0.55, min(0.94, confidence))
    
    # Store as percentage (0-100) for display
    analysis_result['confidence_score'] = round(confidence * 100, 1)

    # --- Fix 4: Clean suspicious charges ---
    # Remove vague/generic suspicious charge descriptions
    vague_terms = ['general', 'various', 'miscellaneous', 'unknown', 'n/a', 'none']
    if isinstance(suspicious, list):
        cleaned = [
            s for s in suspicious
            if isinstance(s, str) and len(s.strip()) > 5
            and not any(v in s.lower() for v in vague_terms)
        ]
        analysis_result['suspicious_charges'] = cleaned

    return analysis_result, safe_float


def _generate_realistic_summary(analysis_result, bill, safe_float):
    """Generate an honest, bill-specific analysis summary."""
    bill_type = bill.get_bill_type_display()
    location = bill.location_name or 'the specified vendor'
    total = bill.total_amount or 'N/A'
    currency = bill.currency
    scam_prob = safe_float(analysis_result.get('scam_probability', 5), 5)
    fair_est = analysis_result.get('fair_price_estimate')
    items = analysis_result.get('items_detected', [])
    suspicious = analysis_result.get('suspicious_charges', [])

    parts = []

    # Opening — what the bill is
    item_count = len(items) if items else 0
    if item_count > 0:
        parts.append(f"This {bill_type.lower()} from {location} contains {item_count} item(s) totaling {currency} {total}.")
    else:
        parts.append(f"This {bill_type.lower()} from {location} shows a total of {currency} {total}.")

    # Price assessment
    if total != 'N/A' and fair_est:
        total_f = safe_float(total, 0)
        fair_f = safe_float(fair_est, 0)
        if fair_f > 0 and total_f > 0:
            diff_pct = abs(total_f - fair_f) / fair_f * 100
            if diff_pct < 5:
                parts.append("The pricing appears consistent with expected market rates for this type of purchase.")
            elif diff_pct < 20:
                parts.append(f"The pricing is slightly above typical rates (approximately {diff_pct:.0f}% difference), which may reflect location-based markup or premium products.")
            elif diff_pct < 50:
                parts.append(f"The total appears to be around {diff_pct:.0f}% above typical market rates, which warrants attention.")
            else:
                parts.append(f"The total is significantly above expected rates by approximately {diff_pct:.0f}%. This level of overcharging is a concern.")

    # Risk verdict
    if scam_prob <= 10:
        parts.append("Overall, this bill appears normal and fairly priced. No action needed.")
    elif scam_prob <= 25:
        if suspicious and len(suspicious) > 0:
            parts.append("The pricing is generally standard, but we detected an unusual or hidden surcharge. While the monetary impact is low, this may be an unfair operational fee.")
        else:
            parts.append("The bill shows minor variations from expected pricing but nothing that suggests deliberate overcharging.")
    elif scam_prob <= 50:
        parts.append("Some charges on this bill appear higher than expected. Consider verifying prices for the flagged items.")
    elif scam_prob <= 75:
        parts.append("Multiple pricing concerns were identified. We recommend comparing these charges with other local vendors before paying.")
    else:
        parts.append("This bill shows strong indicators of overcharging. We recommend disputing the charges or seeking a second opinion.")

    # Suspicious items mention
    if suspicious and len(suspicious) > 0:
        parts.append(f"Flagged concern(s): {'; '.join(str(s) for s in suspicious[:3])}.")

    return ' '.join(parts)


def analyze_bill(bill):
    """Analyze an uploaded bill using Vision AI + OCR fallback."""
    # pyrefly: ignore [missing-import]
    from scams.models import OCRResult, AIAnalysis
    start_time = time.time()

    client = get_groq_client()

    # Default to LOW risk — innocent until proven guilty
    analysis_result = {
        'items_detected': [],
        'total_detected': None,
        'taxes_detected': [],
        'suspicious_charges': [],
        'confidence_score': 75,
        'fair_price_estimate': None,
        'scam_probability': 5.0,
        'analysis_notes': '',
    }

    extracted_text = ""
    vision_success = False
    system_prompt = _build_bill_system_prompt()

    # === RAG Context Retrieval ===
    rag_context = ""
    try:
        from rag_engine.services import get_rag_context
        query = f"{bill.get_bill_type_display()} items"
        city = bill.location_name if bill.location_name else None
        rag_context = get_rag_context(query=query, city=city, top_k=3)
    except Exception as e:
        logger.warning(f"RAG retrieval failed for bill analysis: {e}")

    rag_section = ""
    if rag_context:
        rag_section = f"\n\n=== RETRIEVED PRICING INTELLIGENCE ===\nUse this context to verify if the billed items are priced fairly based on local market rates:\n{rag_context}\n====================================\n"

    # Step 1: Try vision-based analysis
    if client and bill.image:
        try:
            import base64
            image_path = bill.image.path
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode('utf-8')

                ext = os.path.splitext(image_path)[1].lower()
                mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
                mime = mime_map.get(ext, 'image/jpeg')

                vision_prompt = f"""Analyze this bill/receipt image item-by-item. Extract all text, identify the venue context, and perform a REAL CONTEXTUAL PRICING ANALYSIS.

Bill Type: {bill.get_bill_type_display()}
Location/Vendor: {bill.location_name or 'Unknown'}
Stated Total: {bill.total_amount} {bill.currency}
{rag_section}
IMPORTANT: 
- Do NOT assume the bill is "Safe" just because it is mathematically correct or authentic.
- Evaluate EVERY item for pricing fairness based on the region and venue type.
- Do NOT copy the stated total as the fair_price_estimate unless you genuinely believe the prices are 100% fair. Estimate a true realistic total based on local market averages.

Respond ONLY with this JSON:
{{
    "extracted_text": "<all visible text on the bill>",
    "items_detected": [{{"name": "<item>", "price": <amount>, "category": "<food|beverage|tax|service|operational_fee|discount|surcharge|unknown>", "risk_level": "<safe|suspicious>"}}],
    "total_detected": <total from the bill or null>,
    "taxes_detected": [{{"type": "<tax name/service charge>", "amount": <amount>}}, ...],
    "suspicious_charges": ["<specific suspicious charge if any>"],
    "confidence_score": <float 0.55-0.92, NEVER 1.0>,
    "fair_price_estimate": <MUST BE LOWER THAN TOTAL if overpricing is detected. DO NOT blindly copy the total>,
    "scam_probability": <float 0-100, nuanced based on item analysis and markups>,
    "analysis_notes": "<3-5 sentence detailed reasoning. Explain WHICH items are overpriced, WHY it deviates from regional averages, and WHAT the venue context is. Be highly realistic.>"
}}"""

                response = client.chat.completions.create(
                    model='llama-3.2-90b-vision-preview',
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [
                            {"type": "text", "text": vision_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
                        ]}
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                )

                result_text = response.choices[0].message.content.strip()
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    analysis_result = json.loads(result_text)

                extracted_text = analysis_result.pop('extracted_text', '')
                vision_success = True
                logger.info("Vision-based bill analysis succeeded")

        except Exception as e:
            logger.warning(f"Vision analysis failed, falling back to OCR: {e}")

    # Step 2: Fall back to OCR + text-based analysis
    if not vision_success:
        extracted_text = extract_text_from_image(bill.image.path if bill.image else None)

        if client and extracted_text and not extracted_text.startswith('['):
            prompt = f"""Analyze this bill/receipt text item-by-item and perform a REAL CONTEXTUAL PRICING ANALYSIS.

Bill Type: {bill.get_bill_type_display()}
Location/Vendor: {bill.location_name or 'Unknown'}
Stated Total: {bill.total_amount} {bill.currency}

Extracted Text:
{extracted_text}
{rag_section}
IMPORTANT: 
- Do NOT assume the bill is "Safe" just because it is mathematically correct.
- Evaluate EVERY item for pricing fairness based on the region and venue type.
- Estimate a true realistic total based on local market averages. DO NOT echo the stated total if it is overpriced.

Respond ONLY with JSON:
{{
    "items_detected": [{{"name": "<item>", "price": <amount>, "category": "<food|beverage|tax|service|operational_fee|discount|surcharge|unknown>", "risk_level": "<safe|suspicious>"}}],
    "total_detected": <total or null>,
    "taxes_detected": [{{"type": "<tax name/service charge>", "amount": <amount>}}, ...],
    "suspicious_charges": ["<specific suspicious charge if any>"],
    "confidence_score": <float 0.55-0.92, NEVER 1.0>,
    "fair_price_estimate": <MUST BE LOWER THAN TOTAL if overpricing is detected. DO NOT blindly copy the total>,
    "scam_probability": <float 0-100, nuanced based on item analysis and markups>,
    "analysis_notes": "<3-5 sentence detailed reasoning. Explain WHICH items are overpriced, WHY it deviates from regional averages, and WHAT the venue context is. Be highly realistic.>"
}}"""

            try:
                response = client.chat.completions.create(
                    model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500,
                )
                result_text = response.choices[0].message.content.strip()
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    analysis_result = json.loads(result_text)
            except Exception as e:
                logger.error(f"Bill AI analysis failed: {e}")

    # Step 3: Post-process and validate AI output
    analysis_result, safe_float = _validate_and_correct_analysis(analysis_result, bill)

    # Step 4: Generate realistic summary if missing
    notes = str(analysis_result.get('analysis_notes', '')).strip()
    if not notes or len(notes) < 20:
        analysis_result['analysis_notes'] = _generate_realistic_summary(
            analysis_result, bill, safe_float
        )

    # Step 5: Save results
    try:
        ocr_result, _ = OCRResult.objects.update_or_create(
            bill=bill,
            defaults={
                'extracted_text': extracted_text or 'Text extracted via AI vision analysis.',
                'items_detected': analysis_result.get('items_detected', []),
                'total_detected': safe_float(analysis_result.get('total_detected'), None),
                'taxes_detected': analysis_result.get('taxes_detected', []),
                'suspicious_charges': analysis_result.get('suspicious_charges', []),
                'confidence_score': safe_float(analysis_result.get('confidence_score', 75), 75),
                'fair_price_estimate': safe_float(analysis_result.get('fair_price_estimate'), None),
                'scam_probability': safe_float(analysis_result.get('scam_probability', 5), 5.0),
                'analysis_notes': str(analysis_result.get('analysis_notes', '')),
            }
        )

        bill.is_analyzed = True
        bill.save()

        processing_time = time.time() - start_time
        # pyrefly: ignore [missing-import]
        from scams.models import AIAnalysis
        AIAnalysis.objects.create(
            bill=bill,
            analysis_type='bill_analysis',
            input_data=extracted_text or 'Vision-based analysis',
            output_data=json.dumps(analysis_result, default=str),
            confidence=safe_float(analysis_result.get('confidence_score', 75), 75) / 100,
            processing_time=processing_time,
        )
        return ocr_result
    except Exception as db_err:
        logger.error(f"Failed to save AI results to DB: {db_err}")
        raise


def extract_text_from_image(image_path):
    """Extract text from an image using OCR (pytesseract)."""
    if not image_path or not os.path.exists(image_path):
        return ""

    try:
        # pyrefly: ignore [missing-import]
        import pytesseract
        # pyrefly: ignore [missing-import]
        from PIL import Image

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except ImportError:
        logger.warning("pytesseract not installed, vision model will be used")
        return ""
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""


def verify_price(item, price, city, currency='INR'):
    """Universal AI price intelligence engine — verifies any item, service, or product price."""
    client = get_groq_client()

    if not client:
        return {
            'is_fair': None,
            'verdict': 'Unavailable',
            'fair_price_range': 'AI unavailable',
            'scam_probability': 0,
            'analysis': 'AI price verification is currently unavailable. Please configure your Groq API key.',
            'recommendation': 'Compare with local sources for verification.',
            'local_tips': [],
        }

    system_prompt = f"""You are a universal price intelligence expert with deep knowledge of local and global market pricing.

You can analyze the price of ANYTHING: food, electronics, transport, tourism activities, tickets, rentals, healthcare, entertainment, accommodation, services, products, utilities, subscriptions — literally any price query.

CRITICAL RULES:

1. IDENTIFY what the user is asking about. Understand the category automatically:
   - Food & beverages (tea, meals, street food, restaurant dining)
   - Electronics & gadgets (phones, laptops, cameras, accessories)
   - Transport (taxi, auto-rickshaw, Uber, bike rental, fuel)
   - Tourism activities (boat rides, trekking, guided tours, safaris)
   - Tickets (movie, museum, amusement park, concert, flights)
   - Accommodation (hotel rooms, homestays, resorts)
   - Shopping (clothing, souvenirs, sunglasses, jewelry)
   - Services (spa, photography, haircut, laundry, medical)
   - Rentals (scooter, car, equipment, camera)
   - Utilities (mobile recharge, internet, parking, tolls)

2. FAIR PRICE RANGE — Be realistic and specific:
   - Base your range on REAL market prices in the specified city
   - Account for quality tiers (budget/mid-range/premium)
   - Tourist areas typically cost 10-30% more — this is NORMAL, not a scam
   - Airport/mall/hotel premises have legitimately higher prices
   - Brand products (Apple, Samsung, etc.) have fixed MRP — use actual retail prices
   - Street food vs restaurant vs cafe have different legitimate price ranges
   - If you're uncertain about exact pricing, give a wider but honest range

3. VERDICT — Use exactly one of these five categories:
   - "Fair Price" — within or below the expected range
   - "Slightly Expensive" — up to 25% above fair range (normal variation)
   - "Tourist Area Pricing" — 25-50% above but explainable by location/context
   - "Overpriced" — 50-100% above fair range, likely overcharging
   - "Suspiciously High" — more than 100% above, probable scam/fraud

4. SCAM PROBABILITY — Calculate based on actual deviation:
   - Within range: 0-5%
   - Up to 25% over: 5-15%
   - 25-50% over: 15-35%
   - 50-100% over: 35-65%
   - 100-200% over: 65-85%
   - 200%+ over: 85-100%

5. ANALYSIS — Write 2-3 specific sentences that:
   - Directly reference the item and city
   - Explain WHY the price is fair or overpriced using real comparisons
   - Mention specific local context (e.g., "street chai costs ₹10-15 in Ernakulam, cafes charge ₹30-50")
   - Do NOT be generic — be specific to the item and location

6. LOCAL TIPS — Give 2-3 actionable, category-specific tips:
   - For food: where to find better deals, local alternatives
   - For electronics: price comparison advice, warranty checks
   - For transport: typical fare structures, meter vs negotiated
   - For tourism: booking platforms, off-season pricing
   - For shopping: bargaining norms, authentic vs tourist shops

Respond ONLY with valid JSON."""

    # === RAG Context Retrieval ===
    rag_context = ""
    try:
        from rag_engine.services import get_rag_context
        rag_context = get_rag_context(query=item, city=city, top_k=4)
    except Exception as e:
        logger.warning(f"RAG retrieval failed, proceeding without context: {e}")

    # Build prompt with RAG context injection
    rag_section = ""
    if rag_context:
        rag_section = f"""\n\nThe following is verified pricing intelligence from our database. Use this data to ground your fair price estimates:\n\n{rag_context}\n"""

    prompt = f"""Analyze this price for a tourist:

Item/Service: {item}
Price Charged: {price} {currency}
City/Location: {city}
Currency: {currency}
{rag_section}
Respond with this exact JSON structure:
{{
    "is_fair": <true or false>,
    "verdict": "<exactly one of: Fair Price | Slightly Expensive | Tourist Area Pricing | Overpriced | Suspiciously High>",
    "category": "<detected category: food, electronics, transport, tourism, tickets, accommodation, shopping, services, rentals, utilities, other>",
    "fair_price_low": <number — lowest typical price>,
    "fair_price_high": <number — highest typical price>,
    "fair_price_range": "<low> - <high> {currency}",
    "scam_probability": <number 0-100>,
    "overcharge_percentage": <number, 0 if within range>,
    "analysis": "<2-3 sentence specific analysis referencing the item, city, and real local pricing>",
    "recommendation": "<specific actionable advice for this exact situation>",
    "local_tips": ["<tip1>", "<tip2>", "<tip3>"]
}}"""

    try:
        response = client.chat.completions.create(
            model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.15,
            max_tokens=1200,
        )

        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)

        # --- Post-processing validation ---
        try:
            price_val = float(price)
            fair_high = float(result.get('fair_price_high', 0))
            fair_low = float(result.get('fair_price_low', 0))

            # Sanity check: fair range should be reasonable
            if fair_high > 0 and fair_low > 0:
                # Ensure low <= high
                if fair_low > fair_high:
                    fair_low, fair_high = fair_high, fair_low
                    result['fair_price_low'] = fair_low
                    result['fair_price_high'] = fair_high
                    result['fair_price_range'] = f"{fair_low} - {fair_high} {currency}"

                # Calculate overcharge based on validated fair range
                if price_val <= fair_high:
                    result['is_fair'] = True
                    result['overcharge_percentage'] = 0
                    # Price within range — cap scam probability
                    result['scam_probability'] = min(result.get('scam_probability', 0), 10)
                elif price_val <= fair_high * 1.25:
                    result['overcharge_percentage'] = round(((price_val - fair_high) / fair_high) * 100, 1)
                    result['scam_probability'] = min(result.get('scam_probability', 15), 20)
                    result['verdict'] = result.get('verdict', 'Slightly Expensive')
                else:
                    result['is_fair'] = False
                    result['overcharge_percentage'] = round(((price_val - fair_high) / fair_high) * 100, 1)

                # Enforce verdict consistency with overcharge
                overcharge_pct = result.get('overcharge_percentage', 0)
                if overcharge_pct == 0:
                    result['verdict'] = 'Fair Price'
                elif overcharge_pct <= 25:
                    if result.get('verdict') not in ('Fair Price', 'Slightly Expensive', 'Tourist Area Pricing'):
                        result['verdict'] = 'Slightly Expensive'
                elif overcharge_pct <= 50:
                    if result.get('verdict') not in ('Tourist Area Pricing', 'Slightly Expensive'):
                        result['verdict'] = 'Tourist Area Pricing'
                elif overcharge_pct <= 100:
                    result['verdict'] = 'Overpriced'
                else:
                    result['verdict'] = 'Suspiciously High'

        except (ValueError, TypeError):
            pass

        # Ensure verdict exists
        if 'verdict' not in result:
            if result.get('is_fair'):
                result['verdict'] = 'Fair Price'
            elif result.get('scam_probability', 0) > 65:
                result['verdict'] = 'Suspiciously High'
            elif result.get('scam_probability', 0) > 35:
                result['verdict'] = 'Overpriced'
            else:
                result['verdict'] = 'Slightly Expensive'

        # Ensure local_tips is a list
        if not isinstance(result.get('local_tips'), list):
            result['local_tips'] = []

        return result

    except Exception as e:
        logger.error(f"Price verification failed: {e}")
        return {
            'is_fair': None,
            'verdict': 'Error',
            'fair_price_range': 'Analysis failed',
            'scam_probability': 0,
            'analysis': 'Price verification encountered an error. Please try again.',
            'recommendation': 'Try again or compare with local sources.',
            'local_tips': [],
        }


def ai_chat_response(user_message, context=""):
    """Generate AI assistant response for tourist queries."""
    client = get_groq_client()

    if not client:
        return {
            'response': "I'm currently offline. Please ensure the Groq API key is configured to enable AI assistance. In the meantime, check the scam reports and vendor listings for safety information.",
            'suggestions': [
                'Browse verified vendors',
                'Check scam heatmap',
                'Upload a bill for analysis'
            ]
        }

    system_prompt = """You are ScamGuard AI, a friendly and knowledgeable tourist safety assistant. You help tourists:
1. Identify potential scams and overpricing
2. Find safe and trusted vendors, restaurants, and transport
3. Provide local pricing knowledge
4. Give safety tips for tourist areas

Be helpful, specific, and practical. If you're uncertain, say so. Provide actionable advice.
Keep responses concise but informative (2-4 paragraphs max)."""

    if context:
        system_prompt += f"\n\nContext from local scam database:\n{context}"

    try:
        response = client.chat.completions.create(
            model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1024,
        )

        ai_response = response.choices[0].message.content.strip()

        return {
            'response': ai_response,
            'suggestions': [
                'Check vendor trustworthiness',
                'Verify a price',
                'Report a scam',
            ]
        }

    except Exception as e:
        logger.error(f"AI chat failed: {e}")
        return {
            'response': "I'm having trouble processing your request right now. Please try again in a moment.",
            'suggestions': ['Try again', 'Browse reports', 'Check vendors']
        }


def find_similar_reports(report_text, top_k=5):
    """Find semantically similar scam reports using sentence transformers."""
    try:
        # pyrefly: ignore [missing-import]
        from sentence_transformers import SentenceTransformer
        # pyrefly: ignore [missing-import]
        from sklearn.metrics.pairwise import cosine_similarity
        # pyrefly: ignore [missing-import]
        import numpy as np
        # pyrefly: ignore [missing-import]
        from scams.models import ScamReport

        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Get existing reports as a list so indices match reliably
        existing_reports = list(ScamReport.objects.order_by('-created_at')[:100])
        if not existing_reports:
            return []

        # Encode
        report_texts = [f"{r.title} {r.description}" for r in existing_reports]
        report_embeddings = model.encode(report_texts)
        query_embedding = model.encode([report_text])

        # Compute similarities
        similarities = cosine_similarity(query_embedding, report_embeddings)[0]

        # Get top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        similar = []
        for idx in top_indices:
            if similarities[idx] > 0.3:
                report = existing_reports[int(idx)]
                similar.append({
                    'report': report,
                    'similarity': float(similarities[idx]),
                })

        return similar

    except ImportError:
        logger.warning("sentence-transformers not installed")
        return []
    except Exception as e:
        logger.error(f"Similarity search failed: {e}")
        return []
