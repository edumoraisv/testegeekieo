#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, redirect, render_template, request, url_for
import logging
from logging import Formatter, FileHandler
from forms import *
import os

from geekie_api_client import GeekieAPIClient
from geekie_oauth import OAuthClient

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object("config")
app.config["geekie_api_client"] = GeekieAPIClient(
    shared_secret=app.config.get("GEEKIE_API_SHARED_SECRET"),
)

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route("/")
def home():
    return render_template("pages/home.html")


@app.route("/who-am-i", methods=["POST"])
def who_am_i():
    api_client = app.config.get("geekie_api_client")

    remote_organization_id = api_client.who_am_i(request.form["organization_id"]).get(
        "organization_id"
    )

    return redirect(url_for("show_organization", organization_id=remote_organization_id))


@app.route("/organizations/<organization_id>")
def show_organization(organization_id):
    return render_template("pages/show_organization.html", organization_id=organization_id)

@app.route("/organizations/<organization_id>/members")
def list_organization_memberships(organization_id):
    api_client = app.config.get("geekie_api_client")

    api_response = api_client.get_all_memberships(organization_id)
    memberships = api_response["results"]
    oauth_params =  {}

    for membership in memberships:
        oauth_client = OAuthClient(
            shared_secret=app.config.get("GEEKIE_API_SHARED_SECRET"),
            organization_id=organization_id,
            user_id=membership["id"]
        )
        oauth_params[membership["id"]] = oauth_client.get_oauth_params()

    return render_template(
        "pages/members.html",
        organization_id=organization_id,
        memberships=memberships,
        oauth_params=oauth_params,
    )


@app.route("/organizations/<organization_id>/memberships", methods=["POST"])
def create_membership(organization_id):
    api_client = app.config.get("geekie_api_client")

    form_data = request.form

    membership_data = {
        "full_name": form_data["full_name"],
    }

    api_client.create_membership(
        organization_id=organization_id,
        membership_data=membership_data
    )

    return redirect(
        url_for("list_organization_memberships", organization_id=organization_id)
    )


@app.route("/organizations/<organization_id>/memberships/<membership_id>/edit", methods=["GET"])
def edit_membership(organization_id, membership_id):
    api_client = app.config.get("geekie_api_client")

    membership = api_client.get_membership(organization_id, membership_id)

    return render_template(
        "pages/edit_member.html",
        organization_id=organization_id,
        membership_id=membership_id,
        membership=membership,
    )


@app.route("/organizations/<organization_id>/memberships/<membership_id>", methods=["POST"])
def update_membership(organization_id, membership_id):
    api_client = app.config.get("geekie_api_client")
    form_data = request.form

    membership_data = {
        "content_group_ids": [],
        "full_name": form_data["full_name"],
        "roles": form_data["roles"].split(", "),
        "tags": form_data["tags"].split(", "),
        "deleted": form_data.get("deleted", "false"),
        "external_id": form_data.get("external_id", ""),
    }

    api_client.update_membership(
        organization_id=organization_id,
        membership_id=membership_id,
        membership_data=membership_data,
    )

    return redirect(
        url_for("list_organization_memberships", organization_id=organization_id)
    )


# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template("errors/500.html"), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404

if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
"""
