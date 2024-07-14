## Python Web application for XML conversion

The goal of the application is to provide one endpoint /export that will convert data from the XML downloaded from Rossum to a XML in another format.

The original problem assignment:

*Validate that the request came from an authorized source, using Basic Authentication. The right credentials should be stored as environment variables in the environment that your application can access. The username shall be myUser123, password secretSecret.

Accept the user request where the user passes the ID of the annotation they want to get the data for and the queue ID of the annotation where the annotation is located in Rossum. The way how the users shall pass this information is up to you. Validate that the request format is correct and it contains everything necessary.

Within the endpoint, use the passed values to download data for a sample annotation in your Rossum account, using a call on /export endpoint of Rossum API. (Create a new Rossum account here. To create the Rossum account, you can use some temporary email, for example from this website.) The content of the response will be similar to this.

Convert the data that you have received, so that the output data has the following format.

Send the converted content as a REST API POST request to dummy post bin endpoint (you can create one here https://www.toptal.com/developers/postbin/ ), with no authentication details and data as JSON with the keys annotationId and the value of the original annotation ID and the key content with the data in XML as a base64 string.

Return a JSON with a key success, filled by true or false, depending on whether the request could be posted successfully or not.*

## Requirements

- docker
- docker-compose
- some reasonable Python setup, I tested with Python3.9
- poetry is used for package dependencies
- ruff and black are used for linting and code formatting

Several environment variables are needed for the app to run. First the credentials for accessing the endpoint:

```bash
export BASIC_AUTH_USERNAME=myUser123
export BASIC_AUTH_PASSWORD=secretSecret
```

Now the variables necessary for accessing Rossum API:

```bash
# bearer token: if it is valid, username and password for Rossum API are not needed
ROSSUM_BEARER_TOKEN=<valid token>

# actual credentials for Rossum API if the bearer token is invalid or not known
ROSSUM_USERNAME=<your rossum username>
ROSSUM_PASSWORD=<your rossum password>

# rossum domain
ROSSUM_DOMAIN=<your rossum domain>
```

And finally the URL for the postbin where the converted data should be saved.
```
export POSTBIN_URL=https://www.postb.in/1720972373333-3732320638373
```


## Running

Just run the docker image using existing make targets:

```bash
make api
```

Now the server is running on port 8080.
Do not forget to export env variables, or the app will fail on start.


... or prepare virtual environment and start the application directly:

```bash
poetry run rossum
```

Now you can execute API call e.g. using curl:

```bash
curl -u myUser123:secretSecret -H "annotation-id: 3227735" -H "queue-id: 1161196" http://localhost:8080/export
```

## Testing

```bash
make build
make test
```

This will execute simple curl query against running docker image.


## Discussing the solution

For simplicity, everything is in one script. This could be further modified

- route definions (here just `/export`) should go to separate directory
- helper functions (e.g. whole XML conversion) should go to separare helper file

Test coverage: it is very simple, normally we should use some python test library in addition to end-to-end test. And of course there should be tests for various failure cases.

Environment variables: in actual production environment they would be stored in some kind of secret/vault.

## Notes

- Return value is JSON, but it also contains various possible error information
- Sometimes postbin seems to be gone too early thus failing the whole workflow without apparent reason
