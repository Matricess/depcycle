from pipeline.ingest import read_events


def normalize(source):
    return [event["event"] for event in read_events(source)]
