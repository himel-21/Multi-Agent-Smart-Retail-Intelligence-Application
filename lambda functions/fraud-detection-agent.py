import json
import boto3
import requests
import hashlib
from datetime import datetime, timedelta
import re
import statistics
import os

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sagemaker_runtime = boto3.client('sagemaker-runtime')

# DynamoDB tables
fraud_features_table = dynamodb.Table('FraudDetectionFeatures')
serpapi_cache_table = dynamodb.Table('SerpApiCache')

# Environment variables
SERPAPI_KEY = os.environ['SERPAPI_KEY']
BUCKET_NAME = os.environ['BUCKET_NAME']
FRAUD_ENDPOINT = os.environ['FRAUD_ENDPOINT']

def lambda_handler(event, context):
    """Fraud Detection Agent with SageMaker ML Model"""
    
    try:
        # Extract input parameters
        product_query = event.get('product_query', '')
        transaction_data = event.get('transaction_data', {})
        
        if not product_query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'product_query is required'})
            }
        
        # Step 1: Get SerpApi data
        serpapi_data = get_serpapi_data(product_query)
        
        # Step 2: Extract features for ML model
        ml_features = extract_ml_features(serpapi_data, transaction_data)
        
        # Step 3: Get ML prediction from SageMaker
        ml_prediction = get_sagemaker_prediction(ml_features, FRAUD_ENDPOINT)
        
        # Step 4: Store features and prediction
        store_fraud_analysis(ml_features, ml_prediction)
        
        # Step 5: Generate business recommendations
        recommendations = generate_ml_recommendations(ml_prediction, ml_features)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'agent_type': 'fraud_detection_ml',
                'product_query': product_query,
                'ml_prediction': ml_prediction,
                'risk_level': get_risk_level(ml_prediction['fraud_probability'][0]),
                'confidence': ml_prediction['confidence_score'][0],
                'key_features': get_top_risk_features(ml_prediction.get('feature_importance', {})),
                'recommendations': recommendations,
                'model_version': ml_prediction.get('model_version', 'unknown'),
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def get_serpapi_data(product_query):
    """Get SerpApi data with caching"""
    formatted_query = product_query.replace(' ', '+')
    query_hash = hashlib.md5(f"{formatted_query}_india_fraud".encode()).hexdigest()
    
    # Check cache
    try:
        cached_result = serpapi_cache_table.get_item(Key={'query_hash': query_hash})
        if 'Item' in cached_result and cached_result['Item']['ttl'] > int(datetime.now().timestamp()):
            return cached_result['Item']['data']
    except:
        pass
    
    # Make SerpApi call
    serpapi_url = f"https://serpapi.com/search.json?engine=google_shopping&q={formatted_query}&location=India&hl=en&gl=in&api_key={SERPAPI_KEY}&num=10"
    
    try:
        response = requests.get(serpapi_url, timeout=15)
        response.raise_for_status()
        serpapi_data = response.json()
        
        # Cache result
        serpapi_cache_table.put_item(
            Item={
                'query_hash': query_hash,
                'data': serpapi_data,
                'ttl': int(datetime.now().timestamp()) + 3600,
                'query': product_query,
                'agent_type': 'fraud_ml',
                'created_at': datetime.now().isoformat()
            }
        )
        
        return serpapi_data
        
    except Exception as e:
        print(f"SerpApi error: {e}")
        return {}

