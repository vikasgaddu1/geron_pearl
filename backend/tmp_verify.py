#!/usr/bin/env python3
import urllib.request
import urllib.error
import json

base_url = "http://localhost:8000/api/v1"
body = {
	"reporting_effort_id": 2,
	"item_type": "TLF",
	"item_subtype": "Table",
	"item_code": "T_API_CHECK_003",
	"source_type": "custom"
}

try:
	data = json.dumps(body).encode("utf-8")
	req = urllib.request.Request(
		f"{base_url}/reporting-effort-items/",
		data=data,
		headers={"Content-Type": "application/json"}
	)
	with urllib.request.urlopen(req) as resp:
		print("STATUS", resp.getcode())
		print(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
	print("STATUS", e.code)
	print(e.read().decode("utf-8"))
