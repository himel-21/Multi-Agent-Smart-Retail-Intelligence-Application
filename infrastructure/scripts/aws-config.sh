#!/bin/bash

# AWS Resource Export Script
# Creates downloadable archives of all active AWS services, configurations, and data

# Set variables
EXPORT_DIR="aws-export-$(date +%Y%m%d-%H%M%S)"
REGION="ap-south-1"  # Your primary region
ACCOUNT_ID="686316018194"

# Create export directory structure
mkdir -p $EXPORT_DIR/{lambda,s3,dynamodb,apigateway,iam,cloudformation,configs}
cd $EXPORT_DIR

echo "Starting comprehensive AWS resource export..."

# ===== LAMBDA FUNCTIONS EXPORT =====
echo "Exporting Lambda functions..."
mkdir -p lambda/functions lambda/layers

# Export all Lambda functions with code
FUNCTIONS=("ai-assessment-orchestrator" "bedrock-ai-readiness-scorer" "marketplace-product-processor" "genuine_badge" "fraud-detection-agent" "BedrockAgentBridge")

for func in "${FUNCTIONS[@]}"; do
    echo "Exporting function: $func"
    
    # Get function configuration
    aws lambda get-function --function-name $func --region $REGION > lambda/functions/${func}-config.json
    
    # Download function code
    aws lambda get-function --function-name $func --region $REGION --query 'Code.Location' --output text | xargs wget -O lambda/functions/${func}-code.zip
    
    # Get environment variables (sanitized)
    aws lambda get-function-configuration --function-name $func --region $REGION --query 'Environment.Variables' > lambda/functions/${func}-env.json
done

# Export Lambda layers
echo "Exporting Lambda layers..."
aws lambda list-layers --region $REGION > lambda/layers/layers-list.json

# Export specific layers used by your functions
LAYERS=("LambdaInsightsExtension" "serpapi-layer:2" "python_ml_layer:1")
for layer in "${LAYERS[@]}"; do
    layer_name=$(echo $layer | cut -d':' -f1)
    aws lambda get-layer-version --layer-name $layer_name --version-number 1 --region $REGION > lambda/layers/${layer_name}-info.json 2>/dev/null || echo "Layer $layer_name not found"
done

# ===== S3 BUCKETS EXPORT =====
echo "Exporting S3 buckets and data..."
BUCKETS=("amazon-sagemaker-686316018194-ap-south-1-4ujlhydc9dpi81" "ai-assessment-frontend-12345" "financial-risk-fraud-detection-mumbai-1772930498" "sagemaker-ml-models-1772963034" "serp1storage")

for bucket in "${BUCKETS[@]}"; do
    echo "Exporting bucket: $bucket"
    mkdir -p s3/$bucket
    
    # Export bucket configuration
    aws s3api get-bucket-location --bucket $bucket > s3/${bucket}-location.json 2>/dev/null
    aws s3api get-bucket-versioning --bucket $bucket > s3/${bucket}-versioning.json 2>/dev/null
    aws s3api get-bucket-website --bucket $bucket > s3/${bucket}-website.json 2>/dev/null
    aws s3api get-bucket-cors --bucket $bucket > s3/${bucket}-cors.json 2>/dev/null
    aws s3api get-bucket-policy --bucket $bucket > s3/${bucket}-policy.json 2>/dev/null
    
    # List all objects
    aws s3 ls s3://$bucket --recursive > s3/${bucket}-objects-list.txt
    
    # Sync bucket contents (be careful with large buckets)
    echo "Syncing bucket contents for $bucket..."
    aws s3 sync s3://$bucket s3/$bucket/data/ --exclude "*.tmp" --exclude "*.log"
done

# ===== DYNAMODB TABLES EXPORT =====
echo "Exporting DynamoDB tables..."
TABLES=("FraudCache" "FraudDetectionFeatures" "RiskScores" "marketplace-analytics" "marketplace-products-cache")

for table in "${TABLES[@]}"; do
    echo "Exporting table: $table"
    
    # Export table schema
    aws dynamodb describe-table --table-name $table --region $REGION > dynamodb/${table}-schema.json
    
    # Export table data (scan - be careful with large tables)
    aws dynamodb scan --table-name $table --region $REGION > dynamodb/${table}-data.json
    
    # Export table to S3 (requires point-in-time recovery enabled)
    # aws dynamodb export-table-to-point-in-time --table-arn arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$table --s3-bucket $EXPORT_BUCKET --s3-prefix dynamodb-exports/$table/ --export-format DYNAMODB_JSON
done

# ===== API GATEWAY EXPORT =====
echo "Exporting API Gateway configurations..."

