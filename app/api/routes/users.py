from fastapi import APIRouter

router = APIRouter()


@router.get("/users")
def test_route():
    return {"Are users working?": "Yes"}
