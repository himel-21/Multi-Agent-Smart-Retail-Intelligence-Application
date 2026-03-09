import json
import os
import urllib3
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Badge Agent Lambda handler with comprehensive debugging
    """
    
    # CRITICAL: Log the entire event structure
    logger.info("="*50)
    logger.info("COMPLETE EVENT RECEIVED:")
    logger.info(json.dumps(event, indent=2, default=str))
    logger.info("="*50)
    
    try:
        # Extract product name from event
        product_name = extract_product_name_from_event(event)
        
        logger.info(f"EXTRACTED PRODUCT NAME: '{product_name}'")
        
        if not product_name or product_name.strip() == "":
            logger.error("PRODUCT NAME IS EMPTY - RETURNING ERROR MESSAGE")
            return create_api_schema_response(
                event,
                "To proceed with the verification, please provide the exact name of the product you want to check for the genuine badge certification."
            )
        
        logger.info(f"Processing badge verification for: '{product_name}'")
        
        # Validate environment variables
        serpapi_key = os.environ.get('SERPAPI_KEY')
        if not serpapi_key:
            return create_api_schema_response(
                event,
                "Product verification service is temporarily unavailable. Please try again later."
            )
        
        # Perform badge verification
        verification_result = perform_badge_verification_realistic(product_name)
        
        # Return API schema format response
        return create_api_schema_response(event, verification_result)
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        return create_api_schema_response(
            event,
            f"I encountered an error while verifying the product: {str(e)}. Please try again."
        )

def extract_product_name_from_event(event):
    """Extract product name with comprehensive debugging"""
    
    logger.info("="*30)
    logger.info("EXTRACTING PRODUCT NAME")
    logger.info("="*30)
    
    # Log all top-level keys
    logger.info(f"Event top-level keys: {list(event.keys())}")
    
    # Method 1: Check parameters array (most common for Bedrock)
    if "parameters" in event:
        logger.info(f"Found 'parameters' key")
        parameters = event["parameters"]
        logger.info(f"Parameters type: {type(parameters)}")
        logger.info(f"Parameters content: {parameters}")
        
        if isinstance(parameters, list):
            logger.info(f"Parameters is a list with {len(parameters)} items")
            for i, param in enumerate(parameters):
                logger.info(f"Parameter {i}: {param}")
                if isinstance(param, dict):
                    param_name = param.get("name")
                    param_value = param.get("value")
                    logger.info(f"  - name: '{param_name}', value: '{param_value}'")
                    
                    if param_name == "product_name" and param_value:
                        product_name = str(param_value).strip()
                        logger.info(f"SUCCESS: Found product_name in parameters: '{product_name}'")
                        return product_name
        else:
            logger.info(f"Parameters is not a list: {parameters}")
    else:
        logger.info("No 'parameters' key found in event")
    
    # Method 2: Check requestBody
    if "requestBody" in event:
        logger.info(f"Found 'requestBody' key")
        request_body = event["requestBody"]
        logger.info(f"RequestBody: {request_body}")
        
        if "content" in request_body:
            content = request_body["content"]
            logger.info(f"Content: {content}")
            
            if "application/json" in content:
                json_content = content["application/json"]
                logger.info(f"JSON content: {json_content}")
                
                if isinstance(json_content, dict) and "product_name" in json_content:
                    product_name = str(json_content["product_name"]).strip()
                    logger.info(f"SUCCESS: Found product_name in requestBody: '{product_name}'")
                    return product_name
    else:
        logger.info("No 'requestBody' key found in event")
    
    # Method 3: Check inputText
    if "inputText" in event:
        logger.info(f"Found 'inputText' key: {event['inputText']}")
        input_text = event["inputText"]
        
        # Try to parse as JSON
        try:
            input_data = json.loads(input_text)
            logger.info(f"Parsed inputText as JSON: {input_data}")
            if "product_name" in input_data:
                product_name = str(input_data["product_name"]).strip()
                logger.info(f"SUCCESS: Found product_name in inputText: '{product_name}'")
                return product_name
        except:
            logger.info("inputText is not valid JSON")
            
            # Try to extract product name from plain text
            # Look for common patterns like "Check Samsung Galaxy S24"
            import re
            
            # Pattern to extract product names after common phrases
            patterns = [
                r"check\s+(?:the\s+)?authenticity\s+of\s+(.+?)(?:\s|$)",
                r"verify\s+(.+?)(?:\s|$)",
                r"is\s+(.+?)\s+genuine",
                r"authenticate\s+(.+?)(?:\s|$)",
                r"badge\s+for\s+(.+?)(?:\s|$)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, input_text.lower())
                if match:
                    product_name = match.group(1).strip()
                    logger.info(f"SUCCESS: Extracted product_name from inputText pattern: '{product_name}'")
                    return product_name
    else:
        logger.info("No 'inputText' key found in event")
    
    # Method 4: Check all other keys for product_name
    for key, value in event.items():
        if key.lower() == "product_name":
            product_name = str(value).strip()
            logger.info(f"SUCCESS: Found product_name in event['{key}']: '{product_name}'")
            return product_name
    
    logger.error("FAILED: No product_name found anywhere in the event")
    return ""

def perform_badge_verification_realistic(search_query):
    """Main badge verification with realistic criteria"""
    
    try:
        logger.info(f"Starting badge verification for: '{search_query}'")
        
        # Fetch product data from SerpAPI
        products_data = fetch_product_data_from_serpapi(search_query)
        
        if isinstance(products_data, str):  # Error message returned
            return f"Search error: {products_data}"
        
        if not products_data:
            return f"No products found for '{search_query}' in marketplace. Try searching with specific seller names like '{search_query} Amazon' for better results."
        
        # Use realistic criteria
        min_pillars_required = int(os.environ.get('MIN_PILLARS_REQUIRED', '1'))
        min_reviews = int(os.environ.get('MIN_REVIEWS', '5'))
        rating_threshold = float(os.environ.get('RATING_THRESHOLD', '3.0'))
        
        logger.info(f"Using criteria: min_pillars={min_pillars_required}, min_reviews={min_reviews}, rating_threshold={rating_threshold}")
        
        # Verify products
        verified_products = []
        
        for product in products_data[:10]:
            verification_result = verify_product_pillars_realistic(product, min_pillars_required, min_reviews, rating_threshold)
            
            if verification_result["pillars_passed"] >= min_pillars_required:
                verified_products.append(verification_result)
        
        logger.info(f"Verification complete: {len(verified_products)} products qualify")
        
        # Generate response text
        return generate_badge_response_text(search_query, verified_products, min_pillars_required)
        
    except Exception as e:
        logger.error(f"Error in verification: {str(e)}")
        return f"Verification error: {str(e)}"

def fetch_product_data_from_serpapi(search_query):
    """Fetch products from SerpAPI"""
    
    try:
        serpapi_key = os.environ.get('SERPAPI_KEY')
        base_url = os.environ.get('VERIFICATION_API_BASE_URL', 'https://serpapi.com/search.json?engine=google_shopping')
        
        formatted_query = search_query.replace(' ', '+')
        url = f"{base_url}&q={formatted_query}&location=India&hl=en&gl=in&api_key={serpapi_key}&num=15"
        
        logger.info(f"Fetching data for: '{search_query}'")
        
        http = urllib3.PoolManager()
        response = http.request('GET', url, timeout=25)
        
        if response.status != 200:
            return f"Search service unavailable (HTTP {response.status})"
        
        results = json.loads(response.data.decode('utf-8'))
        
        if "error" in results:
            return f"Search API error: {results['error']}"
        
        shopping_results = results.get("shopping_results", [])
        if not shopping_results:
            shopping_results = results.get("inline_shopping_results", [])
        if not shopping_results:
            shopping_results = results.get("products", [])
        
        if not shopping_results:
            return []
        
        logger.info(f"Found {len(shopping_results)} products")
        return shopping_results
        
    except Exception as e:
        logger.error(f"Fetch error: {str(e)}")
        return f"Data retrieval error: {str(e)}"

def verify_product_pillars_realistic(product, min_pillars_required, min_reviews, rating_threshold):
    """Verify product using 3-pillar system"""
    
    title = product.get("title", "")
    price = product.get("price", "Price not available")
    source = product.get("source", "")
    rating = extract_numeric_value(product.get("rating", 0))
    reviews = extract_numeric_value(product.get("reviews", 0))
    
    pillars_passed = 0
    pillar_results = []
    
    # Pillar 1: Seller Credentials
    seller_status = evaluate_seller_credentials_realistic(source)
    if seller_status["verified"]:
        pillars_passed += 1
        pillar_results.append(f"✓ Seller: {seller_status['status']} ({seller_status['category']})")
    else:
        pillar_results.append(f"✗ Seller: {seller_status['status']}")
    
    # Pillar 2: Authenticity Indicators
    authenticity_status = evaluate_authenticity_indicators_realistic(title, product, source)
    if authenticity_status["has_certificate"]:
        pillars_passed += 1
        pillar_results.append(f"✓ Certificate: {authenticity_status['reason']}")
    else:
        pillar_results.append(f"✗ Certificate: {authenticity_status['reason']}")
    
    # Pillar 3: Historical Rating
    rating_status = evaluate_historical_rating_realistic(rating, reviews, rating_threshold, min_reviews)
    if rating_status["meets_threshold"]:
        pillars_passed += 1
        pillar_results.append(f"✓ Rating: {rating_status['reason']}")
    else:
        pillar_results.append(f"✗ Rating: {rating_status['reason']}")
    
    return {
        "title": title,
        "price": price,
        "source": source,
        "rating": rating,
        "reviews": reviews,
        "pillars_passed": pillars_passed,
        "pillar_results": pillar_results,
        "seller_category": seller_status['category']
    }

def evaluate_seller_credentials_realistic(source):
    """Evaluate seller credentials"""
    
    if not source:
        return {"verified": False, "status": "Unknown seller", "category": "Unknown"}
    
    source_lower = source.lower().strip()
    
    # PLATINUM TIER
    platinum_patterns = {
        "amazon": "Platinum E-tailer",
        "flipkart": "Platinum E-tailer", 
        "jiomart": "Platinum E-tailer",
        "reliance": "Platinum E-tailer",
        "tata": "Platinum E-tailer",
        "meesho": "Platinum E-tailer",
        "snapdeal": "Platinum E-tailer",
        "paytm": "Platinum E-tailer",
        "apple": "Official Brand Store",
        "samsung": "Official Brand Store"
    }
    
    # VERIFIED TIER
    verified_patterns = {
        "myntra": "Fashion Specialist",
        "ajio": "Fashion Specialist",
        "nykaa": "Beauty Specialist",
        "croma": "Electronics Specialist",
        "vijaysales": "Electronics Specialist",
        "lenskart": "Eyewear Specialist"
    }
    
    # Check patterns
    for pattern, category in platinum_patterns.items():
        if pattern in source_lower:
            return {"verified": True, "status": "Platinum", "category": category}
    
    for pattern, category in verified_patterns.items():
        if pattern in source_lower:
            return {"verified": True, "status": "Verified", "category": category}
    
    return {"verified": False, "status": "Unverified", "category": f"Independent ({source_lower})"}

def evaluate_authenticity_indicators_realistic(title, product, source):
    """Evaluate authenticity indicators"""
    
    title_lower = title.lower()
    source_lower = source.lower() if source else ""
    
    # Check for authenticity indicators
    primary_keywords = ["official", "authorized", "genuine", "original", "authentic"]
    secondary_keywords = ["warranty", "guarantee", "certified"]
    brand_keywords = ["samsung", "galaxy", "apple", "iphone", "oneplus", "xiaomi", "jordan", "nike"]
    trusted_seller_patterns = ["amazon", "flipkart", "samsung", "apple", "tata", "myntra"]
    
    primary_found = any(kw in title_lower for kw in primary_keywords)
    secondary_found = any(kw in title_lower for kw in secondary_keywords)
    brand_found = any(kw in title_lower for kw in brand_keywords)
    trusted_seller = any(pattern in source_lower for pattern in trusted_seller_patterns)
    
    if primary_found:
        return {"has_certificate": True, "reason": "Primary authenticity indicators found"}
    elif secondary_found:
        return {"has_certificate": True, "reason": "Warranty/guarantee indicators found"}
    elif brand_found and trusted_seller:
        return {"has_certificate": True, "reason": "Brand product from trusted seller"}
    elif trusted_seller:
        return {"has_certificate": True, "reason": "Product from verified trusted seller"}
    elif brand_found:
        return {"has_certificate": True, "reason": "Recognized brand product"}
    else:
        return {"has_certificate": False, "reason": "No clear authenticity indicators"}

def evaluate_historical_rating_realistic(rating, reviews, rating_threshold, min_reviews):
    """Evaluate historical rating"""
    
    if rating >= rating_threshold and reviews >= min_reviews:
        return {"meets_threshold": True, "reason": f"Excellent rating {rating}/5 with {reviews} reviews"}
    elif rating >= rating_threshold and reviews > 0:
        return {"meets_threshold": True, "reason": f"Good rating {rating}/5"}
    elif rating == 0 and reviews == 0:
        return {"meets_threshold": True, "reason": "New product (no ratings yet)"}
    else:
        return {"meets_threshold": False, "reason": f"Rating {rating}/5 with {reviews} reviews below threshold"}

def extract_numeric_value(value):
    """Extract numeric value"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            import re
            cleaned = value.replace(",", "").replace(" stars", "").replace(" reviews", "").replace(" review", "")
            match = re.search(r'(\d+\.?\d*)', cleaned)
            if match:
                return float(match.group(1))
        
        return 0.0
    except:
        return 0.0

