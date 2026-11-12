# Trip Planner API — resource map

Rules: plural nouns, no verbs in paths, lowercase, IDs in the path, filters in the query,
nest only one level (to show who owns what).

| Method | Path | Meaning | Success | Status |
|---|---|---|---|---|
| GET | /health | is the app alive? | 200 | built |
| GET | /destinations | list destinations (filters in query) | 200 | built |
| GET | /destinations/{destination_id} | one destination | 200 | built |
| GET | /trips | list my trips | 200 | planned |
| POST | /trips | create a trip | 201 | planned |
| GET | /trips/{trip_id} | one trip | 200 | planned |
| PATCH | /trips/{trip_id} | change some fields | 200 | planned |
| DELETE | /trips/{trip_id} | delete a trip | 204 | planned |
| GET | /trips/{trip_id}/days | days of a trip | 200 | planned |
| POST | /trips/{trip_id}/days | add a day | 201 | planned |
| GET | /days/{day_id}/activities | activities of a day | 200 | planned |
| POST | /days/{day_id}/activities | add an activity | 201 | planned |
| PATCH | /activities/{activity_id} | change an activity | 200 | planned |
| DELETE | /activities/{activity_id} | delete an activity | 204 | planned |
| POST | /users | sign up | 201 | planned |
| GET | /users/me | the logged-in user | 200 | planned |
| POST | /auth/token | log in, get a token | 200 | planned |

Errors: 400 bad request, 401 not logged in, 403 not allowed, 404 not found,
405 wrong method, 409 conflict, 422 invalid data. Body: {"detail": ...}.
