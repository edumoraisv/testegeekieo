# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import sha
import hmac
import requests


class GeekieAPIClient:

    def __init__(self, shared_secret):
        self.shared_secret = shared_secret
        self.base_url = "http://api.geekielab.com.br"

    def who_am_i(self, organization_id):
        url = "GET /organizations/{}/who-am-i".format(organization_id)
        headers = self._get_authenticated_headers(url)
        response = requests.get(
            "{}/organizations/{}/who-am-i".format(
                self.base_url,
                organization_id,
            ),
            headers=headers
        )

        if not response.status_code == 200:
            return { "organization_id": "Does not have one" }

        return response.json()

    def get_tag_by_id(self, organization_id, tag_id):
        url = "GET /organizations/{}/tags/{}".format(organization_id, tag_id)
        headers = self._get_authenticated_headers(url)
        response = requests.get(
            "{}/organizations/{}/tags/{}".format(
                self.base_url,
                organization_id,
                tag_id,
            ),
            headers=headers
        )

        if not response.status_code == 200:
            return {}

        return response.json()

    def get_all_memberships(self, organization_id):
        url = "GET /organizations/{}/members/list?limit=200".format(organization_id)
        headers = self._get_authenticated_headers(url)
        response = requests.get(
            "{}/organizations/{}/members/list?limit=200".format(
                self.base_url,
                organization_id,
            ),
            headers=headers
        )

        if not response.status_code == 200:
            return []

        return response.json()

    def get_membership(self, organization_id, membership_id):
        url = "GET /organizations/{}/members/{}?include_deleted=true".format(
            organization_id, membership_id
        )

        headers = self._get_authenticated_headers(url)
        response = requests.get(
            "{}/organizations/{}/members/{}?include_deleted=true".format(
                self.base_url,
                organization_id,
                membership_id,
            ),
            headers=headers
        )

        if not response.status_code == 200:
            return {}

        return response.json()


    def get_membership_by_external_id(self, organization_id, external_id):
        url = "GET /organizations/{}/members/by-external-id/{}?include_deleted=true".format(
            organization_id, external_id
        )

        headers = self._get_authenticated_headers(url)
        response = requests.get(
            "{}/organizations/{}/members/by-external-id/{}?include_deleted=true".format(
                self.base_url,
                organization_id,
                external_id,
            ),
            headers=headers
        )

        if not response.status_code == 200:
            return {}

        return response.json()


    def create_membership(self, organization_id, membership_data):
        url = "POST /organizations/{}/members".format(organization_id)

        request_body = {
            "roles": membership_data.get("roles", ["student"]),
            "tags": membership_data.get("tags", []),
            "full_name": membership_data.get("full_name"),
            "content_group_ids": membership_data.get("content_group_ids", [])
        }

        headers = self._get_authenticated_headers(url, request_body)
        response = requests.post(
            "{}/organizations/{}/members".format(
                self.base_url,
                organization_id,
            ),
            headers=headers,
            data=json.dumps(request_body)
        )

        if not response.status_code == 200 or not response.status_code == 201:
            return {}

        return response.json()

    def update_membership(self, organization_id, membership_id, membership_data):
        url = "PUT /organizations/{}/members/{}".format(organization_id, membership_id)

        # So far this endpoint only works if you try to edit students. For non student roles
        # we should have a "data_access_cases" field instead of "tags".
        request_body = {
            "external_id": membership_data.get("external_id"),
            "roles": membership_data.get("roles", ["student"]),
            "tags": membership_data.get("tags", []),
            "full_name": membership_data.get("full_name"),
            "content_group_ids": membership_data.get("content_group_ids", []),
            "deleted": membership_data.get("deleted", False)
        }

        headers = self._get_authenticated_headers(url, request_body)
        response = requests.put(
            "{}/organizations/{}/members/{}".format(
                self.base_url,
                organization_id,
                membership_id,
            ),
            headers=headers,
            data=json.dumps(request_body)
        )

        if not response.status_code == 200 or not response.status_code == 201:
            return {}

        return response.json()


    def update_membership_by_external_id(self, organization_id, external_id, membership_data):
        url = "PUT /organizations/{}/members/by-external-id/{}".format(organization_id, external_id)

        request_body = {
            "roles": membership_data.get("roles", ["student"]),
            "tags": membership_data.get("tags", []),
            "full_name": membership_data.get("full_name"),
            "content_group_ids": membership_data.get("content_group_ids", []),
        }

        headers = self._get_authenticated_headers(url, request_body)
        response = requests.put(
            "{}/organizations/{}/members/by-external-id/{}".format(
                self.base_url,
                organization_id,
                external_id,
            ),
            headers=headers,
            data=json.dumps(request_body)
        )

        if not response.status_code == 200 or not response.status_code == 201:
            return {}

        return response.json()

    # Most endpoints were doing this authentication to build their headers, so isolating it to a
    # separate method seemed handy.
    def _get_authenticated_headers(self, url, request_body=None):
        current_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        body_as_json = json.dumps(request_body) if request_body else ""
        digest = hashlib.sha1(body_as_json).hexdigest()

        request_representation = url + "\n" + current_time + "\n" + digest + "\n"

        signed_request = hmac.new(
            self.shared_secret,
            request_representation,
            hashlib.sha1
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Geekie-Requested-At": current_time,
            "X-Geekie-Signature": signed_request
        }

        return headers
