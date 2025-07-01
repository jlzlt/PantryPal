def boto():
    import boto3
    import os

    # Replace with your actual values
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    region_name = "eu-north-1"
    bucket_name = "pantrypal-media"
    object_key = "media/recipes/test_upload.jpg"  # S3 path

    local_file_path = "media/recipes/008ee6c91e265d2fc3bc22c8920a733128a8a87a3bbff68b18c301ec9f5b02a1.jpg"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

    try:
        with open(local_file_path, "rb") as f:
            s3.upload_fileobj(f, bucket_name, object_key)
        print("Upload successful!")
    except Exception as e:
        print("Upload failed:", e)
