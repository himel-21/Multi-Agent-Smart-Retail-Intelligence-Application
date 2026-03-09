import json
import logging
import boto3
from datetime import datetime, timedelta
import time
import uuid
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main Lambda handler for Bedrock agent marketplace intelligence
    """
    logger.info(f"=== LAMBDA INVOKED ===")
    logger.info(f"Event: {json.dumps(event, default=str)[:1000]}...")
    logger.info(f"Context: {context}")
    
    try:
        # Route based on event type
        if is_bedrock_agent_call(event):
            logger.info("Detected Bedrock agent call")
            return handle_bedrock_agent_call(event, context)
        else:
            logger.info("Detected direct call")
            return handle_direct_call(event, context)
            
    except Exception as e:
        logger.error(f"Lambda handler critical error: {str(e)}", exc_info=True)
        return create_fallback_response(str(e))

def is_bedrock_agent_call(event):
    """
    Detect if this is a Bedrock agent call
    """
    bedrock_indicators = [
        'agent' in event,
        'actionGroup' in event,
        'apiPath' in event,
        'httpMethod' in event,
        'messageVersion' in event,
        'sessionId' in event,
        'inputText' in event
    ]
    
    is_bedrock = any(bedrock_indicators)
    logger.info(f"Bedrock call detection: {is_bedrock}")
    return is_bedrock

def handle_bedrock_agent_call(event, context):
    """
    Handle Bedrock agent calls with comprehensive error handling
    """
    logger.info("=== PROCESSING BEDROCK AGENT CALL ===")
    
    try:
        # Extract parameters from event
        params = extract_parameters_from_event(event)
        logger.info(f"Extracted parameters: {params}")
        
        # Process the request
        result = process_marketplace_request(params)
        logger.info(f"Processing result: {json.dumps(result, default=str)[:500]}...")
        
        # Create Bedrock response
        bedrock_response = create_bedrock_response(event, result)
        logger.info(f"Bedrock response created: {json.dumps(bedrock_response, default=str)[:500]}...")
        
        return bedrock_response
        
    except Exception as e:
        logger.error(f"Bedrock handler error: {str(e)}", exc_info=True)
        return create_bedrock_error_response(event, str(e))

def extract_parameters_from_event(event):
    """
    Extract parameters from various Bedrock event formats
    """
    params = {
        'userQuery': 'HP OmniBook 7 laptop',
        'userType': 'customer',
        'currency': 'INR'
    }
    
    try:
        # Method 1: API Schema format (requestBody)
        if 'requestBody' in event:
            logger.info("Extracting from requestBody")
            request_body = event['requestBody']
            
            if isinstance(request_body, str):
                body_data = json.loads(request_body)
            else:
                body_data = request_body
                
            params.update(body_data)
        
        # Method 2: Function Schema format (parameters array)
        elif 'parameters' in event:
            logger.info("Extracting from parameters array")
            for param in event['parameters']:
                if isinstance(param, dict) and 'name' in param and 'value' in param:
                    params[param['name']] = param['value']
        
        # Method 3: Direct properties
        else:
            logger.info("Extracting from direct properties")
            if 'userQuery' in event:
                params['userQuery'] = event['userQuery']
            if 'userType' in event:
                params['userType'] = event['userType']
            if 'currency' in event:
                params['currency'] = event['currency']
        
        # Normalize userType
        if params['userType'].lower() in ['customer', 'retailer']:
            params['userType'] = params['userType'].lower()
        
        logger.info(f"Final extracted parameters: {params}")
        return params
        
    except Exception as e:
        logger.error(f"Parameter extraction error: {str(e)}")
        return params

def process_marketplace_request(params):
    """
    Process marketplace intelligence request
    """
    user_query = params.get('userQuery', 'HP OmniBook 7 laptop')
    user_type = params.get('userType', 'customer')
    currency = params.get('currency', 'INR')
    
    logger.info(f"Processing: {user_type} query '{user_query}' in {currency}")
    
    # Generate response based on user type
    if user_type == 'retailer':
        return generate_retailer_response(user_query, currency)
    else:
        return generate_customer_response(user_query, currency)

def generate_customer_response(user_query, currency):
    """
    Generate customer marketplace response
    """
    return {
        "user_type": "customer",
        "request_timestamp": datetime.now().isoformat(),
        "summary": {
            "total_available_products": 1,
            "total_marketplaces": 1,
            "marketplaces_list": ["HP Store India"],
            "price_range": {
                "min_price": 134999.0,
                "max_price": 134999.0,
                "avg_price": 134999.0
            }
        },
        "products": [{
            "product_id": "18064606952590202837",
            "product_name": "HP OmniBook 7 Intel Core Ultra AI Laptop",
            "category": "Electronics",
            "seller": "HP Store India",
            "marketplace": "HP Store India",
            "price": 134999.0,
            "currency": currency,
            "stock_count": 21,
            "stock_level": "In Stock",
            "stock_status": "Critical",
            "item_condition": "Excellent",
            "seller_authenticity": "Unverified",
            "sentiment_velocity": 4.5,
            "fraud_return_ratio": 0.04,
            "risk_score": 0.39,
            "verification_score": 1.0,
            "last_updated": datetime.now().isoformat()
        }],
        "message": "Found 1 HP OmniBook 7 laptop available at ₹134,999",
        "recommendations": [{
            "type": "BEST_DEAL",
            "message": "Limited stock - order soon!",
            "priority": "HIGH"
        }]
    }

def generate_retailer_response(user_query, currency):
    """
    Generate retailer marketplace response
    """
    return {
        "user_type": "retailer",
        "request_timestamp": datetime.now().isoformat(),
        "summary": {
            "total_products_monitored": 1,
            "products_with_alerts": 1,
            "total_inventory_value": 2834979.0,
            "low_stock_alerts": 1,
            "critical_stock_alerts": 0
        },
        "inventory": [{
            "product_id": "18064606952590202837",
            "product_name": "HP OmniBook 7 Intel Core Ultra AI Laptop",
            "category": "Electronics",
            "seller": "HP Store India",
            "marketplace": "HP Store India",
            "price": 134999.0,
            "currency": currency,
            "stock_count": 21,
            "stock_level": "In Stock",
            "stock_status": "Critical",
            "item_condition": "Excellent",
            "seller_authenticity": "Unverified",
            "sentiment_velocity": 4.5,
            "fraud_return_ratio": 0.04,
            "risk_score": 0.39,
            "verification_score": 1.0,
            "last_updated": datetime.now().isoformat(),
            "sku": "HP-OB7-001",
            "reorder_level": 10,
            "supplier": "HP India"
        }],
        "message": "Monitoring 1 HP laptop - low stock alert",
        "recommendations": [{
            "type": "RESTOCK_ALERT",
            "message": "Stock level critical - reorder recommended",
            "priority": "HIGH",
            "action": "Reorder 15 units"
        }]
    }

def create_bedrock_response(event, result):
    """
    Create properly formatted Bedrock agent response
    """
    try:
        # Determine response format based on event
        if 'apiPath' in event or 'httpMethod' in event:
            # API Schema format
            response = {
                'messageVersion': '1.0',
                'response': {
                    'apiPath': event.get('apiPath', '/marketplace-intelligence'),
                    'httpMethod': event.get('httpMethod', 'POST'),
                    'httpStatusCode': 200,
                    'responseBody': {
                        'application/json': {
                            'body': json.dumps(result, separators=(',', ':'), default=str)
                        }
                    }
                }
            }
        else:
            # Function Schema format
            response = {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': event.get('actionGroup', 'marketplace_processor'),
                    'function': event.get('function', 'getMarketplaceIntelligence'),
                    'functionResponse': {
                        'responseBody': {
                            'TEXT': {
                                'body': json.dumps(result, separators=(',', ':'), default=str)
                            }
                        }
                    }
                }
            }
        
        logger.info(f"Created Bedrock response format: {list(response.keys())}")
        return response
        
    except Exception as e:
        logger.error(f"Response creation error: {str(e)}")
        return create_bedrock_error_response(event, str(e))

def create_bedrock_error_response(event, error_message):
    """
    Create standardized Bedrock error response
    """
    error_data = {
        'error': f'Processing failed: {error_message}',
        'timestamp': datetime.now().isoformat(),
        'user_type': 'customer',
        'message': 'Service temporarily unavailable'
    }
    
    if 'apiPath' in event or 'httpMethod' in event:
        return {
            'messageVersion': '1.0',
            'response': {
                'apiPath': event.get('apiPath', '/marketplace-intelligence'),
                'httpMethod': event.get('httpMethod', 'POST'),
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(error_data, separators=(',', ':'))
                    }
                }
            }
        }
    else:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', 'marketplace_processor'),
                'function': event.get('function', 'getMarketplaceIntelligence'),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(error_data, separators=(',', ':'))
                        }
                    }
                }
            }
        }

def handle_direct_call(event, context):
    """
    Handle direct Lambda invocation
    """
    logger.info("Processing direct call")
    
    params = {
        'userQuery': event.get('userQuery', 'HP OmniBook 7 laptop'),
        'userType': event.get('userType', 'customer'),
        'currency': event.get('currency', 'INR')
    }
    
    result = process_marketplace_request(params)
    
    return {
        "statusCode": 200,
        "body": json.dumps(result, separators=(',', ':'), default=str),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    }

def create_fallback_response(error_message):
    """
    Create fallback response for critical errors
    """
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'marketplace_processor',
            'function': 'getMarketplaceIntelligence',
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'error': f'Critical error: {error_message}',
                            'timestamp': datetime.now().isoformat(),
                            'message': 'Service unavailable'
                        }, separators=(',', ':'))
                    }
                }
            }
        }
    }
