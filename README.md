## Python Web application for XML conversion


## Requirements

- docker
- docker-compose
- some reasonable Python setup, I tested with Python3.9

Environment variables

## Running

Just run the docker image using existing make targets or prepare virtual environment and start the application directly:

```bash
poetry run rossum
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
- actual test coverage

