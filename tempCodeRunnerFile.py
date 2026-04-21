from weaviate.classes.init import Auth
# ------------------ CONNECT ------------------
client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://gpms6mjcsvuhv9bclfw5cg.c0.asia-southeast1.gcp.weaviate.cloud",
    auth_credentials=Auth.api_key("NmZqQTJYcVRyQ0MyRTJjSV8zdXZZdTlLWG0rMkQ4UjhzdzlVZG5yeW42RFQvcE81SEs4RFo1M2JmYmxRPV92MjAw"),
    skip_init_checks=True
    # print("Connected to:", WEAVIATE_URL)
)