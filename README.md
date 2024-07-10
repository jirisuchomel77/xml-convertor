## Python Web application for XML conversion


## Requirements

- docker
- docker-compose
- some reasonable Python setup, I tested with Python3.9
- poetry is used for package dependencies

Environment variables


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

- route definions (/export) should go to separate directory
- helper functions (whole XML conversion) should go to separare helper file

Test coverage: it is very simple, normally we should use some python test library in addition to end-to-end test. And of course there should be tests for various failure cases.

Environment variables: in actual production environment they would be stored in some kind of secret/vault
