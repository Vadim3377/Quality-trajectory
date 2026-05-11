from docent.sdk.client import Docent
import json, os

client = Docent(domain='docent.transluce.org')

collections = {
    "claude_opus_high": "b038912e-0133-4594-b093-92806f8ffb17",
    # add the other 4 collection IDs from the Trajs links on swebench.com
}

for model, cid in collections.items():
    ids = client.list_agent_run_ids(cid)
    for run_id in ids:
        run = client.get_agent_run(cid, run_id)
        with open(f"trajs/{model}/{run_id}.json", "w") as f:
            json.dump(run, f)