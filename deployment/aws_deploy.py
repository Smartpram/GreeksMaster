"""
AWS Deployment Script for MyBreezeApp
"""
import boto3
import json
import os
import sys
import zipfile
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSDeployer:
    """Deploy MyBreezeApp to AWS"""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.app_name = 'mybreeze-app'
        self.environment_name = 'mybreeze-prod'
        
        # Initialize AWS clients
        try:
            self.eb_client = boto3.client('elasticbeanstalk', region_name=self.region)
            self.s3_client = boto3.client('s3', region_name=self.region)
            self.iam_client = boto3.client('iam', region_name=self.region)
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            sys.exit(1)
    
    def create_deployment_package(self):
        """Create deployment package for Elastic Beanstalk"""
        logger.info("Creating deployment package...")
        
        package_name = 'mybreeze-app-deployment.zip'
        
        with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add application files
            for root, dirs, files in os.walk('.'):
                # Skip unnecessary directories
                if any(skip in root for skip in ['.git', '__pycache__', '.env', 'venv', 'node_modules']):
                    continue
                
                for file in files:
                    if file.endswith(('.pyc', '.pyo', '.DS_Store')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, '.')
                    zipf.write(file_path, arcname)
            
            # Add Elastic Beanstalk configuration
            self._add_eb_config(zipf)
        
        logger.info(f"Deployment package created: {package_name}")
        return package_name
    
    def _add_eb_config(self, zipf):
        """Add Elastic Beanstalk configuration files"""
        # Application configuration
        app_config = {
            "option_settings": [
                {
                    "namespace": "aws:elasticbeanstalk:application:environment",
                    "option_name": "FLASK_ENV",
                    "value": "production"
                },
                {
                    "namespace": "aws:elasticbeanstalk:application:environment",
                    "option_name": "PYTHONPATH",
                    "value": "/var/app/current"
                },
                {
                    "namespace": "aws:elasticbeanstalk:container:python",
                    "option_name": "WSGIPath",
                    "value": "run:app"
                },
                {
                    "namespace": "aws:autoscaling:launchconfiguration",
                    "option_name": "InstanceType",
                    "value": "t3.micro"
                },
                {
                    "namespace": "aws:autoscaling:asg",
                    "option_name": "MinSize",
                    "value": "1"
                },
                {
                    "namespace": "aws:autoscaling:asg",
                    "option_name": "MaxSize",
                    "value": "3"
                }
            ]
        }
        
        # Create .ebextensions directory structure in zip
        zipf.writestr('.ebextensions/01_app.config', 
                     self._create_eb_config_content())
        
        # Add requirements for AWS
        zipf.writestr('requirements_aws.txt', self._get_aws_requirements())
    
    def _create_eb_config_content(self):
        """Create Elastic Beanstalk configuration content"""
        return """
option_settings:
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
    PYTHONPATH: /var/app/current
  aws:elasticbeanstalk:container:python:
    WSGIPath: run:app
  aws:autoscaling:launchconfiguration:
    InstanceType: t3.micro
  aws:autoscaling:asg:
    MinSize: 1
    MaxSize: 3

packages:
  yum:
    gcc: []
    gcc-c++: []
    make: []
    wget: []

commands:
  01_install_talib:
    command: |
      cd /tmp
      wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
      tar -xzf ta-lib-0.4.0-src.tar.gz
      cd ta-lib
      ./configure --prefix=/usr
      make
      sudo make install
      cd ..
      rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

files:
  "/opt/elasticbeanstalk/tasks/bundlelogs.d/mybreeze.conf":
    mode: "000644"
    owner: root
    group: root
    content: |
      /var/app/current/mybreeze.log

container_commands:
  01_migrate:
    command: "python manage.py migrate"
    leader_only: true
"""
    
    def _get_aws_requirements(self):
        """Get requirements for AWS deployment"""
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        # Add AWS-specific requirements
        aws_requirements = requirements + """

# AWS-specific packages
boto3==1.34.14
botocore==1.34.14
awsebcli==3.20.7
"""
        return aws_requirements
    
    def create_s3_bucket(self, bucket_name):
        """Create S3 bucket for application versions"""
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"S3 bucket created: {bucket_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                logger.info(f"S3 bucket already exists: {bucket_name}")
                return True
            else:
                logger.error(f"Failed to create S3 bucket: {e}")
                return False
    
    def upload_to_s3(self, file_path, bucket_name, key):
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(file_path, bucket_name, key)
            logger.info(f"File uploaded to S3: s3://{bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False
    
    def create_application(self):
        """Create Elastic Beanstalk application"""
        try:
            self.eb_client.create_application(
                ApplicationName=self.app_name,
                Description='MyBreezeApp - Algorithmic Trading Platform'
            )
            logger.info(f"Application created: {self.app_name}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidParameterValue':
                logger.info(f"Application already exists: {self.app_name}")
                return True
            else:
                logger.error(f"Failed to create application: {e}")
                return False
    
    def create_application_version(self, version_label, s3_bucket, s3_key):
        """Create application version"""
        try:
            self.eb_client.create_application_version(
                ApplicationName=self.app_name,
                VersionLabel=version_label,
                Description=f'Deployment version {version_label}',
                SourceBundle={
                    'S3Bucket': s3_bucket,
                    'S3Key': s3_key
                }
            )
            logger.info(f"Application version created: {version_label}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create application version: {e}")
            return False
    
    def create_environment(self, version_label):
        """Create Elastic Beanstalk environment"""
        try:
            response = self.eb_client.create_environment(
                ApplicationName=self.app_name,
                EnvironmentName=self.environment_name,
                Description='Production environment for MyBreezeApp',
                VersionLabel=version_label,
                SolutionStackName='64bit Amazon Linux 2 v3.4.0 running Python 3.9',
                OptionSettings=[
                    {
                        'Namespace': 'aws:elasticbeanstalk:application:environment',
                        'OptionName': 'FLASK_ENV',
                        'Value': 'production'
                    },
                    {
                        'Namespace': 'aws:elasticbeanstalk:application:environment',
                        'OptionName': 'DEBUG',
                        'Value': 'False'
                    }
                ]
            )
            
            environment_url = response.get('CNAME')
            logger.info(f"Environment created: {self.environment_name}")
            logger.info(f"Environment URL: http://{environment_url}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create environment: {e}")
            return False
    
    def deploy(self):
        """Main deployment function"""
        logger.info("Starting AWS deployment...")
        
        # Create deployment package
        package_file = self.create_deployment_package()
        
        # Generate version label
        import datetime
        version_label = f"v{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # S3 bucket for deployments
        s3_bucket = f"{self.app_name}-deployments-{self.region}"
        s3_key = f"versions/{version_label}.zip"
        
        try:
            # Create S3 bucket
            if not self.create_s3_bucket(s3_bucket):
                return False
            
            # Upload package to S3
            if not self.upload_to_s3(package_file, s3_bucket, s3_key):
                return False
            
            # Create EB application
            if not self.create_application():
                return False
            
            # Create application version
            if not self.create_application_version(version_label, s3_bucket, s3_key):
                return False
            
            # Create environment
            if not self.create_environment(version_label):
                return False
            
            logger.info("Deployment completed successfully!")
            logger.info(f"Application URL will be available at: http://{self.environment_name}.{self.region}.elasticbeanstalk.com")
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
        
        finally:
            # Cleanup
            if os.path.exists(package_file):
                os.remove(package_file)
                logger.info("Deployment package cleaned up")

def main():
    """Main function"""
    # Check AWS credentials
    try:
        boto3.Session().get_credentials()
    except Exception:
        logger.error("AWS credentials not found. Please configure AWS CLI or set environment variables.")
        sys.exit(1)
    
    # Check required environment variables
    required_vars = ['BREEZE_API_KEY', 'BREEZE_SECRET_KEY', 'BREEZE_USER_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before deployment.")
        sys.exit(1)
    
    # Deploy
    deployer = AWSDeployer()
    success = deployer.deploy()
    
    if success:
        logger.info("🎉 Deployment successful!")
        sys.exit(0)
    else:
        logger.error("❌ Deployment failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()