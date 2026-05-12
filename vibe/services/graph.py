import re


def normalize_route(route: str):
    if not route:
        return ""

    route = str(route).strip()

    route = route.split("?")[0]
    route = re.sub(r"^https?://[^/]+", "", route)
    route = re.sub(r"\$\{[^}]+\}", "{param}", route)
    route = re.sub(r"\{[^}]+\}", "{param}", route)
    route = re.sub(r":[a-zA-Z_][\w]*", "{param}", route)
    route = re.sub(r"/+", "/", route)

    if route != "/" and route.endswith("/"):
        route = route[:-1]

    if not route.startswith("/"):
        route = "/" + route

    return route.lower()


def route_parts(route: str):
    return [
        part
        for part in normalize_route(route).split("/")
        if part and part != "{param}"
    ]


def routes_match(fetch_route: str, backend_route: str):
    fetch = normalize_route(fetch_route)
    backend = normalize_route(backend_route)

    if fetch == backend:
        return True

    fetch_parts = route_parts(fetch)
    backend_parts = route_parts(backend)

    if not fetch_parts or not backend_parts:
        return False

    # suffix match handles:
    # /chat/message/{param} ↔ /message/{param}
    if len(fetch_parts) >= len(backend_parts):
        if fetch_parts[-len(backend_parts):] == backend_parts:
            return True

    if len(backend_parts) >= len(fetch_parts):
        if backend_parts[-len(fetch_parts):] == fetch_parts:
            return True

    shared = set(fetch_parts) & set(backend_parts)

    return len(shared) >= 1 and (
        fetch_parts[-1] == backend_parts[-1]
        or backend_parts[-1] in fetch_parts
    )


def build_relationship_graph(symbols):
    graph = {
        "fetch_to_route": [],
    }

    routes = []
    fetches = []

    for symbol in symbols:
        symbol_type = symbol.get("type")
        symbol_name = symbol.get("symbol", "")

        if symbol_type == "route":
            routes.append({
                "route": normalize_route(symbol_name),
                "raw_route": symbol_name,
                "file_path": symbol["file_path"],
                "meta": symbol.get("meta", ""),
                "start_line": symbol.get("start_line"),
                "end_line": symbol.get("end_line"),
            })

        elif symbol_type in {"fetch", "network"}:
            fetches.append({
                "route": normalize_route(symbol_name),
                "raw_route": symbol_name,
                "file_path": symbol["file_path"],
                "start_line": symbol.get("start_line"),
                "end_line": symbol.get("end_line"),
            })

    for fetch in fetches:
        for route in routes:
            if routes_match(fetch["route"], route["route"]):
                graph["fetch_to_route"].append({
                    "frontend_file": fetch["file_path"],
                    "frontend_range": [
                        fetch["start_line"],
                        fetch["end_line"],
                    ],
                    "frontend_route": fetch["raw_route"],
                    "route": route["raw_route"],
                    "backend_file": route["file_path"],
                    "backend_range": [
                        route["start_line"],
                        route["end_line"],
                    ],
                    "method": route["meta"],
                })

    return graph