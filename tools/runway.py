import json, subprocess, sys, time
H=["-H","Authorization: Bearer key_proxyinjected"+"0"*120,"-H","X-Runway-Version: 2024-11-06","-H","Content-Type: application/json"]
B="https://api.dev.runwayml.com/v1"
def call(method, path, body=None):
    a=["curl","-sS","-X",method,B+path]+H
    if body is not None: a+=["--data",json.dumps(body)]
    return json.loads(subprocess.run(a,capture_output=True,text=True).stdout)
def wait(tid):
    while True:
        t=call("GET",f"/tasks/{tid}")
        if t.get("status") in ("SUCCEEDED","FAILED","CANCELLED"): return t
        time.sleep(5)
def run(path, body, out):
    r=call("POST",path,body)
    if "id" not in r: print("ERR",r); return None
    t=wait(r["id"])
    if t["status"]!="SUCCEEDED": print("FAIL",t); return None
    url=t["output"][0]
    p=subprocess.run(["curl","-sS","-o",out,"-w","%{http_code}",url],capture_output=True,text=True)
    print(out, "download", p.stdout, p.stderr[:200]); return url
if __name__=="__main__":
    spec=json.load(open(sys.argv[1])); path=spec.pop("_path"); out=spec.pop("_out")
    u=run(path,spec,out); print("URL",u)
