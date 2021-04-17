# PID database archive
Downloading and storing transportation data from [golemio](https://golemioapi.docs.apiary.io/#reference/public-transport/gtfs-shapes) into the postgresql database.

* After startup loading static tables:
  * Routes
  * Services
  * Stops
  * Trips
  * Vehicle Positions

* Realtime tracking of: 
  * Vehicle Positions
  

## Launching
1. [Install Docker](https://docs.docker.com/desktop/)
2. Create .env file with secrets and basic config. API token is connected to your [golemio account](https://api.golemio.cz/api-keys).
```dotenv
# 
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
DB_PREFIX=postgresql://
CELERY_REDIS=redis://localhost:6379
# Golemio API 
GOLEMIO_ACCESS_TOKEN={FILL_YOUR_TOKEN}
```
3. Run
```bash
docker-compose up
```
4. Be patient, it takes about 10-20 minutes since the initial structure is download from API.
5. The Database is connected at localhost:5432 (For example: Use [dbeaver](https://dbeaver.io/) for viewing.)

### Structure
* [Source codes for DB init](./srv/init_db.py)
* [Celery task for regular DB updates](./srv/pid-tasks.py)
* [Database structure in SQLAlchemy](./srv/golemio/sql_declaration.py)
* [Parser of Golemio Transport API](./srv/golemio/parser.py)

### Troubleshooting
* Check if your API key works at [apiary](https://golemioapi.docs.apiary.io/#reference/public-transport/realtime-vehicle-positions/get-all-vehicle-positions)
* Clear volume if initialization failed, for example like this:
  * Be aware that following commands removes all stopped containers and volumes
  ``` bask
  docker container prune
  docker volume prune
    ```
