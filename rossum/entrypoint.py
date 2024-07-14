"""Main application. Provides API with export endpoint, converting xml from one format to another."""

import base64
import logging
import os
import re
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ElementTree

import aiohttp
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger(__name__)

USERNAME = os.getenv("BASIC_AUTH_USERNAME")
PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")

BEARER_TOKEN = os.getenv("ROSSUM_BEARER_TOKEN")
ROSSUM_DOMAIN = os.getenv("ROSSUM_DOMAIN")
ROSSUM_USERNAME = os.getenv("ROSSUM_USERNAME")
ROSSUM_PASSWORD = os.getenv("ROSSUM_PASSWORD")

POSTBIN_URL = os.getenv("POSTBIN_URL")  # we could actually create new bin via the api...

app = FastAPI()
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify credentials using basic auth."""
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


async def get_new_bearer_token():
    """Get new bearer token from the login session."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://{ROSSUM_DOMAIN}.rossum.app/api/v1/auth/login",
            json={"username": ROSSUM_USERNAME, "password": ROSSUM_PASSWORD},
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("key")
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to obtain new bearer token",
                )


async def make_export_request(annotation_id: str, queue_id: str, token: str):
    """Make export request to the rossum API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://{ROSSUM_DOMAIN}.rossum.app/api/v1/queues/{queue_id}/export",
            params={"format": "xml", "id": annotation_id},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            return response.status, await response.text()


async def download_schema(xml_root: ElementTree.Element, token: str):
    """Extract the schema URL from the document, download the schema and return as json."""
    try:
        schema_url = xml_root.find(".//schema").attrib["url"]
    except AttributeError:
        raise HTTPException(
            status_code=500,
            detail="Schema URL not found in the document",
        )

    async with aiohttp.ClientSession() as session:
        async with session.get(schema_url, headers={"Authorization": f"Bearer {token}"}) as response:
            if response.status == 200:
                schema_json = await response.json()
                return schema_json
            else:
                detail = await response.text()
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to download schema: {detail}",
                )


async def transform_xml(root: ElementTree.Element, schema: str):
    """Transform the XML using provided schema file."""

    def clean_label(label):
        # Remove spaces from label and convert to camelCase
        cleaned_label = re.sub(r"\s+", "", label.title())
        # escape special chars
        cleaned_label = re.sub(r"[&]", "_", cleaned_label)
        return cleaned_label

    # prepare output XML root
    output_root = ElementTree.Element("Export")  # FIXME maybe this should be document_type ?

    # traverse schema and XML to dynamically create output XML
    for section in schema["content"]:
        section_label = clean_label(section["label"])
        section_element = ElementTree.SubElement(output_root, section_label)

        for child in section["children"]:
            if child["category"] == "datapoint":
                schema_id = child["id"]

                xpath = f".//datapoint[@schema_id='{schema_id}']"

                datapoint_element = root.find(xpath)

                if datapoint_element is not None and datapoint_element.text:
                    xml_tag = clean_label(child["label"])
                    xml_tag_element = ElementTree.SubElement(section_element, xml_tag)
                    xml_tag_element.text = datapoint_element.text

            elif child["category"] == "multivalue":
                schema_id = child["id"]
                xpath = f".//multivalue[@schema_id='{schema_id}']"
                multivalue_elements = root.findall(xpath)

                for multivalue_element in multivalue_elements:
                    multivalue_section_label = clean_label(child["label"])
                    multivalue_section_element = ElementTree.SubElement(section_element, multivalue_section_label)

                    for tuple_child in child["children"]["children"]:
                        tuple_schema_id = tuple_child["id"]
                        tuple_xpath = f".//tuple[@schema_id='{tuple_schema_id}']"
                        tuple_elements = multivalue_element.findall(tuple_xpath)

                        for tuple_element in tuple_elements:
                            tuple_label = clean_label(tuple_child["label"])
                            tuple_section_element = ElementTree.SubElement(multivalue_section_element, tuple_label)

                            for tuple_datapoint_child in tuple_child["children"]:
                                tuple_datapoint_schema_id = tuple_datapoint_child["id"]
                                tuple_datapoint_xpath = f".//datapoint[@schema_id='{tuple_datapoint_schema_id}']"
                                tuple_datapoint_element = tuple_element.find(tuple_datapoint_xpath)

                                if tuple_datapoint_element is not None and tuple_datapoint_element.text:
                                    tuple_datapoint_xml_tag = tuple_datapoint_child["label"]
                                    tuple_datapoint_xml_element = ElementTree.SubElement(
                                        tuple_section_element, tuple_datapoint_xml_tag
                                    )
                                    tuple_datapoint_xml_element.text = tuple_datapoint_element.text

    # Generate output XML string
    output_xml_str = ElementTree.tostring(output_root, encoding="utf-8", xml_declaration=True).decode("utf-8")
    # ... and prettify it
    dom = minidom.parseString(output_xml_str)
    pretty_output_xml = dom.toprettyxml(indent="    ")
    return pretty_output_xml


async def publish_converted(xml: str, annotation_id: str) -> bool:
    """Publish converted XML to the bin."""

    encoded_content = base64.b64encode(xml.encode()).decode()
    payload = {"annotationId": annotation_id, "content": encoded_content}

    async with aiohttp.ClientSession() as session:
        async with session.post(POSTBIN_URL, json=payload) as response:
            if response.status == 200:
                return
            else:
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to save to postbin: {response.reason}",
                )


async def handle_export_endpoint(annotation_id, queue_id):
    """Handle the whole logic for export action."""
    # Check the presence of query parameters
    if not annotation_id or not queue_id:
        raise HTTPException(
            status_code=400,
            detail="Missing annotation_id or queue_id in request",
        )

    bearer_token = BEARER_TOKEN
    # Make the request to Rossum API
    if bearer_token:
        status, text = await make_export_request(annotation_id, queue_id, bearer_token)

    if bearer_token is None or status == 401:
        bearer_token = await get_new_bearer_token()
        status, text = await make_export_request(annotation_id, queue_id, bearer_token)

    if status != 200:
        raise HTTPException(
            status_code=status,
        )

    try:
        xml_root = ElementTree.fromstring(text)
    except ElementTree.ParseError as e:
        raise HTTPException(status_code=500, details=f"Failed to parse XML: {e}")

    schema = await download_schema(xml_root, bearer_token)

    transformed_xml = await transform_xml(xml_root, schema)

    await publish_converted(transformed_xml, annotation_id)


@app.get("/export")
async def export(
    annotation_id: str = Header(..., description="The ID of the annotation"),
    queue_id: str = Header(..., description="The ID of the annotation queue"),
    credentials: HTTPBasicCredentials = Depends(security),
):
    """Endpoint for xml conversion.

    Requires basic authentication, annotation_id and queue_id for Rossum API.
    """
    try:
        # calling verify_credentials explicitly so we can transform exception into JSON response
        verify_credentials(credentials)
        await handle_export_endpoint(annotation_id, queue_id)
        return JSONResponse(content={"success": True})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"success": False, "detail": e.detail})


@app.on_event("startup")
async def start_api() -> None:
    """Initialize API.

    Check that necessary env variables are present.
    """
    if USERNAME is None or PASSWORD is None:
        raise OSError("BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD must be set as environment variables.")

    if ROSSUM_DOMAIN is None:
        raise OSError("ROSSUM_DOMAIN variable is not set.")

    if BEARER_TOKEN is None and (ROSSUM_USERNAME is None or ROSSUM_PASSWORD is None):
        raise OSError(
            "Cannot authenticate requests to Rossum API."
            + "Either ROSSUM_BEARER_TOKEN or ROSSUM_USERNAME and ROSSUM_PASSWORD must be defined."
        )

    if POSTBIN_URL is None:
        raise OSError("POSTBIN_URL variable is not set.")


def main() -> None:
    """Main entrypoint."""
    uvicorn.run("rossum.entrypoint:app", host="0.0.0.0", port=8080, loop="uvloop")  # noqa


if __name__ == "__main__":
    main()
