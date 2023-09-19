from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()

MONGO_DB_URL = 'mongodb+srv://mithravindanambiar2021:mithramithra@cluster0.gww9o7a.mongodb.net/'
MONGO_DB_NAME = "UnivDatabase"
department_collection_name = "Departments"


class MongoDB:
    client: AsyncIOMotorClient = None


db = MongoDB()


async def get_database() -> AsyncIOMotorClient:
    return db.client[MONGO_DB_NAME]


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGO_DB_URL)


async def close_mongo_connection():
    db.client.close()


app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


class Department(BaseModel):
    departmentName: str


class DepartmentInDB(Department):
    id: str


@app.get("/dep", response_model=List[DepartmentInDB])
async def get_departments():
    db = await get_database()
    deps = await db[department_collection_name].find({}).to_list(None)
    return [DepartmentInDB(**dep, id=str(dep["_id"])) for dep in deps]


@app.get("/deps", response_model=List[DepartmentInDB])
async def get_departments(depName: str):
    db = await get_database()
    deps = await db[department_collection_name].find({'departmentName': depName}).to_list(None)

    if deps:
        return [DepartmentInDB(**dep, id=str(dep["_id"])) for dep in deps]
    else:
        raise HTTPException(status_code=404, detail="Department not found")


@app.post("/dep", response_model=DepartmentInDB)
async def create_department(department: Department):
    db = await get_database()
    department_dict = department.dict()
    result = await db[department_collection_name].insert_one(department_dict)
    created_department = await db[department_collection_name].find_one({"_id": result.inserted_id})

    if created_department:
        return DepartmentInDB(**created_department, id=str(created_department["_id"]))
    else:
        raise HTTPException(status_code=500, detail="Failed to create department")


@app.put("/deps/{department_id}", response_model=DepartmentInDB)
async def update_department(department_id: str, department: Department):
    db = await get_database()
    department_dict = department.dict()
    result = await db[department_collection_name].update_one(
        {"_id": ObjectId(department_id)},
        {"$set": department_dict}
    )

    if result.modified_count == 1:
        updated_department = await db[department_collection_name].find_one({"_id": ObjectId(department_id)})
        return DepartmentInDB(**updated_department, id=str(updated_department["_id"]))
    else:
        raise HTTPException(status_code=404, detail="Department not found")

    updated_department = await db[department_collection_name].find_one({"departmentName": department_name})

    return DepartmentInDB(**updated_department, id=str(updated_department["_id"]))


@app.delete("/depswithname/{department_name}", response_model=dict)
async def delete_department(department_name: str):
    db = await get_database()

    # Check if the department exists
    existing_department = await db[department_collection_name].find_one({"departmentName": department_name})
    if existing_department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    # Delete the department
    result = await db[department_collection_name].delete_one({"departmentName": department_name})

    if result.deleted_count == 1:
        return {"message": f"Department '{department_name}' deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="An error occurred while deleting the department")


@app.delete("/depswithId/{department_id}", response_model=dict)
async def delete_department_by_id(department_id: str):
    db = await get_database()

    # Check if the department exists
    existing_department = await db[department_collection_name].find_one({"_id": ObjectId(department_id)})
    if existing_department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    # Delete the department
    result = await db[department_collection_name].delete_one({"_id": ObjectId(department_id)})

    if result.deleted_count == 1:
        return {"message": f"Department with ID '{department_id}' deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="An error occurred while deleting the department")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)