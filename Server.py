import json
from wsgiref.simple_server import make_server


# Base de datos en memoria
tasks = {}

# ID para la próxima tarea
next_id = 1


def json_response(start_response, status, data=None):
    """Envía una respuesta JSON con el código de estado indicado."""
    if data is None:
        data = {}

    body = json.dumps(data).encode("utf-8")

    start_response(
        status,
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )

    return [body]


def read_json(environ):
    """Lee y convierte el cuerpo de la petición desde JSON."""
    try:
        content_length = int(environ.get("CONTENT_LENGTH", 0))
    except ValueError:
        content_length = 0

    body = environ["wsgi.input"].read(content_length)

    if not body:
        return {}

    return json.loads(body.decode("utf-8"))


def application(environ, start_response):
    global next_id

    method = environ["REQUEST_METHOD"]
    path = environ["PATH_INFO"]

    # GET /tasks
    if path == "/tasks":
        if method == "GET":
            return json_response(
                start_response,
                "200 OK",
                list(tasks.values()),
            )

        elif method == "POST":
            try:
                data = read_json(environ)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": "El cuerpo debe ser JSON válido"},
                )

            task = data.copy()
            task["id"] = next_id

            tasks[next_id] = task
            next_id += 1

            return json_response(
                start_response,
                "201 Created",
                task,
            )

        # La ruta existe, pero el verbo no está permitido
        return json_response(
            start_response,
            "405 Method Not Allowed",
            {"error": "Método no permitido"},
        )

    # Rutas /tasks/{id}
    if path.startswith("/tasks/"):
        id_text = path[len("/tasks/"):]

        # Verificamos que el ID sea un número
        try:
            task_id = int(id_text)
        except ValueError:
            return json_response(
                start_response,
                "404 Not Found",
                {"error": "Tarea no encontrada"},
            )

        # GET /tasks/{id}
        if method == "GET":
            if task_id not in tasks:
                return json_response(
                    start_response,
                    "404 Not Found",
                    {"error": "Tarea no encontrada"},
                )

            return json_response(
                start_response,
                "200 OK",
                tasks[task_id],
            )

        # PATCH /tasks/{id}
        elif method == "PATCH":
            if task_id not in tasks:
                return json_response(
                    start_response,
                    "404 Not Found",
                    {"error": "Tarea no encontrada"},
                )

            try:
                data = read_json(environ)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return json_response(
                    start_response,
                    "400 Bad Request",
                    {"error": "El cuerpo debe ser JSON válido"},
                )

            # Modificamos únicamente los campos recibidos
            tasks[task_id].update(data)

            return json_response(
                start_response,
                "200 OK",
                tasks[task_id],
            )

        # DELETE /tasks/{id}
        elif method == "DELETE":
            if task_id not in tasks:
                return json_response(
                    start_response,
                    "404 Not Found",
                    {"error": "Tarea no encontrada"},
                )

            deleted_task = tasks.pop(task_id)

            return json_response(
                start_response,
                "200 OK",
                deleted_task,
            )

        # La ruta existe, pero el verbo no
        return json_response(
            start_response,
            "405 Method Not Allowed",
            {"error": "Método no permitido"},
        )

    # Cualquier otra ruta
    return json_response(
        start_response,
        "404 Not Found",
        {"error": "Ruta no encontrada"},
    )


if __name__ == "__main__":
    HOST = "localhost"
    PORT = 8000

    print(f"Servidor iniciado en http://{HOST}:{PORT}")

    with make_server(HOST, PORT, application) as server:
        server.serve_forever()