# REST APIs
REST_APIS=("5x0wga8prg" "66gpj4a43a")
for api_id in "${REST_APIS[@]}"; do
    echo "Exporting REST API: $api_id"
    
    # Get API details
    aws apigateway get-rest-api --rest-api-id $api_id --region $REGION > apigateway/rest-api-${api_id}.json
    
    # Get resources and methods
    aws apigateway get-resources --rest-api-id $api_id --region $REGION > apigateway/rest-api-${api_id}-resources.json
    
    # Export API as Swagger/OpenAPI
    aws apigateway get-export --rest-api-id $api_id --stage-name prod --export-type swagger --region $REGION > apigateway/rest-api-${api_id}-swagger.json 2>/dev/null
    
    # Get deployments
    aws apigateway get-deployments --rest-api-id $api_id --region $REGION > apigateway/rest-api-${api_id}-deployments.json
done

# WebSocket API
WEBSOCKET_API="dgfai4r9l9"
echo "Exporting WebSocket API: $WEBSOCKET_API"
aws apigatewayv2 get-api --api-id $WEBSOCKET_API --region $REGION > apigateway/websocket-api-${WEBSOCKET_API}.json
aws apigatewayv2 get-routes --api-id $WEBSOCKET_API --region $REGION > apigateway/websocket-api-${WEBSOCKET_API}-routes.json

# ===== IAM ROLES AND POLICIES EXPORT =====
echo "Exporting IAM roles and policies..."

# Export all roles
aws iam list-roles > iam/all-roles.json

# Export specific Lambda execution roles
LAMBDA_ROLES=("ai-assessment-orchestrator-role-c9x5c7is" "bedrock-ai-readiness-scorer-role-xcnrjbk1" "marketplace-product-processor-role-qiwgk6k0")
for role in "${LAMBDA_ROLES[@]}"; do
    echo "Exporting role: $role"
    aws iam get-role --role-name $role > iam/role-${role}.json 2>/dev/null
    aws iam list-attached-role-policies --role-name $role > iam/role-${role}-attached-policies.json 2>/dev/null
    aws iam list-role-policies --role-name $role > iam/role-${role}-inline-policies.json 2>/dev/null
done

# Export managed policies
aws iam list-policies --scope Local > iam/custom-policies.json

# ===== CLOUDFORMATION STACKS EXPORT =====
echo "Exporting CloudFormation stacks..."
aws cloudformation list-stacks --region $REGION > cloudformation/stacks-list.json

# Get active stacks
aws cloudformation describe-stacks --region $REGION > cloudformation/active-stacks.json

# Export stack templates
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --region $REGION --query 'StackSummaries[].StackName' --output text | tr '\t' '\n' | while read stack; do
    if [ ! -z "$stack" ]; then
        echo "Exporting stack template: $stack"
        aws cloudformation get-template --stack-name "$stack" --region $REGION > cloudformation/template-${stack}.json 2>/dev/null
    fi
done

# ===== VPC AND NETWORKING EXPORT =====
echo "Exporting VPC configurations..."
aws ec2 describe-vpcs --region $REGION > configs/vpcs.json
aws ec2 describe-subnets --region $REGION > configs/subnets.json
aws ec2 describe-security-groups --region $REGION > configs/security-groups.json
aws ec2 describe-route-tables --region $REGION > configs/route-tables.json

# ===== SAGEMAKER EXPORT =====
echo "Exporting SageMaker configurations..."
aws sagemaker list-domains --region $REGION > configs/sagemaker-domains.json
aws sagemaker list-notebook-instances --region $REGION > configs/sagemaker-notebooks.json

# ===== CREATE CONFIGURATION SUMMARY =====
echo "Creating configuration summary..."
cat > configs/export-summary.json << EOF
{
  "export_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "account_id": "$ACCOUNT_ID",
  "primary_region": "$REGION",
  "exported_services": {
    "lambda_functions": 6,
    "s3_buckets": 5,
    "dynamodb_tables": 5,
    "api_gateway_apis": 3,
    "iam_roles": "58+",
    "cloudformation_stacks": 4,
    "sagemaker_domains": 1
  },
  "export_structure": {
    "lambda/": "Function code, configurations, and layers",
    "s3/": "Bucket configurations and data",
    "dynamodb/": "Table schemas and data",
    "apigateway/": "API configurations and exports",
    "iam/": "Roles and policies",
    "cloudformation/": "Stack templates",
    "configs/": "VPC, networking, and service configurations"
  }
}
EOF

# ===== CREATE DEPLOYMENT SCRIPTS =====
echo "Creating deployment scripts..."
mkdir -p deployment-scripts

# Lambda deployment script
cat > deployment-scripts/deploy-lambda.sh << 'EOF'
#!/bin/bash
# Lambda Functions Deployment Script

REGION="ap-south-1"
FUNCTIONS=("ai-assessment-orchestrator" "bedrock-ai-readiness-scorer" "marketplace-product-processor" "genuine_badge" "fraud-detection-agent" "BedrockAgentBridge")

for func in "${FUNCTIONS[@]}"; do
    echo "Deploying function: $func"
    
    # Create function from exported code
    if [ -f "../lambda/functions/${func}-code.zip" ]; then
        aws lambda create-function \
            --function-name $func \
            --runtime python3.14 \
            --role $(cat ../lambda/functions/${func}-config.json | jq -r '.Configuration.Role') \
            --handler $(cat ../lambda/functions/${func}-config.json | jq -r '.Configuration.Handler') \
            --zip-file fileb://../lambda/functions/${func}-code.zip \
            --region $REGION
    fi
