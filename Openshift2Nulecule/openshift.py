
import requests

class OpenshiftClient(object):
    def __init__(self, url, token, project, api_version="v1"):
        self.url = url
        self.token = token
        self.api_version = api_version
        self.project = project

        self.openshift_api = "{url}/oapi/{version}".format(
                url=self.url,
                version=self.api_version)
        
        self.kube_api = "{url}/api/{version}".format(
                url=self.url,
                version=self.api_version)

        print("openshift_api = %s" % self.openshift_api)
        print("kube_api = %s" % self.kube_api)

        self.kube_resources = self.get_kube_resources()
        self.openshift_resources = self.get_kube_resources()

    def get_kube_resources(self):
        res = self._get(self.kube_api)
        return res.json()["resources"]

    def get_openshift_resources(self):
        res = self._get(self.openshift_api)
        return res.json()["resources"]
    
    def export(self, kind):
        if kind in [r["name"] for r in self.kube_resources]:
            url = self.kube_api
        elif kind in [r["name"] for r in self.openshift_resources]:
            url = self.openshift_api
        else:
            raise Exception("Unknown kind {}".format(kind))

        url += "/namespaces/{namespace}/{kind}".format(
                    namespace=self.project,
                    kind=kind)
        res = self._get(url)
        return res.json()

    def export_all(self):
        """
        !!! only kubernetes things for now
        TODO
        """
        # objects to export
        objects = ["pods",
                   "replicationcontrollers",
                   "persistentvolumeclaims",
                   "services"]

        res = {}
        for o in objects:
            res[o] = self.export(o)

        return res


    def _get(self, url, params=None):
        if not params:
            params = {}

        headers = {"Authorization": "Bearer {0}".format(self.token)}

        requests.packages.urllib3.disable_warnings() 
        return requests.get(url, params=params, headers=headers, verify=False)
