from docent.sdk.client import Docent
import json
import os

client = Docent(domain="docent.transluce.org")

collections = {
    "claude-4-5-opus-high": "b038912e-0133-4594-b093-92806f8ffb17",
    "gemini-3-flash-high": "1ebbdd7a-55b3-4015-9b83-5978cc7fb618",
    "minimax-2-5-high": "5b77e003-7328-4003-879e-9b55dd3a0b6f",
    "claude-4-6-opus": "9243cc78-d399-402f-be97-e366ff63282c",
    "gpt-5-2-codex": "fb22a2e4-0a41-4d41-8e1e-388d4cb50d80",
}


def to_jsonable(obj):
    """
    Convert Docent SDK objects into JSON-serialisable Python objects.
    Handles Pydantic-style models, dataclasses/objects, lists, and dicts.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, list):
        return [to_jsonable(item) for item in obj]

    if isinstance(obj, tuple):
        return [to_jsonable(item) for item in obj]

    if isinstance(obj, dict):
        return {str(key): to_jsonable(value) for key, value in obj.items()}

    if hasattr(obj, "model_dump"):
        return to_jsonable(obj.model_dump())

    if hasattr(obj, "dict"):
        return to_jsonable(obj.dict())

    if hasattr(obj, "__dict__"):
        return {
            key: to_jsonable(value)
            for key, value in vars(obj).items()
            if not key.startswith("_")
        }

    return str(obj)


for model, collection_id in collections.items():
    output_dir = os.path.join("experiments_for_task2", model)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading runs for {model}...")
    run_ids = client.list_agent_run_ids(collection_id)
    print(f"Found {len(run_ids)} runs")

    for i, run_id in enumerate(run_ids, start=1):
        output_path = os.path.join(output_dir, f"{run_id}.json")

        if os.path.exists(output_path):
            print(f"[{i}/{len(run_ids)}] Skipping existing: {output_path}")
            continue

        run = client.get_agent_run(collection_id, run_id)
        run_json = to_jsonable(run)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(run_json, f, indent=2, ensure_ascii=False)

        print(f"[{i}/{len(run_ids)}] Saved {output_path}")