
import http.client, urllib.parse, json, os
import xml.etree.ElementTree as etree

URL = 'api.planning.domains'
VERSION = '0.5'

DOMAIN_PATH = False
USER_EMAIL = False
USER_TOKEN = False

def checkForDomainPath():
    """Returns the domain path if one exists and is saved in the settings.xml"""

    home_dir = os.path.expanduser("~")
    pd_dir = os.path.join(home_dir,".planning.domains")
    settingsXML = os.path.join(pd_dir,"settings.xml")

    if not os.path.isdir(pd_dir) or not os.path.isfile(settingsXML):
        return False

    installationTree = etree.parse(settingsXML)
    if installationTree is None:
        return False

    installationSettings = installationTree.getroot()
    if installationSettings is None:
        return False

    domainPath = str(list(filter(lambda x: x.tag == 'domain_path', installationSettings))[0].text)
    if not os.path.isdir(domainPath):
        return False

    global DOMAIN_PATH
    global USER_EMAIL
    global USER_TOKEN
    DOMAIN_PATH = domainPath
    if 'email' in [x.tag for x in installationSettings]:
        USER_EMAIL = list(filter(lambda x: x.tag == 'email', installationSettings))[0].text
    if 'token' in [x.tag for x in installationSettings]:
        USER_TOKEN = list(filter(lambda x: x.tag == 'token', installationSettings))[0].text
    return True

def query(qs, formalism, qtype="GET", params={}, offline=False, format='/json'):

    assert not offline, "Error: Offline mode is not supported currently."

    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    params = urllib.parse.urlencode(params)
    conn = http.client.HTTPSConnection(URL)
    if formalism == "":
        conn.request(qtype, f"{format}/{qs}", params, headers)
    else:
        conn.request(qtype, f"{format}/{formalism}/{qs}", params, headers)
    response = conn.getresponse()
    tmp = response.read().decode('utf-8')
    if "<pre>Payload Too Large</pre>" in tmp:
        data = { "error": True, "message": "Payload too large."}
    else:
        try:
            data = json.loads(tmp)
        except:
            data = { "error": True, "message": f"Invalid JSON response:\n{tmp}"}
    conn.close()

    return data

def simple_query(qs, formalism):
    res = query(qs, formalism)
    if res['error']:
        print ("Error: %s" % res['message'])
        return []
    else:
        return res['result']

def update_stat(stat_type, iid, attribute, value, description, formalism):

    params = {'user': USER_EMAIL,
              'password': USER_TOKEN,
              'key': attribute,
              'value': value,
              'desc': description}

    res = query("update%s/%d" % (stat_type, iid),
                formalism,
                qtype='POST',
                params=params,
                offline=False,
                format='')

    if res['error']:
        print ("Error: %s" % res['message'])
    else:
        print ("Result: %s" % str(res))

def change_tag(tag_type, iid, tid, formalism):

    params = {'user': USER_EMAIL,
              'password': USER_TOKEN,
              'tag_id': tid}

    res = query("%s/%d" % (tag_type, iid),
                formalism,
                qtype='POST',
                params=params,
                offline=False,
                format='')

    if res['error']:
        print ("Error: %s" % res['message'])
    else:
        print ("Result: %s" % str(res))

def create_collection(name, description, tags, ipc, formalism):

    params = {'user': USER_EMAIL,
              'password': USER_TOKEN,
              'formalism': formalism,
              'name': name,
              'ipc': ipc,
              'desc': description,
              'tags': tags,
    }
    path = f"{formalism}/collection"
    res = query(path,
          formalism,
          qtype='POST',
          params = params,
          offline=False
          )

    if res['error']:
        print ("Error: %s" % res['message'])
        return []
    else:
        print ("Result: %s" % str(res))
        return res['result']


def get_version():
    """Return the current API version"""
    return str(query('version', "")['version'])


def get_tags(formalism):
    """Get the list of available tags"""
    return {t['name']: t['description'] for t in simple_query("tags", formalism)}


def get_collections(formalism, ipc = None):
    """Return the collections, optionally which are IPC or non-IPC"""
    res = query('collections/', formalism)
    if res['error']:
        print ("Error: %s" % res['message'])
        return []
    else:
        if ipc is not None:
            return list(filter(lambda x: x['ipc'] == ipc, res['result']))
        else:
            return res['result']

def get_collection(cid, formalism):
    """Return the collection of a given id"""
    return simple_query("collection/%d" % cid, formalism)

def find_collections(name, formalism):
    """Find the collections matching the string name"""
    return simple_query("collections/search?collection_name=%s" % name, formalism)

def update_collection_stat(cid, attribute, value, description, formalism):
    """Update the attribute stat with a given value and description"""
    update_stat('collection', cid, attribute, value, description, formalism)

