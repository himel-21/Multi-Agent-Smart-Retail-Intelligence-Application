import boto3
import json
import time

def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-south-1')
    
    try:
        start_time = time.time()
        
        # Parse the request body from API Gateway
        if 'body' in event and isinstance(event['body'], str):
            body = json.loads(event['body'])
            query = body.get('query', 'Show me high score electronics')
            user_type = body.get('user_type', 'customer')
        else:
            query = event.get('query', 'Show me high score electronics')
            user_type = event.get('user_type', 'customer')
        
        print(f"Parsed query: {query}, user_type: {user_type}")
        
        # Invoke the Bedrock agent with timeout handling
        print("Invoking Bedrock agent...")
        response = bedrock_agent_runtime.invoke_agent(
            agentId='THNS1L6LHS',
            agentAliasId='VDJZIIKO6U',  # Make sure this is your correct alias ID
            sessionId=f'session-{int(time.time())}',
            inputText=query
        )
        
        print("Processing agent response...")
        result = ""
        chunk_count = 0
        
        for event_chunk in response.get('completion', []):
            chunk_count += 1
            if 'chunk' in event_chunk:
                chunk_data = event_chunk['chunk']
                if 'bytes' in chunk_data:
                    result += chunk_data['bytes'].decode('utf-8')
            
            # Add timeout protection
            if time.time() - start_time > 25:  # Leave 5 seconds buffer
                print("Approaching timeout, returning partial result")
                break
        
        print(f"Processed {chunk_count} chunks in {time.time() - start_time:.2f} seconds")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': result,
                'query': query,
                'user_type': user_type,
                'processing_time': f"{time.time() - start_time:.2f}s",
                'chunks_processed': chunk_count
            })
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process request'
            })
        }
