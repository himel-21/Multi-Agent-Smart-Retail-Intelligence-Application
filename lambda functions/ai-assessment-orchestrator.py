import json
import boto3
import logging
from datetime import datetime
import random

# Configure logging properly
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AI Assessment Orchestrator - Enhanced version preserving existing logic
    """
    try:
        # Log the incoming event for debugging
        logger.info(f"🚀 Lambda invoked: {json.dumps(event, default=str)}")
        
        # Extract WebSocket context - EXISTING LOGIC PRESERVED
        request_context = event.get('requestContext', {})
        route_key = request_context.get('routeKey')
        connection_id = request_context.get('connectionId')
        domain_name = request_context.get('domainName')
        stage = request_context.get('stage')
        
        logger.info(f"📡 Route: {route_key}, Connection: {connection_id}")
        
        # Initialize API Gateway client - EXISTING LOGIC PRESERVED
        if domain_name and stage:
            endpoint_url = f"https://{domain_name}/{stage}"
            apigateway_client = boto3.client(
                'apigatewaymanagementapi',
                endpoint_url=endpoint_url,
                region_name='ap-south-1'
            )
            logger.info(f"✅ WebSocket client initialized: {endpoint_url}")
        else:
            logger.error("❌ Missing WebSocket context")
            return {'statusCode': 400}
        
        # Route handling - EXISTING LOGIC PRESERVED
        if route_key == '$connect':
            logger.info("🔌 Handling connection")
            send_websocket_message(apigateway_client, connection_id, {
                'type': 'status', 
                'message': 'Agent is coordinating: Connected to Product Discovery Platform'
            })
            return {'statusCode': 200}
        elif route_key == '$disconnect':
            logger.info("🔌 Handling disconnection")
            return {'statusCode': 200}
        elif route_key == 'assess':
            logger.info("🧠 Handling assessment")
            return handle_product_search(event, connection_id, apigateway_client)
        elif route_key == '$default':
            logger.info("❓ Handling default route")
            return handle_product_search(event, connection_id, apigateway_client)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"💥 Critical error in lambda_handler: {str(e)}")
        return {'statusCode': 500}

def handle_product_search(event, connection_id, apigateway_client):
    """
    Handle product search - EXISTING LOGIC PRESERVED with enhancements
    """
    try:
        logger.info(f"🛍️ Processing product search for: {connection_id}")
        
        # Parse request body - EXISTING LOGIC PRESERVED with error handling
        body_str = event.get('body', '{}')
        logger.info(f"📨 Raw body: {body_str}")
        
        if isinstance(body_str, str):
            body = json.loads(body_str)
        else:
            body = body_str
            
        message = body.get('message', '')
        user_type = body.get('userType', 'customer')
        
        logger.info(f"🔍 Search query: '{message}' (User: {user_type})")
        
        if not message.strip():
            logger.warning("⚠️ Empty search query received")
            send_websocket_message(apigateway_client, connection_id, {
                'type': 'result',
                'message': 'Please enter a search query',
                'products': [],
                'market_sentiment': 'Neutral'
            })
            return {'statusCode': 400}
        
        # 1. Send Status to Frontend - EXISTING LOGIC PRESERVED
        send_websocket_message(apigateway_client, connection_id, {
            'type': 'status',
            'message': 'Agent is coordinating: AI agents are analyzing products and market data...'
        })
        
        # 2. Invoke Supervisor Agent in Mumbai - EXISTING LOGIC PRESERVED
        logger.info("🤖 Invoking Bedrock supervisor agent...")
        products, market_sentiment = get_products_via_bedrock(message, user_type)
        
        # 3. Send FINAL result matching index.html logic - EXISTING LOGIC PRESERVED
        response_data = {
            'type': 'result',
            'message': 'Analysis complete',
            'products': products,
            'market_sentiment': market_sentiment
        }
        
        logger.info(f"📤 Sending response with {len(products)} products")
        logger.info(f"📋 Response preview: {json.dumps(response_data, indent=2)}")
        
        send_websocket_message(apigateway_client, connection_id, response_data)
        
        logger.info("✅ Product search completed successfully")
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"💥 Product search error: {str(e)}")
        
        # Error handling - EXISTING LOGIC PRESERVED with enhancements
        try:
            send_websocket_message(apigateway_client, connection_id, {
                'type': 'result', 
                'message': f'Error: {str(e)}', 
                'products': [], 
                'market_sentiment': 'Neutral'
            })
        except Exception as send_error:
            logger.error(f"❌ Failed to send error message: {str(send_error)}")
        
        return {'statusCode': 500}

def get_products_via_bedrock(search_query, user_type):
    """
    Get products via Bedrock - EXISTING LOGIC PRESERVED with robust enhancements
    """
    try:
        logger.info("🚀 Initializing Bedrock client...")
        bedrock_client = boto3.client('bedrock-agent-runtime', region_name='ap-south-1')
        
        # Agent ID for your Mumbai Supervisor - EXISTING LOGIC PRESERVED
        agent_id = 'CSXMF8IQEN'
        agent_alias = 'TSTALIASID'
        
        # Enhanced prompt while preserving core logic
        if user_type == 'retailer':
            # Enhanced prompt for retailer with specific business focus
            input_text = f"""