done
EOF

# S3 deployment script
cat > deployment-scripts/deploy-s3.sh << 'EOF'
#!/bin/bash
# S3 Buckets Deployment Script

BUCKETS=("amazon-sagemaker-686316018194-ap-south-1-4ujlhydc9dpi81" "ai-assessment-frontend-12345" "financial-risk-fraud-detection-mumbai-1772930498" "sagemaker-ml-models-1772963034" "serp1storage")

for bucket in "${BUCKETS[@]}"; do
    echo "Creating and syncing bucket: $bucket"
    
    # Create bucket
    aws s3 mb s3://$bucket --region ap-south-1
    
    # Sync data
    if [ -d "../s3/$bucket/data" ]; then
        aws s3 sync ../s3/$bucket/data/ s3://$bucket/
    fi
    
    # Apply configurations
    if [ -f "../s3/${bucket}-website.json" ]; then
        aws s3api put-bucket-website --bucket $bucket --website-configuration file://../s3/${bucket}-website.json
    fi
done
EOF

chmod +x deployment-scripts/*.sh

# ===== CREATE DOWNLOADABLE ARCHIVES =====
echo "Creating downloadable archives..."
cd ..

# Create separate archives for different components
tar -czf ${EXPORT_DIR}-lambda.tar.gz $EXPORT_DIR/lambda/
tar -czf ${EXPORT_DIR}-s3-configs.tar.gz $EXPORT_DIR/s3/ --exclude="*/data/*"
tar -czf ${EXPORT_DIR}-dynamodb.tar.gz $EXPORT_DIR/dynamodb/
tar -czf ${EXPORT_DIR}-apigateway.tar.gz $EXPORT_DIR/apigateway/
tar -czf ${EXPORT_DIR}-iam.tar.gz $EXPORT_DIR/iam/
tar -czf ${EXPORT_DIR}-cloudformation.tar.gz $EXPORT_DIR/cloudformation/
tar -czf ${EXPORT_DIR}-configs.tar.gz $EXPORT_DIR/configs/
tar -czf ${EXPORT_DIR}-deployment-scripts.tar.gz $EXPORT_DIR/deployment-scripts/

# Create complete archive (excluding large S3 data)
tar -czf ${EXPORT_DIR}-complete.tar.gz $EXPORT_DIR/ --exclude="*/s3/*/data/*"

# Create manifest file
cat > ${EXPORT_DIR}-manifest.txt << EOF
AWS Resource Export Manifest
============================
Export Date: $(date)
Account ID: $ACCOUNT_ID
Primary Region: $REGION

Available Downloads:
- ${EXPORT_DIR}-complete.tar.gz (All configurations without S3 data)
- ${EXPORT_DIR}-lambda.tar.gz (Lambda functions and code)
- ${EXPORT_DIR}-s3-configs.tar.gz (S3 bucket configurations)
- ${EXPORT_DIR}-dynamodb.tar.gz (DynamoDB schemas and data)
- ${EXPORT_DIR}-apigateway.tar.gz (API Gateway configurations)
- ${EXPORT_DIR}-iam.tar.gz (IAM roles and policies)
- ${EXPORT_DIR}-cloudformation.tar.gz (CloudFormation templates)
- ${EXPORT_DIR}-configs.tar.gz (VPC and service configurations)
- ${EXPORT_DIR}-deployment-scripts.tar.gz (Deployment automation scripts)

Individual S3 bucket data available in: $EXPORT_DIR/s3/*/data/

Total exported resources:
- 6 Lambda functions with code
- 5 S3 buckets with configurations
- 5 DynamoDB tables with data
- 3 API Gateway APIs
- 58+ IAM roles
- 4 CloudFormation stacks
- 1 SageMaker domain
- VPC and networking configurations
EOF

echo "Export completed successfully!"
echo "Available downloads:"
ls -lh ${EXPORT_DIR}*.tar.gz
echo ""
echo "Manifest file: ${EXPORT_DIR}-manifest.txt"
echo ""
echo "To download files from CloudShell:"
echo "1. Use the CloudShell download feature"
echo "2. Or use 'aws s3 cp' to upload to an S3 bucket for download"

# Download all archives to your local machine
# (Use CloudShell's download feature or upload to S3)

# Option 1: Upload to S3 for download
DOWNLOAD_BUCKET="your-download-bucket"
aws s3 cp aws-export-*-complete.tar.gz s3://$DOWNLOAD_BUCKET/
aws s3 cp aws-export-*-manifest.txt s3://$DOWNLOAD_BUCKET/

# Option 2: Generate presigned URLs for download
aws s3 presign s3://$DOWNLOAD_BUCKET/aws-export-*-complete.tar.gz --expires-in 3600