def tag_collection(cid, tagname, formalism):
    """Tag the collection with a given tag"""
    tag2id = {t['name']: t['id'] for t in simple_query("tags", formalism)}
    if tagname not in tag2id:
        print ("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("tagcollection", cid, tag2id[tagname], formalism)

def untag_collection(cid, tagname, formalism):
    """Remove a given tag from a collection"""
    tag2id = {t['name']: t['id'] for t in simple_query("tags", formalism)}
    if tagname not in tag2id:
        print ("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("untagcollection", cid, tag2id[tagname], formalism)



def get_domains(cid, formalism):
    """Return the set of domains for a given collection id"""
    return simple_query("domains/%d" % cid, formalism)

def get_domain(did, formalism):
    """Return the domain for a given domain id"""
    return simple_query("domain/%d" % did, formalism)

def find_domains(name, formalism):
    """Return the domains matching the string name"""
    return simple_query("domains/search?domain_name=%s" % name, formalism)

def update_domain_stat(did, attribute, value, description, formalism):
    """Update the attribute stat with a given value and description"""
    update_stat('domain', did, attribute, value, description, formalism)

def tag_domain(did, tagname, formalism):
    """Tag the domain with a given tag"""
    tag2id = {t['name']: t['id'] for t in simple_query("tags", formalism)}
    if tagname not in tag2id:
        print ("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("tagdomain", did, tag2id[tagname], formalism)

def untag_domain(did, tagname, formalism):
    """Remove a given tag from a domain"""
    tag2id = {t['name']: t['id'] for t in simple_query("tags", formalism)}
    if tagname not in tag2id:
        print ("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("untagdomain", did, tag2id[tagname], formalism)


def get_problems(did, formalism):
    """Return the set of problems for a given domain id"""
    return map(localize, simple_query("problems/%d" % did, formalism))

def get_problem(pid, formalism):
    """Return the problem for a given problem id"""
    return localize(simple_query("problem/%d" % pid, formalism))

def find_problems(name, formalism):
    """Return the problems matching the string name"""
    return list(map(localize, simple_query("problems/search?problem_name=%s" % name, formalism)))

def update_problem_stat(pid, attribute, value, description, formalism):
    """Update the attribute stat with a given value and description"""
    update_stat('problem', pid, attribute, value, description, formalism)

def get_null_attribute_problems(attribute, formalism):
    """Fetches all of the problems that do not have the attribute set yet"""
    return {i['id']: (i['domain_path'], i['problem_path'])
            for i in map(localize, simple_query("nullattribute/%s" % attribute, formalism))}

def tag_problem(pid, tagname, formalism):
    """Tag the problem with a given tag"""
    tag2id = {t['name']: t['id'] for t in simple_query("tags", formalism)}
    if tagname not in tag2id:
        print ("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("tagproblem", pid, tag2id[tagname], formalism)

def untag_problem(pid, tagname, formalism):
    """Remove a given tag from a problem"""
    tag2id = {t['name']: t['id'] for t in simple_query("tags", formalism)}
    if tagname not in tag2id:
        print ("Error: Tag %s does not exist" % tagname)
    else:
        change_tag("untagproblem", pid, tag2id[tagname], formalism)

def get_plan(pid, formalism):
    """Return the existing plan for a problem if it exists"""
    res = simple_query("plan/%d" % pid, formalism)
    if res:
        return res['plan'].strip()
    return res


def submit_plan(pid, plan, formalism):
    """Submit the provided plan for validation and possible storage"""

    params = {'plan': plan, 'email': USER_EMAIL}

    res = query("submitplan/%d" % pid,
                formalism,
                qtype='POST',
                params=params,
                offline=False,
                format='')
    if res['error']:
        print ("Error: %s" % res['message'])
    else:
        print ("Result: %s" % str(res))


def localize(prob):
    """Convert the relative paths to local ones"""
    if not DOMAIN_PATH:
        return prob

    toRet = {k:prob[k] for k in prob}

    pathKeys = ['domain_path', 'problem_path']
    for key in pathKeys:
        if key in toRet:
            toRet[key] = os.path.join(DOMAIN_PATH, prob[key])

    return toRet


def generate_lab_suite(cid, formalism):
    """Uses the lab API to generate a suite of problems in a collection"""
    try:
        from downward.suites import Problem
    except:
        print ("\n Error: Lab does not seem to be installed ( https://lab.readthedocs.io/ )\n")
        return

    SUITE = []
    for d in get_domains(cid, formalism):
        for p in get_problems(d['domain_id'], formalism):
            SUITE.append(Problem(p['domain'], p['problem'],
                                 domain_file = p['domain_path'],
                                 problem_file = p['problem_path'],
                                 properties = {'api_problem_id': p['problem_id']}))
    return SUITE


if not checkForDomainPath():
    print ("\n Warning: No domain path is set\n")

try:
    if VERSION != get_version():
        print (f"\n Warning: Script version ({VERSION}) doesn't match API ({get_version()}). Do you have the latest version of this file?\n")
except:
    pass
