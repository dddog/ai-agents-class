import vertexai
from vertexai import agent_engines

PROJECT_ID = "gen-lang-client-0539942578"
LOCATION = "asia-northeast1"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
)

# deployments = agent_engines.list()

# for deployment in deployments:
#     print(deployment)

DEPLOYMENT_ID = "projects/203901859150/locations/asia-northeast1/reasoningEngines/3050828107729600512"

SESSION_ID = "2001404182401122304"

remote_app = agent_engines.get(DEPLOYMENT_ID)

remote_app.delete(force=True)


# remote_session = remote_app.create_session(user_id="u_123")

# print(remote_session["id"])

# for event in remote_app.stream_query(
#     user_id="u_123",
#     session_id=SESSION_ID,
#     message="I'm going to Laos, any tips?",
# ):
#     print(event, "\n", "=" * 50)