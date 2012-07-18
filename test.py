from busyflow.pivotal import PivotalClient
client = PivotalClient(token='1214d1361ead2de171188a29dc180798', cache=None)
stories = client.stories.all(348467)
