import boto3


def add_to_s3(bucket):
    s3 = boto3.client('s3')
    try:
        resp = s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={'LocationConstraint': 'us-west-2'})
    except:
        return False
    else:
        return True