RETAILER BUSINESS ANALYSIS:
Search Query: {search_query}
User Type: {user_type}

Please analyze "{search_query}" and return a JSON object with:
1. 'products' list containing objects with: name, image_url, stock, ai_score
2. 'market_sentiment' string (Positive/Neutral/Negative)

Focus on business intelligence for retailer dashboard. Ensure ai_score reflects actual AI readiness (use <70 for low scores).

Return only valid JSON format.
            """
        else:
            # Original prompt preserved for customer
            input_text = f"Search for {search_query}. Return a JSON object with a 'products' list (including name, image_url, stock, ai_score) and 'market_sentiment' string."
        
        # Create consistent session ID for better conversation context
        session_id = f"sid_{user_type}_{abs(hash(search_query)) % 1000}"
        
        logger.info(f"🤖 Invoking agent {agent_id} with alias {agent_alias}")
        logger.info(f"📤 Session ID: {session_id}")
        logger.info(f"📝 Input text: {input_text[:200]}...")
        
        # EXISTING BEDROCK INVOCATION LOGIC PRESERVED
        response = bedrock_client.invoke_agent(
            agentId=agent_id, 
            agentAliasId=agent_alias,
            sessionId=session_id, 
            inputText=input_text
        )
        
        logger.info("📡 Bedrock response received, processing...")
        
        # EXISTING RESPONSE PROCESSING LOGIC PRESERVED with enhancements
        result = ""
        chunk_count = 0
        
        for event in response.get('completion', []):
            try:
                if 'chunk' in event and 'bytes' in event['chunk']:
                    chunk_text = event['chunk']['bytes'].decode('utf-8')
                    result += chunk_text
                    chunk_count += 1
                    
                    # Log first few chunks for debugging
                    if chunk_count <= 3:
                        logger.info(f"📝 Chunk {chunk_count}: {chunk_text[:100]}...")
            except Exception as chunk_error:
                logger.warning(f"⚠️ Error processing chunk: {str(chunk_error)}")
                continue
        
        logger.info(f"✅ Bedrock processing complete: {len(result)} characters, {chunk_count} chunks")
        
        if result:
            logger.info(f"📋 Full Bedrock response: {result}")
            
            # Enhanced JSON parsing while preserving existing logic
            try:
                # Try to extract JSON from response
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    clean_json = result[json_start:json_end]
                    logger.info(f"🧹 Extracted JSON: {clean_json}")
                    
                    parsed = json.loads(clean_json)
                    products = parsed.get('products', [])
                    market_sentiment = parsed.get('market_sentiment', 'Neutral')
                    
                    if products:
                        # Validate and enhance product data
                        enhanced_products = []
                        for product in products:
                            enhanced_product = {
                                "name": str(product.get('name', f'Product for {search_query}')),
                                "image_url": str(product.get('image_url', 'https://via.placeholder.com/300x200/607D8B/white?text=Product')),
                                "stock": int(product.get('stock', 0)),
                                "ai_score": max(0, min(100, int(product.get('ai_score', 50))))
                            }
                            enhanced_products.append(enhanced_product)
                        
                        logger.info(f"✅ Successfully parsed {len(enhanced_products)} products from Bedrock")
                        return enhanced_products, market_sentiment
                    else:
                        logger.warning("⚠️ No products in parsed response")
                else:
                    logger.warning("⚠️ No valid JSON structure found")
                    
                # Fallback to original parsing method
                parsed = json.loads(result)
                return parsed.get('products', []), parsed.get('market_sentiment', 'Neutral')
                
            except json.JSONDecodeError as json_error:
                logger.warning(f"⚠️ JSON parse error: {str(json_error)}")
                logger.warning(f"⚠️ Problematic response: {result}")
        else:
            logger.warning("⚠️ Empty response from Bedrock")
        
        # Fallback - EXISTING LOGIC PRESERVED
        logger.info("📦 Using fallback product generation")
        return generate_sample_products(search_query, user_type), "Positive"
        
    except Exception as bedrock_error:
        logger.error(f"💥 Bedrock error: {str(bedrock_error)}")
        logger.error(f"📍 Error type: {type(bedrock_error).__name__}")
        
        # High-quality fallback for UI testing - EXISTING LOGIC PRESERVED
        return generate_sample_products(search_query, user_type), "Positive"

def generate_sample_products(query, user_type='customer'):
    """
    Generate sample products - EXISTING LOGIC PRESERVED with enhancements
    """
    logger.info(f"📦 Generating sample products for '{query}' (user: {user_type})")
    
    # Clean query for better product names
    clean_query = query.strip().title()
    
    if user_type == 'retailer':
        # For retailer - focus on specific product with business metrics
        products = [
            {
                "name": clean_query,
                "image_url": f"https://via.placeholder.com/300x200/FF5722/white?text={query.replace(' ', '+')}",
                "stock": 0,  # Out of stock for Critical Stock KPI
                "ai_score": 67  # Below 70 for Low AI Score KPI
            },
            {
                "name": f"Enhanced {clean_query}",
                "image_url": f"https://via.placeholder.com/300x200/4CAF50/white?text=Enhanced",
                "stock": 5,
                "ai_score": 45  # Low score
            }
        ]
    else:
        # EXISTING CUSTOMER LOGIC PRESERVED with enhancements
        products = [
            {
                "name": f"AI {clean_query} Pro", 
                "image_url": "https://via.placeholder.com/300x200/4CAF50/white?text=AI+Pro", 
                "stock": 0, 
                "ai_score": 42
            },
            {
                "name": f"Smart {clean_query}", 
                "image_url": "https://via.placeholder.com/300x200/2196F3/white?text=Smart+Tool", 
                "stock": 10, 
                "ai_score": 88
            },
            {
                "name": f"Enterprise {clean_query} Solution",
                "image_url": "https://via.placeholder.com/300x200/9C27B0/white?text=Enterprise",
                "stock": 8,
                "ai_score": 76
            }
        ]
    
    logger.info(f"✅ Generated {len(products)} sample products")
    return products

def send_websocket_message(client, cid, msg):
    """
    Send WebSocket message - EXISTING LOGIC PRESERVED with error handling
    """
    try:
        logger.info(f"📤 Sending WebSocket message to {cid}")
        logger.info(f"📋 Message type: {msg.get('type', 'unknown')}")
        
        # Ensure message is properly formatted
        if not isinstance(msg, dict):
            msg = {'type': 'error', 'message': str(msg)}
        
        # Log message content for debugging
        logger.info(f"📊 Message content: {json.dumps(msg, indent=2)}")
        
        # EXISTING SEND LOGIC PRESERVED
        data = json.dumps(msg, ensure_ascii=False, default=str)
        client.post_to_connection(ConnectionId=cid, Data=data)
        
        logger.info(f"✅ WebSocket message sent successfully: {msg.get('type', 'unknown')}")
        
    except client.exceptions.GoneException:
        logger.warning(f"⚠️ Connection {cid} is gone (client disconnected)")
    except Exception as e:
        logger.error(f"❌ Failed to send WebSocket message to {cid}: {str(e)}")
        logger.error(f"📍 Error type: {type(e).__name__}")
        raise
