![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Me-Phew/timetable-api?style=for-the-badge)
![GitHub repo size](https://img.shields.io/github/repo-size/Me-Phew/timetable-api?style=for-the-badge)

![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMe-Phew%2Ftimetable-uptime%2Fmaster%2Fapi%2Fapi%2Fuptime.json&style=for-the-badge)
![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FMe-Phew%2Ftimetable-uptime%2Fmaster%2Fapi%2Fapi%2Fresponse-time.json&style=for-the-badge)

## Improved unofficial version of the [Timetable MPK Nowy Sącz](https://www.mpk.nowysacz.pl/timetable/)

### Features:
- [x] Fast and easy to maintain thanks to [FastAPI](https://fastapi.tiangolo.com/) and [Redis](https://redis.io/)
- [x] Proxy of the official [Timetable MPK Nowy Sącz](https://www.mpk.nowysacz.pl/timetable/) stops endpoint that provides bus ETAs made in order to avoid CORS errors
- [x] Tracking buses ETA with notifications implemented using [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
