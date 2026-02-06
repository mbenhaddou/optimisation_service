# 📦 Database Schema – SolutionRouting

## Entity: `SolutionRouting`

This table stores each optimization request and its result, along with metadata about the execution status and parameters.

| Column                  | Type           | Description                                                                 |
|-------------------------|----------------|-----------------------------------------------------------------------------|
| `uuid`                  | UUID (BINARY)  | Primary key (indexed). Unique identifier for each routing solution.        |
| `creation_date`         | `DateTime`     | UTC timestamp when the request was created.                                |
| `update_date`           | `DateTime`     | UTC timestamp of the last update (auto-updated on modification).           |
| `optimization_request`  | `MEDIUMTEXT`   | JSON string of the original input request (orders, workers, constraints).  |
| `optimization_response` | `MEDIUMTEXT`   | JSON string of the computed solution or error.                             |
| `status`                | `Text`         | Status of the computation: `CREATED`, `RUNNING`, `FINISHED`, `FAILED`.     |
| `status_msg`            | `Text`         | Optional log message or user feedback related to status.                   |
| `parameters`            | `Text`         | Configuration and solver parameters used in the optimization run.          |

---

## ⚙️ Enum: `SolutionRoutingStatus`

Defined values for `status`:

- `CREATED`: The request was received but not yet processed.
- `RUNNING`: The optimization is currently being computed.
- `FINISHED`: A solution was found successfully.
- `FAILED`: The optimization failed due to an error.

---

## 🔄 JSON Deserialization

The fields `optimization_request`, `optimization_response`, and `parameters` are stored as strings in the database but automatically converted to Python `dict` objects when accessed via the API thanks to custom validators in the Pydantic schema:

```python
@validator("optimization_response", "optimization_request", "parameters", pre=True)
def str_to_dictionary(cls, v) -> Optional[dict]:
    if isinstance(v, str):
        if v.strip() == '':
            return None
        else:
            return json.loads(v)
```