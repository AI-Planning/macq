# NOTE: This code comes directly from https://github.com/AI-Planning/api-tools
#       The only difference is that checkForDomainPath() is disabled.


import http.client, urllib.request, urllib.parse, urllib.error, json, os, re
import xml.etree.ElementTree as etree

URL = "api.planning.domains"
VERSION = "0.3"

DOMAIN_PATH = False
USER_EMAIL = False
USER_TOKEN = False


def checkForDomainPath():
    """Returns the domain path if one exists and is saved in the settings.xml"""

    return True
    home_dir = os.path.expanduser("~")
    pd_dir = os.path.join(home_dir, ".planning.domains")
    settingsXML = os.path.join(pd_dir, "settings.xml")

    if not os.path.isdir(pd_dir) or not os.path.isfile(settingsXML):
        return False

    installationTree = etree.parse(settingsXML)
    if installationTree is None:
        return False

    installationSettings = installationTree.getroot()
    if installationSettings is None:
        return False

    domainPath = [x for x in installationSettings if x.tag == "domain_path"][0].text
    if not os.path.isdir(domainPath):
        return False

    global DOMAIN_PATH
    global USER_EMAIL
    global USER_TOKEN
    DOMAIN_PATH = domainPath
    if "email" in [x.tag for x in installationSettings]:
        USER_EMAIL = [x for x in installationSettings if x.tag == "email"][0].text
    if "token" in [x.tag for x in installationSettings]:
        USER_TOKEN = [x for x in installationSettings if x.tag == "token"][0].text
    return True


def query(qs, qtype="GET", params={}, offline=False, format="/json"):

    assert not offline, "Error: Offline mode is not supported currently."

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }

    params = urllib.parse.urlencode(params)
    conn = http.client.HTTPConnection(URL)
    conn.request(qtype, format + qs, params, headers)
    response = conn.getresponse()

    data = json.loads(response.read())
    conn.close()

    return data


def update_stat(stat_type, iid, attribute, value, description):

    params = {
        "user": USER_EMAIL,
        "password": USER_TOKEN,
        "key": attribute,
        "value": value,
        "desc": description,
    }

    res = query(
        "/classical/update%s/%d" % (stat_type, iid),
        qtype="POST",
        params=params,
        offline=False,
        format="",
    )

    if res["error"]:
        print("Error: %s" % res["message"])
    else:
        print("Result: %s" % str(res))


def change_tag(tag_type, iid, tid):

    params = {"user": USER_EMAIL, "password": USER_TOKEN, "tag_id": tid}

    res = query(
        "/classical/%s/%d" % (tag_type, iid),
        qtype="POST",
        params=params,
        offline=False,
        format="",
    )

    if res["error"]:
        print("Error: %s" % res["message"])
    else:
        print("Result: %s" % str(res))


def simple_query(qs):
    res = query(qs)
    if res["error"]:
        print("Error: %s" % res["message"])
        return []
    else:
        return res["result"]


def get_version():
    """Return the current API version"""
    return str(query("/version")["version"])


def get_tags():
    """Get the list of available tags"""
    return {t["name"]: t["description"] for t in simple_query("/classical/tags")}


def get_collections(ipc=None):
    """Return the collections, optionally which are IPC or non-IPC"""
    res = query("/classical/collections/")
    if res["error"]:
        print("Error: %s" % res["message"])
        return []
    else:
        if ipc is not None:
            return [x for x in res["result"] if x["ipc"] == ipc]
        else:
            return res["result"]


def get_collection(cid):
    """Return the collection of a given id"""
    return simple_query("/classical/collection/%d" % cid)


def find_collections(name):
    """Find the collections matching the string name"""
    return simple_query("/classical/collections/search?collection_name=%s" % name)


def update_collection_stat(cid, attribute, value, description):
    """Update the attribute stat with a given value and description"""
    update_stat("collection", cid, attribute, value, description)