def extract_ml_features(serpapi_data, transaction_data):
    """Extract features in the exact format expected by the ML model"""
    
    shopping_results = serpapi_data.get('shopping_results', [])
    
    # Initialize features with defaults
    features = {
        'material_delicacy_score': 0.0,
        'free_return_ratio': 0.0,
        'seller_authenticity_score': 0.5,
        'condition_inconsistency': 0.0,
        'price_variance': 0.0,
        'marketplace_diversity': 1,
        'avg_rating': 4.0,
        'rating_variance': 0.0,
        'thumbnail_availability_ratio': 0.0,
        'return_policy_mentions': 0,
        'unique_product_count': 1,
        'avg_snippet_length': 50.0,
        'new_item_ratio': 1.0,
        'used_item_ratio': 0.0,
        'price_range': 0.0,
        'avg_price': 1000.0
    }
    
    if not shopping_results:
        return features
    
    # Extract actual features from SerpApi data
    delicate_keywords = ['silk', 'cashmere', 'leather', 'suede', 'wool', 'designer', 'premium', 'luxury']
    delicate_count = 0
    snippets = []
    prices = []
    ratings = []
    free_returns = 0
    verified_sellers = 0
    thumbnails = 0
    return_mentions = 0
    new_items = 0
    used_items = 0
    sources = set()
    product_ids = set()
    
    for result in shopping_results:
        # Snippet analysis
        snippet = result.get('snippet', '').lower()
        snippets.append(snippet)
        delicate_count += sum(1 for keyword in delicate_keywords if keyword in snippet)
        
        # Price analysis
        price = result.get('extracted_price', 0)
        if price > 0:
            prices.append(price)
        
        # Rating analysis
        rating = result.get('rating', 0)
        if rating > 0:
            ratings.append(rating)
        
        # Return policy analysis
        extensions = result.get('extensions', [])
        for ext in extensions:
            if 'return' in ext.lower():
                return_mentions += 1
                if 'free' in ext.lower():
                    free_returns += 1
        
        # Seller authenticity
        tag = str(result.get('tag', '')).lower()
        if any(keyword in tag for keyword in ['verified', 'official', 'authorized']):
            verified_sellers += 1
        
        # Visual verification
        if 'thumbnail' in result:
            thumbnails += 1
        
        # Condition analysis
        condition = result.get('second_hand_condition', 'new').lower()
        if 'new' in condition:
            new_items += 1
        elif 'used' in condition or 'refurbished' in condition:
            used_items += 1
        
        # Source diversity
        source = result.get('source', '')
        if source:
            sources.add(source)
        
        # Product ID tracking
        product_id = result.get('product_id', '')
        if product_id:
            product_ids.add(product_id)
    
    # Calculate final features
    total_results = len(shopping_results)
    
    features['material_delicacy_score'] = delicate_count / total_results if total_results > 0 else 0
    features['free_return_ratio'] = free_returns / total_results if total_results > 0 else 0
    features['seller_authenticity_score'] = verified_sellers / total_results if total_results > 0 else 0
    features['thumbnail_availability_ratio'] = thumbnails / total_results if total_results > 0 else 0
    features['return_policy_mentions'] = return_mentions
    features['unique_product_count'] = len(product_ids)
    features['marketplace_diversity'] = len(sources)
    features['new_item_ratio'] = new_items / total_results if total_results > 0 else 0
    features['used_item_ratio'] = used_items / total_results if total_results > 0 else 0
    features['condition_inconsistency'] = abs(features['new_item_ratio'] - features['used_item_ratio'])
    
    if snippets:
        features['avg_snippet_length'] = statistics.mean([len(s) for s in snippets])
    
    if prices:
        features['avg_price'] = statistics.mean(prices)
        features['price_variance'] = statistics.stdev(prices) if len(prices) > 1 else 0
        features['price_range'] = max(prices) - min(prices)
    
    if ratings:
        features['avg_rating'] = statistics.mean(ratings)
        features['rating_variance'] = statistics.stdev(ratings) if len(ratings) > 1 else 0
    
    return features

def get_sagemaker_prediction(features, endpoint_name):
    """Get prediction from SageMaker endpoint"""
    
    try:
        # Prepare payload for SageMaker
        payload = json.dumps(features)
        
        # Invoke SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=payload
        )
        
        # Parse response
        result = json.loads(response['Body'].read().decode())
        return result
        
    except Exception as e:
        print(f"SageMaker prediction error: {e}")
        # Return default prediction if SageMaker fails
        return {
            'fraud_prediction': [0],
            'fraud_probability': [0.1],
            'confidence_score': [0.5],
            'feature_importance': {},
            'model_version': 'fallback'
        }

def store_fraud_analysis(features, prediction):
    """Store analysis results in DynamoDB"""
    
    try:
        item = {
            'product_id': features.get('product_id', f"analysis_{int(datetime.now().timestamp())}"),
            'timestamp': datetime.now().isoformat(),
            'features': features,
            'ml_prediction': prediction,
            'analysis_type': 'fraud_detection_ml'
        }
        
        fraud_features_table.put_item(Item=item)
        
    except Exception as e:
        print(f"Error storing analysis: {e}")

def get_risk_level(fraud_probability):
    """Convert fraud probability to risk level"""
    if fraud_probability >= 0.7:
        return 'HIGH'
    elif fraud_probability >= 0.4:
        return 'MEDIUM'
    else:
        return 'LOW'

def get_top_risk_features(feature_importance):
    """Get top risk contributing features"""
    if not feature_importance:
        return []
    
    # Sort features by importance
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    return [{'feature': k, 'importance': v} for k, v in sorted_features[:5]]

def generate_ml_recommendations(prediction, features):
    """Generate recommendations based on ML prediction"""
    
    fraud_prob = prediction['fraud_probability'][0]
    confidence = prediction['confidence_score'][0]
    
    recommendations = []
    
    if fraud_prob >= 0.8:
        recommendations.append('CRITICAL: Block transaction immediately')
        recommendations.append('Require manual verification and documentation')
        recommendations.append('Flag customer for enhanced monitoring')
    elif fraud_prob >= 0.6:
        recommendations.append('HIGH RISK: Manual review required')
        recommendations.append('Implement additional verification steps')
        recommendations.append('Consider delayed processing')
    elif fraud_prob >= 0.4:
        recommendations.append('MEDIUM RISK: Enhanced monitoring')
        recommendations.append('Apply standard verification procedures')
        recommendations.append('Monitor return patterns')
    else:
        recommendations.append('LOW RISK: Standard processing')
        recommendations.append('Continue normal workflow')
    
    # Add confidence-based recommendations
    if confidence < 0.6:
        recommendations.append('NOTE: Low model confidence - consider human review')
    
    # Feature-specific recommendations
    if features.get('material_delicacy_score', 0) > 0.5:
        recommendations.append('High-value items: Consider no-return policy')
    
    if features.get('free_return_ratio', 0) > 0.8:
        recommendations.append('High return availability: Monitor for abuse patterns')
    
    return recommendations