def generate_badge_response_text(search_query, verified_products, min_pillars_required):
    """Generate badge response as formatted text"""
    
    if not verified_products:
        return f"""**Verification Status:** Denied
**Badge Awarded:** No
**Reasoning:** Analyzed products for '{search_query}' but none met the required {min_pillars_required} authenticity pillars. Try searching with specific seller names like '{search_query} Amazon' for better results.
**Confidence Score:** 10%"""
    
    # Get the best product
    best_product = max(verified_products, key=lambda x: x["pillars_passed"])
    
    # Calculate confidence
    base_confidence = int((best_product["pillars_passed"] / 3) * 100)
    bonus_confidence = min(len(verified_products) * 5, 20)
    confidence_score = min(base_confidence + bonus_confidence, 100)
    
    # Generate response
    if best_product["pillars_passed"] == 3:
        status = "Verified"
        badge = "Yes"
        reasoning = f"Product meets all 3 verification pillars. Available from {best_product['source']} - fully authenticated and genuine."
    elif best_product["pillars_passed"] >= min_pillars_required:
        status = "Verified"
        badge = "Yes"
        reasoning = f"Product meets {best_product['pillars_passed']}/3 verification pillars from {best_product['source']} - genuine badge awarded."
    else:
        status = "Pending"
        badge = "No"
        reasoning = f"Product meets only {best_product['pillars_passed']}/3 verification pillars."
    
    return f"""**Verification Status:** {status}
**Badge Awarded:** {badge}
**Reasoning:** {reasoning}
**Confidence Score:** {confidence_score}%

**Product Details:**
- Title: {best_product['title'][:80]}...
- Price: {best_product['price']}
- Available at: {best_product['source']}
- Rating: {best_product['rating']}/5 ({best_product['reviews']} reviews)

**Verification Pillars:**
{chr(10).join(best_product['pillar_results'])}"""

def create_api_schema_response(event, response_text):
    """Create API Schema response format"""
    
    logger.info("="*30)
    logger.info("CREATING RESPONSE")
    logger.info("="*30)
    
    api_path = event.get("apiPath", "/verify-product-authenticity")
    logger.info(f"Using apiPath: {api_path}")
    
    response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", "ProductVerificationGroup"),
            "apiPath": api_path,
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": response_text
                }
            }
        }
    }
    
    logger.info("RESPONSE STRUCTURE:")
    logger.info(json.dumps(response, indent=2, default=str))
    
    return response