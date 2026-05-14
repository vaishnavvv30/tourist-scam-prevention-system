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


def analyze_bill(bill):
    """Analyze an uploaded bill using Vision AI + OCR fallback."""
    # pyrefly: ignore [missing-import]
    from scams.models import OCRResult, AIAnalysis
    start_time = time.time()

    client = get_groq_client()

    analysis_result = {
        'items_detected': [],
        'total_detected': None,
        'taxes_detected': [],
        'suspicious_charges': [],
        'confidence_score': 0.5,
        'fair_price_estimate': None,
        'scam_probability': 50.0,
        'analysis_notes': 'Analysis performed with limited data.',
    }

    extracted_text = ""
    vision_success = False

    # Step 1: Try vision-based analysis (no OCR dependency needed)
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

                vision_prompt = f"""Analyze this bill/receipt image carefully. Extract all text and line items.

Bill Type: {bill.get_bill_type_display()}
Location: {bill.location_name or 'Unknown'}
Stated Total: {bill.total_amount} {bill.currency}

Respond ONLY with this JSON:
{{
    "extracted_text": "<all text visible on the bill>",
    "items_detected": [{{"name": "<item>", "price": <amount>}}, ...],
    "total_detected": <total amount or null>,
    "taxes_detected": [{{"type": "<tax name>", "amount": <amount>}}, ...],
    "suspicious_charges": ["<description>", ...],
    "confidence_score": <float 0-1>,
    "fair_price_estimate": <estimated fair total or null>,
    "scam_probability": <float 0-100>,
    "analysis_notes": "<detailed analysis>"
}}"""

                response = client.chat.completions.create(
                    model='llama-3.2-90b-vision-preview',
                    messages=[
                        {"role": "system", "content": "You are a bill analysis expert. Read the bill image, extract text, detect overcharging. Respond with valid JSON only."},
                        {"role": "user", "content": [
                            {"type": "text", "text": vision_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
                        ]}
                    ],
                    temperature=0.2,
                    max_tokens=1500,
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
            prompt = f"""Analyze this bill/receipt text. Identify overcharging or scam indicators.

Bill Type: {bill.get_bill_type_display()}
Location: {bill.location_name}
Stated Total: {bill.total_amount} {bill.currency}

Extracted Text:
{extracted_text}

Respond ONLY with JSON:
{{
    "items_detected": [{{"name": "<item>", "price": <amount>}}, ...],
    "total_detected": <total amount or null>,
    "taxes_detected": [{{"type": "<tax>", "amount": <amount>}}, ...],
    "suspicious_charges": ["<description>", ...],
    "confidence_score": <float 0-1>,
    "fair_price_estimate": <fair total or null>,
    "scam_probability": <float 0-100>,
    "analysis_notes": "<detailed analysis>"
}}"""

            try:
                response = client.chat.completions.create(
                    model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
                    messages=[
                        {"role": "system", "content": "You are a bill analysis expert. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1024,
                )
                result_text = response.choices[0].message.content.strip()
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    analysis_result = json.loads(result_text)
            except Exception as e:
                logger.error(f"Bill AI analysis failed: {e}")

    def safe_float(val, default):
        try:
            if val is None: return default
            return float(val)
        except:
            return default

    # Save results
    try:
        ocr_result, _ = OCRResult.objects.update_or_create(
            bill=bill,
            defaults={
                'extracted_text': extracted_text or 'Text extracted via AI vision analysis.',
                'items_detected': analysis_result.get('items_detected', []),
                'total_detected': safe_float(analysis_result.get('total_detected'), None),
                'taxes_detected': analysis_result.get('taxes_detected', []),
                'suspicious_charges': analysis_result.get('suspicious_charges', []),
                'confidence_score': safe_float(analysis_result.get('confidence_score', 0.5), 0.5),
                'fair_price_estimate': safe_float(analysis_result.get('fair_price_estimate'), None),
                'scam_probability': safe_float(analysis_result.get('scam_probability', 50), 50.0),
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
            confidence=safe_float(analysis_result.get('confidence_score', 0.5), 0.5),
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
    """Verify if a price is fair using AI."""
    client = get_groq_client()

    if not client:
        return {
            'is_fair': None,
            'fair_price_range': 'AI unavailable',
            'scam_probability': 50,
            'analysis': 'AI price verification is currently unavailable. Please configure your Groq API key.',
            'recommendation': 'Compare with local sources for verification.',
        }

    prompt = f"""You are an expert on local pricing in cities worldwide. A tourist needs to verify a price.

Item/Service: {item}
Price Charged: {price} {currency}
City: {city}
Currency: {currency}

IMPORTANT RULES:
1. Research your knowledge of typical local prices in {city} for "{item}".
2. Compare the charged price ({price} {currency}) against the fair local range.
3. If the price is BELOW or WITHIN the fair range, mark is_fair as true.
4. If the price is ABOVE the fair range, mark is_fair as false.
5. Set scam_probability based on how far the price deviates from the fair range:
   - Within range: 0-20%
   - Slightly above (up to 50% over): 20-50%
   - Significantly above (50-200% over): 50-80%
   - Extremely above (200%+ over): 80-100%
6. Be accurate with local pricing. Consider that tourist areas may have slightly higher prices.
7. The overcharge_percentage should be calculated as: ((charged_price - fair_high) / fair_high) * 100. If within range, set to 0.

Respond ONLY with this JSON (no other text):
{{
    "is_fair": <true or false>,
    "fair_price_low": <number - lowest fair price>,
    "fair_price_high": <number - highest fair price>,
    "fair_price_range": "<low> - <high> {currency}",
    "scam_probability": <number 0-100>,
    "overcharge_percentage": <number, 0 if fair>,
    "analysis": "<2-3 sentence detailed analysis explaining WHY this price is fair or unfair based on local rates>",
    "recommendation": "<specific actionable advice for the tourist>",
    "local_tips": ["<tip1>", "<tip2>"]
}}"""

    try:
        response = client.chat.completions.create(
            model=getattr(settings, 'AI_MODEL', 'llama-3.3-70b-versatile'),
            messages=[
                {"role": "system", "content": "You are a precise local pricing expert. You must respond with valid JSON only. Be accurate with real-world prices. Never hallucinate prices - if uncertain, provide conservative estimates and say so in the analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)

        # Validate and enforce consistency
        try:
            price_val = float(price)
            fair_high = float(result.get('fair_price_high', 0))
            fair_low = float(result.get('fair_price_low', 0))
            if fair_high > 0:
                if price_val <= fair_high:
                    result['is_fair'] = True
                    result['overcharge_percentage'] = 0
                    if result.get('scam_probability', 0) > 25:
                        result['scam_probability'] = max(0, min(25, result['scam_probability']))
                else:
                    result['is_fair'] = False
                    result['overcharge_percentage'] = round(((price_val - fair_high) / fair_high) * 100, 1)
        except (ValueError, TypeError):
            pass

        return result

    except Exception as e:
        logger.error(f"Price verification failed: {e}")
        return {
            'is_fair': None,
            'fair_price_range': 'Analysis failed',
            'scam_probability': 50,
            'analysis': f'Price verification encountered an error.',
            'recommendation': 'Try again or compare with local sources.',
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
