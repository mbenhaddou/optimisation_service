import uvicorn
from multiprocessing import cpu_count

if __name__ == "__main__":
    number_of_workers = cpu_count()
    uvicorn.run("application:app", host="0.0.0.0", port=5051, workers=number_of_workers)