def tag_collection(cid, tagname):
    """Tag the collection with a given tag"""
    tag2id = {t["name"]: t["id"] for t in simple_query("/classical/tags")}
    if tagname not in tag2id:
        print("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("tagcollection", cid, tag2id[tagname])


def untag_collection(cid, tagname):
    """Remove a given tag from a collection"""
    tag2id = {t["name"]: t["id"] for t in simple_query("/classical/tags")}
    if tagname not in tag2id:
        print("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("untagcollection", cid, tag2id[tagname])


def get_domains(cid):
    """Return the set of domains for a given collection id"""
    return simple_query("/classical/domains/%d" % cid)


def get_domain(did):
    """Return the domain for a given domain id"""
    return simple_query("/classical/domain/%d" % did)


def find_domains(name):
    """Return the domains matching the string name"""
    return simple_query("/classical/domains/search?domain_name=%s" % name)


def update_domain_stat(did, attribute, value, description):
    """Update the attribute stat with a given value and description"""
    update_stat("domain", did, attribute, value, description)


def tag_domain(did, tagname):
    """Tag the domain with a given tag"""
    tag2id = {t["name"]: t["id"] for t in simple_query("/classical/tags")}
    if tagname not in tag2id:
        print("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("tagdomain", did, tag2id[tagname])


def untag_domain(did, tagname):
    """Remove a given tag from a domain"""
    tag2id = {t["name"]: t["id"] for t in simple_query("/classical/tags")}
    if tagname not in tag2id:
        print("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("untagdomain", did, tag2id[tagname])


def get_problems(did):
    """Return the set of problems for a given domain id"""
    return list(map(localize, simple_query("/classical/problems/%d" % did)))


def get_problem(pid):
    """Return the problem for a given problem id"""
    return localize(simple_query("/classical/problem/%d" % pid))


def find_problems(name):
    """Return the problems matching the string name"""
    return list(
        map(localize, simple_query("/classical/problems/search?problem_name=%s" % name))
    )


def update_problem_stat(pid, attribute, value, description):
    """Update the attribute stat with a given value and description"""
    update_stat("problem", pid, attribute, value, description)


def get_null_attribute_problems(attribute):
    """Fetches all of the problems that do not have the attribute set yet"""
    return {
        i["id"]: (i["domain_path"], i["problem_path"])
        for i in map(localize, simple_query("/classical/nullattribute/%s" % attribute))
    }


def tag_problem(pid, tagname):
    """Tag the problem with a given tag"""
    tag2id = {t["name"]: t["id"] for t in simple_query("/classical/tags")}
    if tagname not in tag2id:
        print("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("tagproblem", pid, tag2id[tagname])


def untag_problem(pid, tagname):
    """Remove a given tag from a problem"""
    tag2id = {t["name"]: t["id"] for t in simple_query("/classical/tags")}
    if tagname not in tag2id:
        print("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("untagproblem", pid, tag2id[tagname])


def get_plan(pid):
    """Return the existing plan for a problem if it exists"""
    plan = simple_query("/classical/plan/%d" % pid)["plan"].strip()
    if plan:
        return list(map(str, plan.split("\n")))
    else:
        return None


def submit_plan(pid, plan):
    """Submit the provided plan for validation and possible storage"""

    params = {"plan": plan, "email": USER_EMAIL}

    res = query(
        "/classical/submitplan/%d" % pid,
        qtype="POST",
        params=params,
        offline=False,
        format="",
    )

    if res["error"]:
        print("Error: %s" % res["message"])
    else:
        print("Result: %s" % str(res))


def localize(prob):
    """Convert the relative paths to local ones"""
    if not DOMAIN_PATH:
        return prob

    toRet = {k: prob[k] for k in prob}

    toRet["domain_path"] = os.path.join(DOMAIN_PATH, prob["domain_path"])
    toRet["problem_path"] = os.path.join(DOMAIN_PATH, prob["problem_path"])

    return toRet


if not checkForDomainPath():
    print("\n Warning: No domain path is set\n")

try:
    if VERSION != get_version():
        print(
            "\n Warning: Script version doesn't match API. Do you have the latest version of this file?\n"
        )
except:
    pass
