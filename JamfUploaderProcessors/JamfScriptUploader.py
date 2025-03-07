#!/usr/local/autopkg/python

"""
JamfScriptUploader processor for uploading items to Jamf Pro using AutoPkg
    by G Pugh
"""

import os.path
import sys

from time import sleep
from autopkglib import ProcessorError  # pylint: disable=import-error

# to use a base module in AutoPkg we need to add this path to the sys.path.
# this violates flake8 E402 (PEP8 imports) but is unavoidable, so the following
# imports require noqa comments for E402
sys.path.insert(0, os.path.dirname(__file__))

from JamfUploaderLib.JamfUploaderBase import JamfUploaderBase  # noqa: E402

__all__ = ["JamfScriptUploader"]


class JamfScriptUploader(JamfUploaderBase):
    description = (
        "A processor for AutoPkg that will upload a script to a Jamf Cloud or "
        "on-prem server."
    )
    input_variables = {
        "JSS_URL": {
            "required": True,
            "description": "URL to a Jamf Pro server that the API user has write access "
            "to, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_USERNAME": {
            "required": True,
            "description": "Username of account with appropriate access to "
            "jss, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_PASSWORD": {
            "required": True,
            "description": "Password of api user, optionally set as a key in "
            "the com.github.autopkg preference file.",
        },
        "script_path": {
            "required": False,
            "description": "Full path to the script to be uploaded",
        },
        "script_name": {
            "required": False,
            "description": "Name of the script in Jamf",
        },
        "script_category": {
            "required": False,
            "description": "Script category",
            "default": "",
        },
        "script_priority": {
            "required": False,
            "description": "Script priority (BEFORE or AFTER)",
            "default": "AFTER",
        },
        "osrequirements": {
            "required": False,
            "description": "Script OS requirements",
            "default": "",
        },
        "script_info": {
            "required": False,
            "description": "Script info field",
            "default": "",
        },
        "script_notes": {
            "required": False,
            "description": "Script notes field",
            "default": "",
        },
        "script_parameter4": {
            "required": False,
            "description": "Script parameter 4 title",
            "default": "",
        },
        "script_parameter5": {
            "required": False,
            "description": "Script parameter 5 title",
            "default": "",
        },
        "script_parameter6": {
            "required": False,
            "description": "Script parameter 6 title",
            "default": "",
        },
        "script_parameter7": {
            "required": False,
            "description": "Script parameter 7 title",
            "default": "",
        },
        "script_parameter8": {
            "required": False,
            "description": "Script parameter 8 title",
            "default": "",
        },
        "script_parameter9": {
            "required": False,
            "description": "Script parameter 9 title",
            "default": "",
        },
        "script_parameter10": {
            "required": False,
            "description": "Script parameter 10 title",
            "default": "",
        },
        "script_parameter11": {
            "required": False,
            "description": "Script parameter 11 title",
            "default": "",
        },
        "replace_script": {
            "required": False,
            "description": "Overwrite an existing script if True.",
            "default": False,
        },
        "sleep": {
            "required": False,
            "description": "Pause after running this processor for specified seconds.",
            "default": "0",
        },
    }

    output_variables = {
        "script_name": {
            "required": False,
            "description": "Name of the uploaded script",
        },
        "jamfscriptuploader_summary_result": {
            "description": "Description of interesting results.",
        },
    }

    def upload_script(
        self,
        jamf_url,
        script_name,
        script_path,
        category_id,
        script_category,
        script_info,
        script_notes,
        script_priority,
        script_parameter4,
        script_parameter5,
        script_parameter6,
        script_parameter7,
        script_parameter8,
        script_parameter9,
        script_parameter10,
        script_parameter11,
        script_os_requirements,
        token,
        obj_id=0,
    ):
        """Update script metadata."""

        # import script from file and replace any keys in the script
        if os.path.exists(script_path):
            with open(script_path, "r") as file:
                script_contents = file.read()
        else:
            raise ProcessorError("Script does not exist!")

        # substitute user-assignable keys
        script_contents = self.substitute_assignable_keys(script_contents)

        # priority has to be in upper case. Let's make it nice for the user
        if script_priority:
            script_priority = script_priority.upper()

        # build the object
        script_data = {
            "name": script_name,
            "info": script_info,
            "notes": script_notes,
            "priority": script_priority,
            "categoryId": category_id,
            "categoryName": script_category,
            "parameter4": script_parameter4,
            "parameter5": script_parameter5,
            "parameter6": script_parameter6,
            "parameter7": script_parameter7,
            "parameter8": script_parameter8,
            "parameter9": script_parameter9,
            "parameter10": script_parameter10,
            "parameter11": script_parameter11,
            "osRequirements": script_os_requirements,
            "scriptContents": script_contents,
        }

        self.output(
            "Script data:",
            verbose_level=2,
        )
        self.output(
            script_data,
            verbose_level=2,
        )

        script_json = self.write_json_file(script_data)

        self.output("Uploading script..")

        # if we find an object ID we put, if not, we post
        object_type = "script"
        if obj_id:
            url = "{}/{}/{}".format(jamf_url, self.api_endpoints(object_type), obj_id)
        else:
            url = "{}/{}".format(jamf_url, self.api_endpoints(object_type))

        count = 0
        while True:
            count += 1
            self.output(
                "Script upload attempt {}".format(count),
                verbose_level=2,
            )
            request = "PUT" if obj_id else "POST"
            r = self.curl(request=request, url=url, token=token, data=script_json)
            # check HTTP response
            if self.status_check(r, "Script", script_name, request) == "break":
                break
            if count > 5:
                self.output("Script upload did not succeed after 5 attempts")
                self.output("\nHTTP POST Response Code: {}".format(r.status_code))
                raise ProcessorError("ERROR: Script upload failed ")
            if int(self.sleep) > 30:
                sleep(int(self.sleep))
            else:
                sleep(30)
        return r

    def main(self):
        """Do the main thing here"""
        self.jamf_url = self.env.get("JSS_URL")
        self.jamf_user = self.env.get("API_USERNAME")
        self.jamf_password = self.env.get("API_PASSWORD")
        self.script_path = self.env.get("script_path")
        self.script_name = self.env.get("script_name")
        self.script_category = self.env.get("script_category")
        self.script_priority = self.env.get("script_priority")
        self.osrequirements = self.env.get("osrequirements")
        self.script_info = self.env.get("script_info")
        self.script_notes = self.env.get("script_notes")
        self.script_parameter4 = self.env.get("script_parameter4")
        self.script_parameter5 = self.env.get("script_parameter5")
        self.script_parameter6 = self.env.get("script_parameter6")
        self.script_parameter7 = self.env.get("script_parameter7")
        self.script_parameter8 = self.env.get("script_parameter8")
        self.script_parameter9 = self.env.get("script_parameter9")
        self.script_parameter10 = self.env.get("script_parameter10")
        self.script_parameter11 = self.env.get("script_parameter11")
        self.replace = self.env.get("replace_script")
        self.sleep = self.env.get("sleep")
        # handle setting replace in overrides
        if not self.replace or self.replace == "False":
            self.replace = False

        # clear any pre-existing summary result
        if "jamfscriptuploader_summary_result" in self.env:
            del self.env["jamfscriptuploader_summary_result"]
        script_uploaded = False

        # obtain the relevant credentials
        token = self.handle_uapi_auth(self.jamf_url, self.jamf_user, self.jamf_password)

        # get the id for a category if supplied
        if self.script_category:
            self.output("Checking categories for {}".format(self.script_category))

            # check for existing category - requires obj_name
            obj_type = "category"
            obj_name = self.script_category
            category_id = self.get_uapi_obj_id_from_name(
                self.jamf_url,
                obj_type,
                obj_name,
                token,
            )

            if not category_id:
                self.output("WARNING: Category not found!")
                category_id = "-1"
            else:
                self.output(
                    "Category {} found: ID={}".format(self.script_category, category_id)
                )
        else:
            self.script_category = ""
            category_id = "-1"

        # handle files with no path
        if "/" not in self.script_path:
            found_template = self.get_path_to_file(self.script_path)
            if found_template:
                self.script_path = found_template
            else:
                raise ProcessorError(f"ERROR: Script file {self.script_path} not found")

        # now start the process of uploading the object
        if not self.script_name:
            self.script_name = os.path.basename(self.script_path)

        # check for existing script
        self.output(
            "Checking for existing '{}' on {}".format(self.script_name, self.jamf_url)
        )
        self.output(
            "Full path: {}".format(self.script_path),
            verbose_level=2,
        )
        obj_type = "script"
        obj_name = self.script_name
        obj_id = self.get_uapi_obj_id_from_name(
            self.jamf_url,
            obj_type,
            obj_name,
            token,
        )

        if obj_id:
            self.output(
                "Script '{}' already exists: ID {}".format(self.script_name, obj_id)
            )
            if self.replace:
                self.output(
                    "Replacing existing script as 'replace_script' is set to {}".format(
                        self.replace
                    ),
                    verbose_level=1,
                )
            else:
                self.output(
                    "Not replacing existing script. Use replace_script='True' to enforce.",
                    verbose_level=1,
                )
                return

        # post the script
        self.upload_script(
            self.jamf_url,
            self.script_name,
            self.script_path,
            category_id,
            self.script_category,
            self.script_info,
            self.script_notes,
            self.script_priority,
            self.script_parameter4,
            self.script_parameter5,
            self.script_parameter6,
            self.script_parameter7,
            self.script_parameter8,
            self.script_parameter9,
            self.script_parameter10,
            self.script_parameter11,
            self.osrequirements,
            token,
            obj_id,
        )
        script_uploaded = True

        # output the summary
        self.env["script_name"] = self.script_name
        self.env["script_uploaded"] = script_uploaded
        if script_uploaded:
            self.env["jamfscriptuploader_summary_result"] = {
                "summary_text": "The following scripts were created or updated in Jamf Pro:",
                "report_fields": [
                    "script",
                    "path",
                    "category",
                    "priority",
                    "os_req",
                    "info",
                    "notes",
                    "P4",
                    "P5",
                    "P6",
                    "P7",
                    "P8",
                    "P9",
                    "P10",
                    "P11",
                ],
                "data": {
                    "script": self.script_name,
                    "path": self.script_path,
                    "category": self.script_category,
                    "priority": str(self.script_priority),
                    "info": self.script_info,
                    "os_req": self.osrequirements,
                    "notes": self.script_notes,
                    "P4": self.script_parameter4,
                    "P5": self.script_parameter5,
                    "P6": self.script_parameter6,
                    "P7": self.script_parameter7,
                    "P8": self.script_parameter8,
                    "P9": self.script_parameter9,
                    "P10": self.script_parameter10,
                    "P11": self.script_parameter11,
                },
            }


if __name__ == "__main__":
    PROCESSOR = JamfScriptUploader()
    PROCESSOR.execute_shell()
